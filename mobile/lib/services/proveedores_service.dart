import '../services/api_client.dart';

class Proveedor {
  final String id;
  final String nombre;
  final String? telefono;
  final String? rif;
  final double saldoDeudaUsd;

  Proveedor({
    required this.id,
    required this.nombre,
    this.telefono,
    this.rif,
    this.saldoDeudaUsd = 0,
  });

  factory Proveedor.fromJson(Map<String, dynamic> j) => Proveedor(
        id: j['id'],
        nombre: j['nombre'],
        telefono: j['telefono'],
        rif: j['rif'],
        saldoDeudaUsd: (j['saldo_deuda_usd'] as num?)?.toDouble() ?? 0,
      );
}

class ProveedoresService {
  ProveedoresService(this._api);
  final ApiClient _api;

  Future<List<Proveedor>> listar() async {
    final data = await _api.get('/proveedores/') as List;
    return data.map((e) => Proveedor.fromJson(e)).toList();
  }

  Future<Proveedor> crear({
    required String nombre,
    String? telefono,
    String? rif,
    String? contacto,
  }) async {
    final data = await _api.post('/proveedores/', {
      'nombre': nombre,
      if (telefono != null) 'telefono': telefono,
      if (rif != null) 'rif': rif,
      if (contacto != null) 'contacto': contacto,
    });
    return Proveedor.fromJson(data);
  }

  Future<Proveedor> registrarPago(String proveedorId, double montoUsd, {String? descripcion}) async {
    final data = await _api.post('/proveedores/$proveedorId/pagar', {
      'monto_usd': montoUsd,
      if (descripcion != null) 'descripcion': descripcion,
    });
    return Proveedor.fromJson(data);
  }
}
