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
    bool recordar = true,
  }) async {
    final data = await _api.post('/auth/login', {
      'username': correo.trim(),
      'password': password,
    });
    final user = Usuario.fromJson(data);
    await _api.saveSession(
      token: user.id,
      usuarioId: user.id,
      usuarioJson: jsonEncode(user.toJson()),
    );

    try {
      final yaGuardadas = await _biometric.tieneCredenciales();
      if (recordar || !yaGuardadas) {
        await _biometric.guardarCredenciales(correo: correo, password: password);
      } else {
        await _biometric.borrarCredenciales();
      }
    } catch (_) {}
    return user;
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

  Future<void> logout() => _api.clearSession();
}
