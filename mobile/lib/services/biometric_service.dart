import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

/// Huella o rostro, y credenciales cifradas para "Recordar sesión".
class BiometricService {
  BiometricService({
    LocalAuthentication? localAuth,
    FlutterSecureStorage? storage,
  })  : _localAuth = localAuth ?? LocalAuthentication(),
        _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  static const _kCorreo = 'session_correo';
  static const _kPassword = 'session_password';
  static const _kToken = 'session_token';
  static const _kUsuarioId = 'session_usuario_id';
  static const _kUsuarioJson = 'session_usuario_json';
  static const _kPaisLoginId = 'session_pais_login_id';

  final LocalAuthentication _localAuth;
  final FlutterSecureStorage _storage;

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

  Future<bool> autenticar() async {
    const razon = 'Confirma tu huella para entrar a ED NET PRO';
    const optsHuella = AuthenticationOptions(
      biometricOnly: true,
      stickyAuth: true,
      useErrorDialogs: true,
    );
    try {
      final ok = await _localAuth.authenticate(
        localizedReason: razon,
        options: optsHuella,
      );
      if (ok) return true;
    } catch (_) {}
    try {
      return await _localAuth.authenticate(
        localizedReason: razon,
        options: const AuthenticationOptions(
          biometricOnly: false,
          stickyAuth: true,
          useErrorDialogs: true,
        ),
      );
    } catch (_) {
      return false;
    }
  }

  Future<bool> tieneCredenciales() async {
    final credenciales = await leerCredenciales();
    return credenciales != null;
  }

  Future<bool> tieneSesionSegura() async {
    final sesion = await leerSesion();
    return sesion != null;
  }

  /// Huella disponible si hay sesión cifrada y/o credenciales para re-login.
  Future<bool> puedeIngresarConBiometria() async {
    if (!await soportaBiometria()) return false;
    return (await tieneSesionSegura()) || (await tieneCredenciales());
  }

  Future<({String correo, String password})?> leerCredenciales() async {
    String? correo;
    String? password;
    try {
      correo = await _storage.read(key: _kCorreo);
      password = await _storage.read(key: _kPassword);
    } catch (_) {
      return null;
    }
    if (correo == null || correo.isEmpty || password == null || password.isEmpty) {
      return null;
    }
    return (correo: correo, password: password);
  }

  Future<void> guardarCredenciales({
    required String correo,
    required String password,
    String? paisId,
  }) async {
    await _storage.write(key: _kCorreo, value: correo.trim());
    await _storage.write(key: _kPassword, value: password);
    if (paisId != null && paisId.isNotEmpty) {
      await _storage.write(key: _kPaisLoginId, value: paisId);
    }
  }

  Future<String?> leerPaisLoginId() async {
    try {
      return await _storage.read(key: _kPaisLoginId);
    } catch (_) {
      return null;
    }
  }

  Future<void> guardarSesion({
    required String token,
    required String usuarioId,
    required String usuarioJson,
  }) async {
    await _storage.write(key: _kToken, value: token);
    await _storage.write(key: _kUsuarioId, value: usuarioId);
    await _storage.write(key: _kUsuarioJson, value: usuarioJson);
  }

  Future<({String token, String usuarioId, String usuarioJson})?> leerSesion() async {
    try {
      final token = await _storage.read(key: _kToken);
      final usuarioId = await _storage.read(key: _kUsuarioId);
      final usuarioJson = await _storage.read(key: _kUsuarioJson);
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

  Future<void> borrarCredenciales() async {
    await _storage.delete(key: _kCorreo);
    await _storage.delete(key: _kPassword);
    await _storage.delete(key: _kPaisLoginId);
  }

  Future<void> borrarSesionSegura() async {
    await _storage.delete(key: _kToken);
    await _storage.delete(key: _kUsuarioId);
    await _storage.delete(key: _kUsuarioJson);
  }

  Future<void> borrarTodoAccesoBiometrico() async {
    await borrarCredenciales();
    await borrarSesionSegura();
  }
}
