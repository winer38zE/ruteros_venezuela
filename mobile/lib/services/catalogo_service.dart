import '../services/api_client.dart';

class Cliente {
  final String id;
  final String nombre;
  final String tipoCliente;

  Cliente({required this.id, required this.nombre, required this.tipoCliente});

  factory Cliente.fromJson(Map<String, dynamic> j) => Cliente(
        id: j['id'],
        nombre: j['nombre'],
        tipoCliente: j['tipo_cliente'] ?? 'detal',
      );
}

class Producto {
  final String id;
  final String nombre;
  final double precioUsd;
  final int stock;

  Producto({
    required this.id,
    required this.nombre,
    required this.precioUsd,
    required this.stock,
  });

  factory Producto.fromJson(Map<String, dynamic> j) => Producto(
        id: j['id'],
        nombre: j['nombre'],
        precioUsd: (j['precio_usd'] as num).toDouble(),
        stock: j['stock'],
      );
}

class PrecioProducto {
  final String tipoCliente;
  final double precioUsd;

  PrecioProducto({required this.tipoCliente, required this.precioUsd});

  factory PrecioProducto.fromJson(Map<String, dynamic> j) => PrecioProducto(
        tipoCliente: j['tipo_cliente'],
        precioUsd: (j['precio_usd'] as num).toDouble(),
      );
}

class Almacen {
  final String id;
  final String nombre;
  final bool esPrincipal;

  Almacen({required this.id, required this.nombre, required this.esPrincipal});

  factory Almacen.fromJson(Map<String, dynamic> j) => Almacen(
        id: j['id'],
        nombre: j['nombre'],
        esPrincipal: j['es_principal'] ?? false,
      );
}

class TasaCambio {
  final double usdBs;
  final double eurBs;

  TasaCambio({required this.usdBs, required this.eurBs});

  factory TasaCambio.fromJson(Map<String, dynamic> j) => TasaCambio(
        usdBs: (j['usd_bs'] as num).toDouble(),
        eurBs: (j['eur_bs'] as num).toDouble(),
      );
}

class CatalogoService {
  CatalogoService(this._api);
  final ApiClient _api;

  Future<List<Cliente>> listarClientes() async {
    final data = await _api.get('/clientes/') as List;
    return data.map((e) => Cliente.fromJson(e)).toList();
  }

  Future<List<Producto>> listarProductos() async {
    final data = await _api.get('/productos/') as List;
    return data.map((e) => Producto.fromJson(e)).toList();
  }

  Future<List<PrecioProducto>> preciosProducto(String productoId) async {
    final data = await _api.get('/inventario/productos/$productoId/precios') as List;
    return data.map((e) => PrecioProducto.fromJson(e)).toList();
  }

  Future<List<Almacen>> listarAlmacenes() async {
    final data = await _api.get('/inventario/almacenes') as List;
    return data.map((e) => Almacen.fromJson(e)).toList();
  }

  Future<TasaCambio> ultimaTasa() async {
    final data = await _api.get('/tasas-cambio/ultima');
    return TasaCambio.fromJson(data);
  }
}
