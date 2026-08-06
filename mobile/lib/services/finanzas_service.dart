import '../services/api_client.dart';

class ResumenFinanciero {
  final double totalEntradasUsd;
  final double totalSalidasUsd;
  final double gastosMotoUsd;
  final double nominaPendienteUsd;
  final double balanceNetoUsd;
  final double totalCobrosOperativosUsd;

  ResumenFinanciero({
    required this.totalEntradasUsd,
    required this.totalSalidasUsd,
    required this.gastosMotoUsd,
    required this.nominaPendienteUsd,
    required this.balanceNetoUsd,
    required this.totalCobrosOperativosUsd,
  });

  factory ResumenFinanciero.fromJson(Map<String, dynamic> j) => ResumenFinanciero(
        totalEntradasUsd: (j['total_entradas_usd'] as num).toDouble(),
        totalSalidasUsd: (j['total_salidas_usd'] as num).toDouble(),
        gastosMotoUsd: (j['gastos_moto_usd'] as num).toDouble(),
        nominaPendienteUsd: (j['nomina_pendiente_usd'] as num).toDouble(),
        balanceNetoUsd: (j['balance_neto_usd'] as num).toDouble(),
        totalCobrosOperativosUsd: (j['total_cobros_operativos_usd'] as num).toDouble(),
      );
}

class MovimientoFinanciero {
  final String id;
  final String tipo;
  final String categoria;
  final double montoUsd;
  final String descripcion;
  final String fecha;

  MovimientoFinanciero({
    required this.id,
    required this.tipo,
    required this.categoria,
    required this.montoUsd,
    required this.descripcion,
    required this.fecha,
  });

  factory MovimientoFinanciero.fromJson(Map<String, dynamic> j) => MovimientoFinanciero(
        id: j['id'],
        tipo: j['tipo'],
        categoria: j['categoria'],
        montoUsd: (j['monto_usd'] as num).toDouble(),
        descripcion: j['descripcion'],
        fecha: j['fecha'],
      );
}

class DetalleNominaEmpleado {
  final String empleadoId;
  final String empleadoNombre;
  final String rol;
  final int articulosVendidos;
  final double comisionVentasUsd;
  final double totalCobradoUsd;
  final double comisionCobrosUsd;
  final double sueldoBaseUsd;
  final double totalCalculadoUsd;
  final double totalPagadoUsd;
  final double pendienteUsd;

  DetalleNominaEmpleado({
    required this.empleadoId,
    required this.empleadoNombre,
    required this.rol,
    required this.articulosVendidos,
    required this.comisionVentasUsd,
    required this.totalCobradoUsd,
    required this.comisionCobrosUsd,
    required this.sueldoBaseUsd,
    required this.totalCalculadoUsd,
    required this.totalPagadoUsd,
    required this.pendienteUsd,
  });

  factory DetalleNominaEmpleado.fromJson(Map<String, dynamic> j) => DetalleNominaEmpleado(
        empleadoId: j['empleado_id'],
        empleadoNombre: j['empleado_nombre'],
        rol: j['rol'],
        articulosVendidos: j['articulos_vendidos'] ?? 0,
        comisionVentasUsd: (j['comision_ventas_usd'] as num).toDouble(),
        totalCobradoUsd: (j['total_cobrado_usd'] as num).toDouble(),
        comisionCobrosUsd: (j['comision_cobros_usd'] as num).toDouble(),
        sueldoBaseUsd: (j['sueldo_base_usd'] as num).toDouble(),
        totalCalculadoUsd: (j['total_calculado_usd'] as num).toDouble(),
        totalPagadoUsd: (j['total_pagado_usd'] as num).toDouble(),
        pendienteUsd: (j['pendiente_usd'] as num).toDouble(),
      );
}

class NominaCalculada {
  final List<DetalleNominaEmpleado> empleados;
  final double totalPendienteUsd;
  final double comisionVendedorPorArticulo;
  final double comisionCobradorPorcentaje;

