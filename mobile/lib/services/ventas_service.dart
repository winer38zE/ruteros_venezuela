import '../services/api_client.dart';

class CuotaAmortizacion {
  final String id;
  final int numeroCuota;
  final String fechaVencimiento;
  final double montoUsd;
  final double montoPagadoUsd;
  final String estado;

  CuotaAmortizacion({
    required this.id,
    required this.numeroCuota,
    required this.fechaVencimiento,
    required this.montoUsd,
    required this.montoPagadoUsd,
    required this.estado,
  });

  factory CuotaAmortizacion.fromJson(Map<String, dynamic> j) => CuotaAmortizacion(
        id: j['id'],
        numeroCuota: j['numero_cuota'],
        fechaVencimiento: j['fecha_vencimiento'],
        montoUsd: (j['monto_usd'] as num).toDouble(),
        montoPagadoUsd: (j['monto_pagado_usd'] as num).toDouble(),
        estado: j['estado'],
      );
}

class DetalleVenta {
  final String id;
  final String productoId;
  final int cantidad;
  final double precioUnitarioUsd;

  DetalleVenta({
    required this.id,
    required this.productoId,
    required this.cantidad,
    required this.precioUnitarioUsd,
  });

  factory DetalleVenta.fromJson(Map<String, dynamic> j) => DetalleVenta(
        id: j['id'],
        productoId: j['producto_id'],
        cantidad: j['cantidad'],
        precioUnitarioUsd: (j['precio_unitario_usd'] as num).toDouble(),
      );

  double get subtotal => precioUnitarioUsd * cantidad;
}

class Venta {
  final String id;
  final String clienteId;
  final String vendedorId;
  final double totalUsd;
  final String estado;
  final String frecuenciaPago;
  final List<DetalleVenta> detalles;
  final List<CuotaAmortizacion> cuotas;

  Venta({
    required this.id,
    required this.clienteId,
    required this.vendedorId,
    required this.totalUsd,
    required this.estado,
    required this.frecuenciaPago,
    required this.detalles,
    required this.cuotas,
  });

  factory Venta.fromJson(Map<String, dynamic> j) => Venta(
        id: j['id'],
        clienteId: j['cliente_id'],
        vendedorId: j['vendedor_id'],
        totalUsd: (j['total_usd'] as num).toDouble(),
        estado: j['estado'],
        frecuenciaPago: j['frecuencia_pago'] ?? 'contado',
        detalles: (j['detalles'] as List? ?? [])
            .map((e) => DetalleVenta.fromJson(e))
            .toList(),
        cuotas: (j['cuotas'] as List? ?? [])
            .map((e) => CuotaAmortizacion.fromJson(e))
            .toList(),
      );
}

class ItemCarrito {
  final String productoId;
  final String nombre;
  final int cantidad;
  final double precioUnitario;
  final String tipoPrecio;

  ItemCarrito({
    required this.productoId,
    required this.nombre,
    required this.cantidad,
    required this.precioUnitario,
    required this.tipoPrecio,
  });

  double get subtotal => precioUnitario * cantidad;

  Map<String, dynamic> toDetalleJson() => {
        'producto_id': productoId,
        'cantidad': cantidad,
        'tipo_precio': tipoPrecio,
      };
}

class VentasService {
  VentasService(this._api);
  final ApiClient _api;

  Future<List<Venta>> misVentas() async {
    final data = await _api.get('/ventas/mis-ventas') as List;
    return data.map((e) => Venta.fromJson(e)).toList();
  }

  Future<List<CuotaAmortizacion>> amortizacion(String ventaId) async {
    final data = await _api.get('/ventas/$ventaId/amortizacion') as List;
    return data.map((e) => CuotaAmortizacion.fromJson(e)).toList();
  }

  Future<Venta> aprobarBorrador(String ventaId) async {
    final data = await _api.post('/ventas/$ventaId/aprobar', {});
    return Venta.fromJson(data);
  }

  Future<Venta> crearVenta({
    required String clienteId,
    required double totalUsd,
    required double tasaUsd,
    required double tasaEur,
    required String frecuenciaPago,
    required List<ItemCarrito> items,
    String? almacenId,
    String? ventaId,
    int? numeroCuotas,
    String tipoTasaUsd = 'bcv',
    bool esBorrador = false,
  }) async {
    final body = {
      'cliente_id': clienteId,
      'total_usd': totalUsd,
      'tasa_usd_aplicada': tasaUsd,
      'tasa_eur_aplicada': tasaEur,
      'frecuencia_pago': frecuenciaPago,
      'tipo_tasa_usd': tipoTasaUsd,
      'es_borrador': esBorrador,
      if (numeroCuotas != null) 'numero_cuotas': numeroCuotas,
      if (almacenId != null) 'almacen_id': almacenId,
      if (ventaId != null) 'id': ventaId,
      'detalles': items.map((i) => i.toDetalleJson()).toList(),
    };
    final data = await _api.post('/ventas/', body);
    return Venta.fromJson(data);
  }
}
