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
  final double? montoOriginal;
  final String moneda;
  final String? metodoPago;
  final String descripcion;
  final String fecha;
  final bool tieneComprobante;

  MovimientoFinanciero({
    required this.id,
    required this.tipo,
    required this.categoria,
    required this.montoUsd,
    this.montoOriginal,
    required this.moneda,
    this.metodoPago,
    required this.descripcion,
    required this.fecha,
    this.tieneComprobante = false,
  });

  factory MovimientoFinanciero.fromJson(Map<String, dynamic> j) => MovimientoFinanciero(
        id: j['id'],
        tipo: j['tipo'],
        categoria: j['categoria'],
        montoUsd: (j['monto_usd'] as num).toDouble(),
        montoOriginal: j['monto_original'] != null ? (j['monto_original'] as num).toDouble() : null,
        moneda: j['moneda'] ?? 'usd',
        metodoPago: j['metodo_pago'],
        descripcion: j['descripcion'],
        fecha: j['fecha'],
        tieneComprobante: j['tiene_comprobante'] ?? false,
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

  double get comisionesTotalUsd => comisionVentasUsd + comisionCobrosUsd;

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
  final double sueldoBaseLegalPais;
  final double porcentajeComisionVentaPais;
  final double porcentajeComisionCobroPais;
  final String monedaPrincipal;
  final String simboloMoneda;

  NominaCalculada({
    required this.empleados,
    required this.totalPendienteUsd,
    required this.comisionVendedorPorArticulo,
    required this.comisionCobradorPorcentaje,
    this.sueldoBaseLegalPais = 0,
    this.porcentajeComisionVentaPais = 0,
    this.porcentajeComisionCobroPais = 0,
    this.monedaPrincipal = 'USD',
    this.simboloMoneda = r'$',
  });

  factory NominaCalculada.fromJson(Map<String, dynamic> j) => NominaCalculada(
        empleados: (j['empleados'] as List).map((e) => DetalleNominaEmpleado.fromJson(e)).toList(),
        totalPendienteUsd: (j['total_pendiente_usd'] as num).toDouble(),
        comisionVendedorPorArticulo: (j['comision_vendedor_por_articulo_usd'] as num).toDouble(),
        comisionCobradorPorcentaje: (j['comision_cobrador_porcentaje'] as num).toDouble(),
        sueldoBaseLegalPais: (j['sueldo_base_legal_pais'] as num?)?.toDouble() ?? 0,
        porcentajeComisionVentaPais: (j['porcentaje_comision_venta_pais'] as num?)?.toDouble() ?? 0,
        porcentajeComisionCobroPais: (j['porcentaje_comision_cobro_pais'] as num?)?.toDouble() ?? 0,
        monedaPrincipal: j['moneda_principal']?.toString() ?? 'USD',
        simboloMoneda: j['simbolo_moneda']?.toString() ?? r'$',
      );
}

class ParametrosNominaPais {
  final String paisId;
  final String nombre;
  final String codigoIso;
  final String monedaPrincipal;
  final String simboloMoneda;
  final double sueldoBaseLegal;
  final double porcentajeComisionVenta;
  final double porcentajeComisionCobro;
  final double bonoIncentivo;

  ParametrosNominaPais({
    required this.paisId,
    required this.nombre,
    required this.codigoIso,
    required this.monedaPrincipal,
    required this.simboloMoneda,
    required this.sueldoBaseLegal,
    required this.porcentajeComisionVenta,
    required this.porcentajeComisionCobro,
    required this.bonoIncentivo,
  });

  factory ParametrosNominaPais.fromJson(Map<String, dynamic> j) => ParametrosNominaPais(
        paisId: j['pais_id'].toString(),
        nombre: j['nombre'].toString(),
        codigoIso: j['codigo_iso'].toString(),
        monedaPrincipal: j['moneda_principal'].toString(),
        simboloMoneda: j['simbolo_moneda'].toString(),
        sueldoBaseLegal: (j['sueldo_base_legal'] as num).toDouble(),
        porcentajeComisionVenta: (j['porcentaje_comision_venta'] as num).toDouble(),
        porcentajeComisionCobro: (j['porcentaje_comision_cobro'] as num).toDouble(),
        bonoIncentivo: (j['bono_incentivo'] as num?)?.toDouble() ?? 0,
      );
}

