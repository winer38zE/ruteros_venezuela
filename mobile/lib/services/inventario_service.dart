import '../services/api_client.dart';
import 'productos_service.dart';

export 'productos_service.dart' show ProductoDetalle, ProductosService;

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
  final String productoId;
  final String nombre;
  final int stockTotal;
  final double valorTotalUsd;

  InventarioValoradoItem({
    required this.productoId,
    required this.nombre,
    required this.stockTotal,
    required this.valorTotalUsd,
  });

  factory InventarioValoradoItem.fromJson(Map<String, dynamic> j) =>
      InventarioValoradoItem(
        productoId: j['producto_id'],
        nombre: j['producto_nombre'],
        stockTotal: j['stock_total'],
        valorTotalUsd: (j['valor_total_usd'] as num).toDouble(),
      );
}

class MovimientoInventarioItem {
  final String id;
  final String productoId;
  final String tipo;
  final int cantidad;
  final String? referenciaTipo;
  final String fecha;

  MovimientoInventarioItem({
    required this.id,
    required this.productoId,
    required this.tipo,
    required this.cantidad,
    this.referenciaTipo,
    required this.fecha,
  });

  factory MovimientoInventarioItem.fromJson(Map<String, dynamic> j) => MovimientoInventarioItem(
        id: j['id'],
        productoId: j['producto_id'],
        tipo: j['tipo'],
        cantidad: j['cantidad'],
        referenciaTipo: j['referencia_tipo'],
        fecha: j['fecha'].toString(),
      );
}

/// Producto enriquecido con stock global para la lista de inventario.
class ProductoInventario {
  final ProductoDetalle producto;
  final int stockTotal;

  ProductoInventario({required this.producto, required this.stockTotal});

  bool get bajoStock => producto.stockMinimo > 0 && stockTotal <= producto.stockMinimo;
}

class InventarioService {
  InventarioService(this._api);
  final ApiClient _api;

  static const motivosEntrada = [
    ('compra', 'Compra / Recepción'),
    ('devolucion', 'Devolución de cliente'),
    ('ajuste_positivo', 'Ajuste positivo'),
  ];

  static const motivosSalida = [
    ('merma', 'Merma'),
    ('dano', 'Daño / Pérdida'),
    ('ajuste_negativo', 'Ajuste negativo'),
  ];

  Future<List<StockProducto>> listarStock() async {
    final data = await _api.get('/inventario/stock') as List;
    return data.map((e) => StockProducto.fromJson(e)).toList();
  }

  Future<List<InventarioValoradoItem>> inventarioValorado() async {
    final data = await _api.get('/inventario/valorado') as List;
    return data.map((e) => InventarioValoradoItem.fromJson(e)).toList();
  }

  Future<List<ProductoInventario>> listarProductosConStock() async {
    final productosSvc = ProductosService(_api);
    final productos = await productosSvc.listar();
    List<StockProducto> stockList = [];
    try {
      stockList = await listarStock();
    } catch (_) {
      // Si falla /inventario/stock, mostrar al menos el stock del catálogo.
    }
    final stockMap = {for (final s in stockList) s.productoId: s.stockTotalGlobal};

    return productos.map((p) {
      return ProductoInventario(
        producto: p,
        stockTotal: stockMap[p.id] ?? p.stock,
      );
    }).toList();
  }

  Future<MovimientoInventarioItem> ajustarStock({
    required String productoId,
    required String tipo,
    required int cantidad,
    required String motivo,
  }) async {
    final data = await _api.post('/inventario/movimiento', {
      'producto_id': productoId,
      'tipo': tipo,
      'cantidad': cantidad,
      'motivo': motivo,
    });
    return MovimientoInventarioItem.fromJson(data);
  }
}
