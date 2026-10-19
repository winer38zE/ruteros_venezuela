import 'package:flutter/services.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

/// Resultado detallado del prompt biométrico (huella / rostro).
enum BiometricAuthResult {
  success,
  canceled,
  notAvailable,
  notEnrolled,
  lockedOut,
  permanentlyLockedOut,
  failed,
}

/// Huella o rostro; credenciales cifradas por país + usuario.
class BiometricService {
  BiometricService({
    LocalAuthentication? localAuth,
    FlutterSecureStorage? storage,
  })  : _localAuth = localAuth ?? LocalAuthentication(),
        _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  /// Claves legadas (una sola sesión global — migrar a [scopeKey]).
  static const _kLegacyCorreo = 'session_correo';
  static const _kLegacyPassword = 'session_password';
  static const _kLegacyToken = 'session_token';
  static const _kLegacyUsuarioId = 'session_usuario_id';
  static const _kLegacyUsuarioJson = 'session_usuario_json';
  static const _kLegacyPaisLoginId = 'session_pais_login_id';
  static const _kLegacyPaisSimbolo = 'session_pais_simbolo_moneda';

  final LocalAuthentication _localAuth;
  final FlutterSecureStorage _storage;

  /// Prefijo estable: `biometric:{paisId}:{usuarioNormalizado}`.
  static String scopeKey(String paisId, String usuario) {
    final p = paisId.trim();
    final u = usuario.trim().toLowerCase();
    return 'biometric:$p:$u';
  }

  String _kCorreo(String scope) => '$scope:correo';
  String _kPassword(String scope) => '$scope:password';
  String _kToken(String scope) => '$scope:token';
  String _kUsuarioId(String scope) => '$scope:usuario_id';
  String _kUsuarioJson(String scope) => '$scope:usuario_json';
  String _kPaisSimbolo(String scope) => '$scope:pais_simbolo';