class FinanzasService {
  FinanzasService(this._api);
  final ApiClient _api;

  static const categoriasGasto = [
    ('gasto_moto', 'Moto / Vehículo (repuestos, gasolina, taller)'),
    ('pago_proveedor', 'Pago a Proveedor'),
    ('servicios_operativos', 'Servicios y Gastos Operativos'),
    ('operacion_general', 'Operación General'),
  ];

  static const categoriasSalida = [
    ...categoriasGasto,
    ('pago_vendedor', 'Pago a Vendedor'),
    ('pago_cobrador', 'Pago a Cobrador'),
  ];

  static const categoriasEntrada = [
    ('ingreso_operativo', 'Ingreso Operativo'),
  ];

  static const monedas = [('usd', 'USD'), ('ves', 'VES'), ('cop', 'COP')];

  static const metodosPago = [
    ('efectivo', 'Efectivo'),
    ('transferencia', 'Transferencia'),
    ('pago_movil', 'Pago Móvil'),
    ('tarjeta', 'Tarjeta'),
    ('otro', 'Otro'),
  ];

  Map<String, String> _queryFechas({DateTime? desde, DateTime? hasta}) {
    final q = <String, String>{};
    if (desde != null) q['fecha_desde'] = DateTime(desde.year, desde.month, desde.day).toIso8601String();
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

  Future<MovimientoFinanciero> registrarGasto({
    required String categoria,
    required double monto,
    required String moneda,
    required String descripcion,
    String? metodoPago,
    double? tasaAplicada,
    String? proveedorId,
    String? comprobanteBase64,
  }) async {
    final data = await _api.post('/finanzas/movimientos', {
      'tipo': 'salida',
      'categoria': categoria,
      'monto': monto,
      'moneda': moneda,
      'descripcion': descripcion,
      if (metodoPago != null) 'metodo_pago': metodoPago,
      if (tasaAplicada != null) 'tasa_aplicada': tasaAplicada,
      if (proveedorId != null) 'proveedor_id': proveedorId,
      if (comprobanteBase64 != null) 'comprobante_base64': comprobanteBase64,
    });
    return MovimientoFinanciero.fromJson(data);
  }

  Future<MovimientoFinanciero> registrarMovimiento({
    required String tipo,
    required String categoria,
    required double montoUsd,
    required String descripcion,
    String moneda = 'usd',
    String? metodoPago,
  }) async {
    final data = await _api.post('/finanzas/movimientos', {
      'tipo': tipo,
      'categoria': categoria,
      'monto': montoUsd,
      'moneda': moneda,
      'descripcion': descripcion,
      if (metodoPago != null) 'metodo_pago': metodoPago,
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
    String? descripcion,
  }) async {
    await _api.post('/finanzas/nomina/aprobar-pago', {
      'empleado_id': empleadoId,
      'monto_usd': montoUsd,
      if (descripcion != null) 'descripcion': descripcion,
    });
  }

  Future<ParametrosNominaPais> obtenerParametrosNominaPais() async {
    final data = await _api.get('/finanzas/nomina/parametros-pais');
    return ParametrosNominaPais.fromJson(data);
  }

  Future<ParametrosNominaPais> guardarParametrosNominaPais({
    required double sueldoBaseLegal,
    required double porcentajeComisionVenta,
    required double porcentajeComisionCobro,
    double? bonoIncentivo,
  }) async {
    final data = await _api.put('/finanzas/nomina/parametros-pais', {
      'sueldo_base_legal': sueldoBaseLegal,
      'porcentaje_comision_venta': porcentajeComisionVenta,
      'porcentaje_comision_cobro': porcentajeComisionCobro,
      if (bonoIncentivo != null) 'bono_incentivo': bonoIncentivo,
    });
    return ParametrosNominaPais.fromJson(data);
  }
}
