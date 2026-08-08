import 'dart:convert';
import '../services/api_service.dart';

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

  bool get esDueno => rol == 'DUEÑO';
  bool get esAdministrador => rol == 'ADMINISTRADOR';
  bool get puedeOperaciones => esDueno || esAdministrador;
}

class AuthService {
  AuthService(this._api);
  final ApiService _api;

  Future<Usuario> login(String username) async {
    final data = await _api.post('/auth/login', {'username': username});
    final user = Usuario.fromJson(data);
    await _api.saveSession(
      token: user.id,
      usuarioId: user.id,
      usuarioJson: jsonEncode(user.toJson()),
    );
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