  /// True si el dispositivo puede mostrar el prompt de huella/rostro.
  Future<bool> soportaBiometria() async {
    try {
      if (await _localAuth.isDeviceSupported()) return true;
      if (await _localAuth.canCheckBiometrics) return true;
      final disponibles = await _localAuth.getAvailableBiometrics();
      return disponibles.isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  Future<BiometricAuthResult> autenticarDetallado() async {
    const razon = 'Confirma tu huella para entrar a ED NET PRO';
    try {
      final ok = await _localAuth.authenticate(
        localizedReason: razon,
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
          useErrorDialogs: true,
        ),
      );
      if (ok) return BiometricAuthResult.success;
      return BiometricAuthResult.canceled;
    } on PlatformException catch (e) {
      return _mapearErrorPlataforma(e);
    } catch (_) {
      return BiometricAuthResult.failed;
    }
  }

  BiometricAuthResult _mapearErrorPlataforma(PlatformException e) {
    final code = e.code.toLowerCase();
    if (code.contains('notenrolled') || code.contains('not_enrolled')) {
      return BiometricAuthResult.notEnrolled;
    }
    if (code.contains('permantlylockedout') ||
        code.contains('permanentlylockedout')) {
      return BiometricAuthResult.permanentlyLockedOut;
    }
    if (code.contains('lockedout') || code.contains('locked_out')) {
      return BiometricAuthResult.lockedOut;
    }
    if (code.contains('notavailable') ||
        code.contains('not_available') ||
        code.contains('passcodenotset')) {
      return BiometricAuthResult.notAvailable;
    }
    if (code.contains('usercancel') ||
        code.contains('cancel') ||
        code.contains('auth_in_progress')) {
      return BiometricAuthResult.canceled;
    }
    return BiometricAuthResult.failed;
  }

  Future<bool> autenticar() async {
    final r = await autenticarDetallado();
    return r == BiometricAuthResult.success;
  }

  Future<bool> tieneCredenciales({
    required String paisId,
    String? correo,
  }) async {
    final cred = await leerCredenciales(paisId: paisId, correo: correo);
    return cred != null;
  }

  Future<bool> tieneSesionSegura({
    required String paisId,
    required String correo,
  }) async {
    final sesion = await leerSesion(paisId: paisId, correo: correo);
    return sesion != null;
  }

  Future<bool> puedeIngresarConBiometria({
    required String paisId,
    String? correo,
  }) async {
    if (!await soportaBiometria()) return false;
    if (correo != null && correo.trim().isNotEmpty) {
      return tieneCredenciales(paisId: paisId, correo: correo);
    }
    final encontrado = await _buscarCredencialesEnPais(paisId);
    return encontrado != null;
  }

  Future<({String correo, String password})?> leerCredenciales({
    required String paisId,
    String? correo,
  }) async {
    await _migrarLegadoSiAplica(paisId: paisId, correo: correo);
    final usuario = correo?.trim();
    if (usuario != null && usuario.isNotEmpty) {
      return _leerScope(scopeKey(paisId, usuario));
    }
    return _buscarCredencialesEnPais(paisId);
  }

  Future<({String correo, String password})?> _buscarCredencialesEnPais(
    String paisId,
  ) async {
    try {
      final all = await _storage.readAll();
      final prefijo = 'biometric:${paisId.trim()}:';
      for (final entry in all.entries) {
        if (!entry.key.startsWith(prefijo) || !entry.key.endsWith(':correo')) {
          continue;
        }
        final scope = entry.key.substring(0, entry.key.length - ':correo'.length);
        final cred = await _leerScope(scope);
        if (cred != null) return cred;
      }
    } catch (_) {}
    return null;
  }

  Future<({String correo, String password})?> _leerScope(String scope) async {
    try {
      final correo = await _storage.read(key: _kCorreo(scope));
      final password = await _storage.read(key: _kPassword(scope));
      if (correo == null ||
          correo.isEmpty ||
          password == null ||
          password.isEmpty) {
        return null;
      }
      return (correo: correo, password: password);
    } catch (_) {
      return null;
    }
  }

  Future<void> guardarCredenciales({
    required String paisId,
    required String correo,
    required String password,
    String? paisSimboloMoneda,
  }) async {
    final scope = scopeKey(paisId, correo);
    await _storage.write(key: _kCorreo(scope), value: correo.trim());
    await _storage.write(key: _kPassword(scope), value: password);
    if (paisSimboloMoneda != null && paisSimboloMoneda.isNotEmpty) {
      await _storage.write(
        key: _kPaisSimbolo(scope),
        value: paisSimboloMoneda,
      );
    }
    await _limpiarLegado();
  }

  Future<String?> leerPaisSimboloMoneda({
    required String paisId,
    String? correo,
  }) async {
    final cred = await leerCredenciales(paisId: paisId, correo: correo);
    if (cred == null) return null;
    final scope = scopeKey(paisId, cred.correo);
    try {
      return await _storage.read(key: _kPaisSimbolo(scope));
    } catch (_) {
      return null;
    }
  }

  /// Compat: último país con huella (solo UI); preferir selector explícito.
  Future<String?> leerPaisLoginId() async {
    try {
      return await _storage.read(key: _kLegacyPaisLoginId);
    } catch (_) {
      return null;
    }
  }

  Future<void> guardarSesion({
    required String paisId,
    required String correo,
    required String token,
    required String usuarioId,
    required String usuarioJson,
  }) async {
    final scope = scopeKey(paisId, correo);
    await _storage.write(key: _kToken(scope), value: token);
    await _storage.write(key: _kUsuarioId(scope), value: usuarioId);
    await _storage.write(key: _kUsuarioJson(scope), value: usuarioJson);
  }

  Future<({String token, String usuarioId, String usuarioJson})?> leerSesion({
    required String paisId,
    required String correo,
  }) async {
    final scope = scopeKey(paisId, correo);
    try {
      final token = await _storage.read(key: _kToken(scope));
      final usuarioId = await _storage.read(key: _kUsuarioId(scope));
      final usuarioJson = await _storage.read(key: _kUsuarioJson(scope));
      if (token == null ||
          token.isEmpty ||
          usuarioId == null ||
          usuarioId.isEmpty ||
          usuarioJson == null ||
          usuarioJson.isEmpty) {
        return null;
      }
      return (token: token, usuarioId: usuarioId, usuarioJson: usuarioJson);
    } catch (_) {
      return null;
    }
  }

  Future<void> desactivarAccesoBiometrico({
    required String paisId,
    required String correo,
  }) async {
    final scope = scopeKey(paisId, correo);
    await _storage.delete(key: _kCorreo(scope));
    await _storage.delete(key: _kPassword(scope));
    await _storage.delete(key: _kToken(scope));
    await _storage.delete(key: _kUsuarioId(scope));
    await _storage.delete(key: _kUsuarioJson(scope));
    await _storage.delete(key: _kPaisSimbolo(scope));
  }

  Future<void> borrarTodoAccesoBiometrico() async {
    try {
      final all = await _storage.readAll();
      for (final key in all.keys) {
        if (key.startsWith('biometric:') || _esClaveLegado(key)) {
          await _storage.delete(key: key);
        }
      }
    } catch (_) {
      await _limpiarLegado();
    }
  }

  bool _esClaveLegado(String key) {
    return key == _kLegacyCorreo ||
        key == _kLegacyPassword ||
        key == _kLegacyToken ||
        key == _kLegacyUsuarioId ||
        key == _kLegacyUsuarioJson ||
        key == _kLegacyPaisLoginId ||
        key == _kLegacyPaisSimbolo;
  }

  Future<void> _limpiarLegado() async {
    for (final k in [
      _kLegacyCorreo,
      _kLegacyPassword,
      _kLegacyToken,
      _kLegacyUsuarioId,
      _kLegacyUsuarioJson,
      _kLegacyPaisSimbolo,
    ]) {
      await _storage.delete(key: k);
    }
  }

  Future<void> _migrarLegadoSiAplica({
    required String paisId,
    String? correo,
  }) async {
    try {
      final legacyCorreo = await _storage.read(key: _kLegacyCorreo);
      final legacyPass = await _storage.read(key: _kLegacyPassword);
      if (legacyCorreo == null ||
          legacyCorreo.isEmpty ||
          legacyPass == null ||
          legacyPass.isEmpty) {
        return;
      }
      final paisMigracion =
          (await _storage.read(key: _kLegacyPaisLoginId))?.trim() ?? paisId;
      final usuario = (correo?.trim().isNotEmpty == true)
          ? correo!.trim()
          : legacyCorreo.trim();
      await guardarCredenciales(
        paisId: paisMigracion,
        correo: usuario,
        password: legacyPass,
      );
      final legacyToken = await _storage.read(key: _kLegacyToken);
      final legacyUid = await _storage.read(key: _kLegacyUsuarioId);
      final legacyJson = await _storage.read(key: _kLegacyUsuarioJson);
      if (legacyToken != null &&
          legacyUid != null &&
          legacyJson != null &&
          legacyToken.isNotEmpty) {
        await guardarSesion(
          paisId: paisMigracion,
          correo: usuario,
          token: legacyToken,
          usuarioId: legacyUid,
          usuarioJson: legacyJson,
        );
      }
      await _limpiarLegado();
    } catch (_) {}
  }
}
