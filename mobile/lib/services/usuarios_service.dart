import '../services/api_client.dart';

class UsuarioEquipo {
  final String id;
  final String nombre;
  final String username;
  final String rol;
  final bool activo;
  final String? telefono;

  UsuarioEquipo({
    required this.id,
    required this.nombre,
    required this.username,
    required this.rol,
    required this.activo,
    this.telefono,
  });

  factory UsuarioEquipo.fromJson(Map<String, dynamic> j) => UsuarioEquipo(
        id: j['id'],
        nombre: j['nombre'],
        username: j['username'],
        rol: j['rol'],
        activo: j['activo'] ?? true,
        telefono: j['telefono'],
      );
}

class UsuariosService {
  UsuariosService(this._api);
  final ApiClient _api;

  static const roles = [
    ('DUEÑO', 'Administrador / Dueño'),
    ('VENDEDOR', 'Vendedor en ruta'),
    ('COBRADOR', 'Cobrador'),
  ];

  Future<List<UsuarioEquipo>> listar() async {
    final data = await _api.get('/usuarios/') as List;
    return data.map((e) => UsuarioEquipo.fromJson(e)).toList();
  }

  Future<UsuarioEquipo> crear({
    required String nombre,
    required String username,
    required String password,
    required String rol,
  }) async {
    final data = await _api.post('/usuarios/', {
      'nombre': nombre,
      'username': username,
      'password': password,
      'rol': rol,
    });
    return UsuarioEquipo.fromJson(data);
  }

  Future<UsuarioEquipo> actualizarActivo(String id, bool activo) async {
    final data = await _api.patch('/usuarios/$id', {'activo': activo});
    return UsuarioEquipo.fromJson(data);
  }
}
