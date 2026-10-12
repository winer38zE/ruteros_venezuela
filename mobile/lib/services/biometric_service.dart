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

  final LocalAuthentication _localAuth;
  final FlutterSecureStorage _storage;

  Future<bool> soportaBiometria() async {
    try {
      final soportado = await _localAuth.isDeviceSupported();
      if (!soportado) return false;
      final puede = await _localAuth.canCheckBiometrics;
      final disponibles = await _localAuth.getAvailableBiometrics();
      return puede || disponibles.isNotEmpty;
    } catch (_) {
      return false;
    }
  }

  Future<bool> autenticar() async {
    try {
      return await _localAuth.authenticate(
        localizedReason: 'Ingresar con huella dactilar o rostro',
        options: const AuthenticationOptions(
          biometricOnly: true,
          stickyAuth: true,
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
  }) async {
    await _storage.write(key: _kCorreo, value: correo.trim());
    await _storage.write(key: _kPassword, value: password);
  }

  Future<void> borrarCredenciales() async {
    await _storage.delete(key: _kCorreo);
    await _storage.delete(key: _kPassword);
  }
}
