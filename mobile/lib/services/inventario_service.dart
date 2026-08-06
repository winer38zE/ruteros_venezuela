import '../services/api_client.dart';

class StockProducto {
  final String productoId;
  final String productoNombre;
  final int stockTotalGlobal;

  StockProducto({
    required this.productoId,
    required this.productoNombre,
    required this.stockTotalGlobal,
  });

  factory StockProducto.fromJson(Map<String, dynamic> j) => StockProducto(
        productoId: j['producto_id'],
        productoNombre: j['producto_nombre'],
        stockTotalGlobal: j['stock_total_global'],
      );
}

class InventarioValoradoItem {
  final String nombre;
  final int stockTotal;
  final double valorTotalUsd;

  InventarioValoradoItem({
    required this.nombre,
    required this.stockTotal,
    required this.valorTotalUsd,
  });

  factory InventarioValoradoItem.fromJson(Map<String, dynamic> j) =>
      InventarioValoradoItem(
        nombre: j['producto_nombre'],
        stockTotal: j['stock_total'],
        valorTotalUsd: (j['valor_total_usd'] as num).toDouble(),
      );
}

class InventarioService {
  InventarioService(this._api);
  final ApiClient _api;

  Future<List<StockProducto>> listarStock() async {
    final data = await _api.get('/inventario/stock') as List;
    return data.map((e) => StockProducto.fromJson(e)).toList();
  }

  Future<List<InventarioValoradoItem>> inventarioValorado() async {
    final data = await _api.get('/inventario/valorado') as List;
    return data.map((e) => InventarioValoradoItem.fromJson(e)).toList();
  }
}
