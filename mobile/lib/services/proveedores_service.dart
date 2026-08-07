import '../services/api_client.dart';

class Proveedor {
  final String id;
  final String nombre;
  final String? telefono;
  final String? rif;

  Proveedor({required this.id, required this.nombre, this.telefono, this.rif});

  factory Proveedor.fromJson(Map<String, dynamic> j) => Proveedor(
        id: j['id'],
        nombre: j['nombre'],
        telefono: j['telefono'],
        rif: j['rif'],
      );
}

class ProveedoresService {
  ProveedoresService(this._api);
  final ApiClient _api;

  Future<List<Proveedor>> listar() async {
    final data = await _api.get('/proveedores/') as List;
    return data.map((e) => Proveedor.fromJson(e)).toList();
  }

  Future<Proveedor> crear({required String nombre, String? telefono, String? rif}) async {
    final data = await _api.post('/proveedores/', {
      'nombre': nombre,
      if (telefono != null) 'telefono': telefono,
      if (rif != null) 'rif': rif,
    });
    return Proveedor.fromJson(data);
  }
}
