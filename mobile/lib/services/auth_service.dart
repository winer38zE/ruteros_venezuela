import 'dart:convert';
import '../services/api_service.dart';
import 'biometric_service.dart';

class Usuario {
  final String id;
  final String nombre;
  final String username;
  final String rol;
  final String empresaId;

  Usuario({
    required this.id,
    required this.nombre,
    required this.username,
    required this.rol,
    required this.empresaId,
  });

  factory Usuario.fromJson(Map<String, dynamic> j) => Usuario(
        id: j['id'],
        nombre: j['nombre'],
        username: j['username'],
        rol: j['rol'],
        empresaId: j['empresa_id'],
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'username': username,
        'rol': rol,
        'empresa_id': empresaId,
      };

  bool get esDueno => rol == 'DUEÑO' || rol.toLowerCase() == 'owner';
  bool get esAdministrador => rol == 'ADMINISTRADOR';
  bool get puedeOperaciones => esDueno || esAdministrador;

  /// RBAC de la app: dueño con acceso total, el resto es panel de empleado.
  String get rolAcceso => esDueno ? 'owner' : 'employee';
  bool get esOwner => rolAcceso == 'owner';
}

class AuthService {
  AuthService(this._api, {BiometricService? biometric})
      : _biometric = biometric ?? BiometricService();

  final ApiService _api;
  final BiometricService _biometric;

  BiometricService get biometric => _biometric;

  Future<Usuario> login(
    String correo,
    String password, {
    bool guardarBiometria = false,
  }) async {
    final usuarioNorm = correo.trim();
    final data = await _api.post('/auth/login', {
      'username': usuarioNorm,
      'password': password,
    });
    final user = Usuario.fromJson(data);
    await _api.saveSession(
      token: user.id,
      usuarioId: user.id,
      usuarioJson: jsonEncode(user.toJson()),
    );

    if (guardarBiometria) {
      try {
        await _biometric.guardarCredenciales(
          correo: usuarioNorm,
          password: password,
        );
      } catch (_) {}
    }
    return user;
  }

  /// Huella válida → login con credenciales guardadas.
  Future<Usuario?> loginConBiometria() async {
    final ok = await _biometric.autenticar();
    if (!ok) return null;
    final credenciales = await _biometric.leerCredenciales();
    if (credenciales == null) return null;
    try {
      return await login(
        credenciales.correo,
        credenciales.password,
        guardarBiometria: true,
      );
    } on ApiException catch (e) {
      if (e.statusCode == 401 || e.statusCode == 403 || e.statusCode == 429) {
        await _invalidarSesionLocal();
      }
      rethrow;
    }
  }

  Future<void> _invalidarSesionLocal() async {
    await _biometric.borrarCredenciales();
    await _api.clearSession();
  }

  Future<Usuario?> restoreSession() async {
    await _api.loadSession();
    if (!_api.hasSession || _api.usuarioJson == null) return null;
    try {
      final user = Usuario.fromJson(jsonDecode(_api.usuarioJson!));
      _api.setUsuarioId(user.id);
      return user;
    } catch (_) {
      await _api.clearSession();
      return null;
    }
  }

  Future<void> logout() async {
    await _biometric.borrarCredenciales();
    await _api.clearSession();
  }
}