  NominaCalculada({
    required this.empleados,
    required this.totalPendienteUsd,
    required this.comisionVendedorPorArticulo,
    required this.comisionCobradorPorcentaje,
  });

  factory NominaCalculada.fromJson(Map<String, dynamic> j) => NominaCalculada(
        empleados: (j['empleados'] as List)
            .map((e) => DetalleNominaEmpleado.fromJson(e))
            .toList(),
        totalPendienteUsd: (j['total_pendiente_usd'] as num).toDouble(),
        comisionVendedorPorArticulo: (j['comision_vendedor_por_articulo_usd'] as num).toDouble(),
        comisionCobradorPorcentaje: (j['comision_cobrador_porcentaje'] as num).toDouble(),
      );
}

class FinanzasService {
  FinanzasService(this._api);
  final ApiClient _api;

  static const categoriasSalida = [
    ('pago_vendedor', 'Pago a Vendedor'),
    ('pago_cobrador', 'Pago a Cobrador'),
    ('pago_proveedor', 'Pago a Proveedor'),
    ('gasto_moto', 'Gasto de Moto'),
    ('operacion_general', 'Operación General'),
  ];

  static const categoriasEntrada = [
    ('ingreso_operativo', 'Ingreso Operativo'),
    ('operacion_general', 'Operación General'),
  ];

  Map<String, String> _queryFechas({DateTime? desde, DateTime? hasta}) {
    final q = <String, String>{};
    if (desde != null) {
      q['fecha_desde'] = DateTime(desde.year, desde.month, desde.day).toIso8601String();
    }
    if (hasta != null) {
      final fin = DateTime(hasta.year, hasta.month, hasta.day, 23, 59, 59);
      q['fecha_hasta'] = fin.toIso8601String();
    }
    return q;
  }

  Future<ResumenFinanciero> obtenerResumen({DateTime? fechaDesde, DateTime? fechaHasta}) async {
    final data = await _api.get('/finanzas/resumen', query: _queryFechas(desde: fechaDesde, hasta: fechaHasta));
    return ResumenFinanciero.fromJson(data);
  }

  Future<List<MovimientoFinanciero>> listarMovimientos({DateTime? fechaDesde, DateTime? fechaHasta}) async {
    final data = await _api.get('/finanzas/movimientos', query: _queryFechas(desde: fechaDesde, hasta: fechaHasta)) as List;
    return data.map((e) => MovimientoFinanciero.fromJson(e)).toList();
  }

  Future<MovimientoFinanciero> registrarMovimiento({
    required String tipo,
    required String categoria,
    required double montoUsd,
    required String descripcion,
  }) async {
    final data = await _api.post('/finanzas/movimientos', {
      'tipo': tipo,
      'categoria': categoria,
      'monto_usd': montoUsd,
      'descripcion': descripcion,
    });
    return MovimientoFinanciero.fromJson(data);
  }

  Future<NominaCalculada> calcularNomina({DateTime? fechaDesde, DateTime? fechaHasta}) async {
    final data = await _api.get('/finanzas/nomina/calcular', query: _queryFechas(desde: fechaDesde, hasta: fechaHasta));
    return NominaCalculada.fromJson(data);
  }

  Future<void> aprobarPago({
    required String empleadoId,
    required double montoUsd,
    DateTime? periodoDesde,
    DateTime? periodoHasta,
    String? descripcion,
  }) async {
    await _api.post('/finanzas/nomina/aprobar-pago', {
      'empleado_id': empleadoId,
      'monto_usd': montoUsd,
      if (periodoDesde != null) 'periodo_desde': periodoDesde.toIso8601String(),
      if (periodoHasta != null) 'periodo_hasta': periodoHasta.toIso8601String(),
      if (descripcion != null) 'descripcion': descripcion,
    });
  }
}
