import '../services/api_client.dart';

class FilaCobranza {
  final String id;
  final String clienteId;
  final String clienteNombre;
  final String productosResumen;
  final double costoTotalUsd;
  final double totalUsd;
  final double cobradoUsd;
  final double saldoPendienteUsd;
  final String frecuenciaPago;
  final String tipoCredito;
  final String estado;
  final String estadoCuenta;
  final String? proximoPago;
  final double montoProximaCuotaUsd;
  final int cuotasPagadas;
  final int cuotasTotales;

  FilaCobranza({
    required this.id,
    required this.clienteId,
    required this.clienteNombre,
    required this.productosResumen,
    required this.costoTotalUsd,
    required this.totalUsd,
    required this.cobradoUsd,
    required this.saldoPendienteUsd,
    required this.frecuenciaPago,
    required this.tipoCredito,
    required this.estado,
    required this.estadoCuenta,
    this.proximoPago,
    required this.montoProximaCuotaUsd,
    required this.cuotasPagadas,
    required this.cuotasTotales,
  });

  factory FilaCobranza.fromJson(Map<String, dynamic> j) => FilaCobranza(
        id: j['id'],
        clienteId: j['cliente_id'],
        clienteNombre: j['cliente_nombre'] ?? '—',
        productosResumen: j['productos_resumen'] ?? '—',
        costoTotalUsd: (j['costo_total_usd'] as num?)?.toDouble() ?? 0,
        totalUsd: (j['total_usd'] as num).toDouble(),
        cobradoUsd: (j['cobrado_usd'] as num).toDouble(),
        saldoPendienteUsd: (j['saldo_pendiente_usd'] as num).toDouble(),
        frecuenciaPago: j['frecuencia_pago'] ?? 'contado',
        tipoCredito: j['tipo_credito'] ?? '—',
        estado: j['estado'],
        estadoCuenta: j['estado_cuenta'] ?? 'Al día',
        proximoPago: j['proximo_pago'],
        montoProximaCuotaUsd: (j['monto_proxima_cuota_usd'] as num?)?.toDouble() ?? 0,
        cuotasPagadas: j['cuotas_pagadas'] ?? 0,
        cuotasTotales: j['cuotas_totales'] ?? 0,
      );
}

class VentaPendiente {
  final String id;
  final String clienteId;
  final String clienteNombre;
  final double totalUsd;
  final double cobradoUsd;
  final double saldoPendienteUsd;
  final String estado;

  VentaPendiente({
    required this.id,
    required this.clienteId,
    required this.clienteNombre,
    required this.totalUsd,
    required this.cobradoUsd,
    required this.saldoPendienteUsd,
    required this.estado,
  });

  factory VentaPendiente.fromJson(Map<String, dynamic> j) => VentaPendiente(
        id: j['id'],
        clienteId: j['cliente_id'],
        clienteNombre: j['cliente_nombre'] ?? '—',
        totalUsd: (j['total_usd'] as num).toDouble(),
        cobradoUsd: (j['cobrado_usd'] as num).toDouble(),
        saldoPendienteUsd: (j['saldo_pendiente_usd'] as num).toDouble(),
        estado: j['estado'],
      );
}

class Cobro {
  final String id;
  final String ventaId;
  final double montoUsd;
  final String monedaPago;
  final String fecha;

  Cobro({
    required this.id,
    required this.ventaId,
    required this.montoUsd,
    required this.monedaPago,
    required this.fecha,
  });

  factory Cobro.fromJson(Map<String, dynamic> j) => Cobro(
        id: j['id'],
        ventaId: j['venta_id'],
        montoUsd: (j['monto_usd'] as num).toDouble(),
        monedaPago: j['moneda_pago'],
        fecha: j['fecha'],
      );
}

class CobrosService {
  CobrosService(this._api);
  final ApiClient _api;

  static const monedas = [
    ('bolivar', 'Bolívares'),
    ('dolar', 'Dólares'),
    ('euro', 'Euros'),
    ('pago_movil', 'Pago Móvil'),
    ('transferencia', 'Transferencia'),
  ];

  Future<List<FilaCobranza>> panelCobranza() async {
    final data = await _api.get('/cobros/panel-cobranza') as List;
    return data.map((e) => FilaCobranza.fromJson(e)).toList();
  }

  Future<List<VentaPendiente>> ventasPendientes() async {
    final data = await _api.get('/cobros/ventas-pendientes') as List;
    return data.map((e) => VentaPendiente.fromJson(e)).toList();
  }

  Future<List<Cobro>> misCobros() async {
    final data = await _api.get('/cobros/mis-cobros') as List;
    return data.map((e) => Cobro.fromJson(e)).toList();
  }

  Future<Cobro> registrarCobro({
    required String ventaId,
    required double montoUsd,
    required String monedaPago,
    required double tasaUsd,
    required double tasaEur,
    String? cobroId,
  }) async {
    final body = {
      'venta_id': ventaId,
      'monto_usd': montoUsd,
      'moneda_pago': monedaPago,
      'tasa_usd_aplicada': tasaUsd,
      'tasa_eur_aplicada': tasaEur,
      if (cobroId != null) 'id': cobroId,
    };
    final data = await _api.post('/cobros/', body);
    return Cobro.fromJson(data);
  }
}
