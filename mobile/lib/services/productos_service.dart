import '../services/api_client.dart';

class ProductoDetalle {
  final String id;
  final String nombre;
  final String? sku;
  final String? categoria;
  final double precioUsd;
  final double? precioVes;
  final double? precioCop;
  final double costoUsd;
  final int stock;
  final int stockMinimo;
  final bool activo;
  final String? proveedor;
  final String? condicionPago;
  final DateTime? fechaLimitePago;

  ProductoDetalle({
    required this.id,
    required this.nombre,
    this.sku,
    this.categoria,
    required this.precioUsd,
    this.precioVes,
    this.precioCop,
    required this.costoUsd,
    required this.stock,
    required this.stockMinimo,
    this.activo = true,
    this.proveedor,
    this.condicionPago,
    this.fechaLimitePago,
  });

  static DateTime? _parseFecha(dynamic raw) {
    if (raw == null) return null;
    final s = raw.toString();
    if (s.isEmpty) return null;
    return DateTime.tryParse(s.length <= 10 ? '${s}T00:00:00' : s);
  }

  factory ProductoDetalle.fromJson(Map<String, dynamic> j) => ProductoDetalle(
        id: j['id'],
        nombre: j['nombre'],
        sku: j['sku'],
        categoria: j['categoria'],
        precioUsd: (j['precio_usd'] as num).toDouble(),
        precioVes: j['precio_ves'] != null ? (j['precio_ves'] as num).toDouble() : null,
        precioCop: j['precio_cop'] != null ? (j['precio_cop'] as num).toDouble() : null,
        costoUsd: j['costo_usd'] != null ? (j['costo_usd'] as num).toDouble() : 0,
        stock: j['stock'] ?? 0,
        stockMinimo: j['stock_minimo'] ?? 0,
        activo: j['activo'] ?? true,
        proveedor: j['proveedor']?.toString(),
        condicionPago: j['condicion_pago']?.toString(),
        fechaLimitePago: _parseFecha(j['fecha_limite_pago']),
      );

  bool get bajoStock => stockMinimo > 0 && stock <= stockMinimo;
}

class ProductosService {
  ProductosService(this._api);
  final ApiClient _api;

  static const categoriasBase = [
    'General',
    'Sábanas',
    'Alimentos',
    'Bebidas',
    'Limpieza',
    'Hogar',
    'Ropa',
    'Electrónica',
    'Repuestos',
    'Otros',
  ];

  /// Compatibilidad con pantallas que usan [categorias].
  static List<String> get categorias => List.unmodifiable(categoriasBase);

  static List<String> combinarCategorias({Iterable<String>? extra}) {
    final set = {...categoriasBase, ...?extra};
    final list = set.toList()
      ..sort((a, b) {
        if (a == 'General') return -1;
        if (b == 'General') return 1;
        return a.compareTo(b);
      });
    return list;
  }

  Future<List<ProductoDetalle>> listar() async {
    final data = await _api.get('/productos/') as List;
    return data.map((e) => ProductoDetalle.fromJson(e)).toList();
  }

  Future<ProductoDetalle> obtener(String id) async {
    final data = await _api.get('/productos/$id');
    return ProductoDetalle.fromJson(data);
  }

  Future<ProductoDetalle> crear({
    required String nombre,
    required double precioUsd,
    String? sku,
    String? categoria,
    double? precioVes,
    double? precioCop,
    double costoUsd = 0,
    int stockInicial = 0,
    int stockMinimo = 0,
    String? proveedorId,
    String? proveedor,
    String? condicionPago,
    String? fechaLimitePago,
  }) async {
    final data = await _api.post('/productos/', {
      'nombre': nombre,
      'precio_base_usd': precioUsd,
      if (sku != null && sku.isNotEmpty) 'sku': sku,
      if (categoria != null && categoria.isNotEmpty) 'categoria': categoria,
      if (precioVes != null) 'precio_ves': precioVes,
      if (precioCop != null) 'precio_cop': precioCop,
      'costo_usd': costoUsd,
      'stock_actual': stockInicial,
      'stock_minimo': stockMinimo,
      if (proveedorId != null) 'proveedor_id': proveedorId,
      if (proveedor != null && proveedor.isNotEmpty) 'proveedor': proveedor,
      if (condicionPago != null && condicionPago.isNotEmpty) 'condicion_pago': condicionPago,
      if (fechaLimitePago != null && fechaLimitePago.isNotEmpty)
        'fecha_limite_pago': fechaLimitePago,
    });
    return ProductoDetalle.fromJson(data);
  }

  Future<ProductoDetalle> actualizar(
    String id, {
    String? nombre,
    String? sku,
    String? categoria,
    double? precioUsd,
    double? precioVes,
    double? precioCop,
    double? costoUsd,
    int? stockMinimo,
    String? proveedor,
    String? condicionPago,
    String? fechaLimitePago,
  }) async {
    final body = <String, dynamic>{};
    if (nombre != null) body['nombre'] = nombre;
    if (sku != null) body['sku'] = sku.isEmpty ? null : sku;
    if (categoria != null) body['categoria'] = categoria.isEmpty ? null : categoria;
    if (precioUsd != null) body['precio_base_usd'] = precioUsd;
    if (precioVes != null) body['precio_ves'] = precioVes;
    if (precioCop != null) body['precio_cop'] = precioCop;
    if (costoUsd != null) body['costo_usd'] = costoUsd;
    if (stockMinimo != null) body['stock_minimo'] = stockMinimo;
    if (proveedor != null) body['proveedor'] = proveedor.isEmpty ? null : proveedor;
    if (condicionPago != null) body['condicion_pago'] = condicionPago;
    if (fechaLimitePago != null) {
      body['fecha_limite_pago'] = fechaLimitePago.isEmpty ? null : fechaLimitePago;
    }

    final data = await _api.put('/productos/$id', body);
    return ProductoDetalle.fromJson(data);
  }
}
