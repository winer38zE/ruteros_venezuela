import 'api_client.dart';

class NominaCalculadaEmpleado {
  final String usuarioId;
  final String empleadoNombre;
  final String rol;
  final String pais;
  final String monedaPrincipal;
  final String tipoPago;
  final double salarioBase;
  final double salarioBaseUsd;
  final double totalComisiones;
  final double totalBonos;
  final double? porcentajeCobro;
  final int numVentas;
  final double totalCobradoUsd;
  final double totalPagarUsd;
  final double totalPagarLocal;
  final double tasaCambioAplicada;
  final Map<String, dynamic> tasas;
  final Map<String, double> detallesPago;
  final String? advertenciaDetalle;

  NominaCalculadaEmpleado({
    required this.usuarioId,
    required this.empleadoNombre,
    required this.rol,
    required this.pais,
    required this.monedaPrincipal,
    required this.tipoPago,
    required this.salarioBase,
    required this.salarioBaseUsd,
    required this.totalComisiones,
    required this.totalBonos,
    this.porcentajeCobro,
    required this.numVentas,
    required this.totalCobradoUsd,
    required this.totalPagarUsd,
    required this.totalPagarLocal,
    required this.tasaCambioAplicada,
    required this.tasas,
    required this.detallesPago,
    this.advertenciaDetalle,
  });

  factory NominaCalculadaEmpleado.fromJson(Map<String, dynamic> j) {
    final rawDet = j['detalles_pago'] as Map<String, dynamic>? ?? {};
    final det = <String, double>{};
    rawDet.forEach((k, v) {
      if (v is num && k != 'tasas') det[k] = v.toDouble();
    });
    return NominaCalculadaEmpleado(
      usuarioId: j['usuario_id'] as String,
      empleadoNombre: j['empleado_nombre'] as String,
      rol: j['rol'] as String,
      pais: j['pais'] as String,
      monedaPrincipal: j['moneda_principal'] as String,
      tipoPago: j['tipo_pago'] as String,
      salarioBase: (j['salario_base'] as num).toDouble(),
      salarioBaseUsd: (j['salario_base_usd'] as num).toDouble(),
      totalComisiones: (j['total_comisiones'] as num).toDouble(),
      totalBonos: (j['total_bonos'] as num).toDouble(),
      porcentajeCobro: j['porcentaje_cobro'] != null ? (j['porcentaje_cobro'] as num).toDouble() : null,
      numVentas: j['num_ventas'] as int? ?? 0,
      totalCobradoUsd: (j['total_cobrado_usd'] as num?)?.toDouble() ?? 0,
      totalPagarUsd: (j['total_pagar_usd'] as num).toDouble(),
      totalPagarLocal: (j['total_pagar_local'] as num).toDouble(),
      tasaCambioAplicada: (j['tasa_cambio_aplicada'] as num).toDouble(),
      tasas: Map<String, dynamic>.from(j['tasas'] as Map? ?? {}),
      detallesPago: det,
      advertenciaDetalle: j['advertencia_detalle'] as String?,
    );
  }
}

class TasasNomina {
  final double usdToVes;
  final double usdToCop;

  TasasNomina({required this.usdToVes, required this.usdToCop});

  factory TasasNomina.fromJson(Map<String, dynamic> j) => TasasNomina(
        usdToVes: (j['USD_TO_VES'] as num).toDouble(),
        usdToCop: (j['USD_TO_COP'] as num).toDouble(),
      );
}

class NominaPagoService {
  NominaPagoService(this._api);
  final ApiClient _api;

  Future<TasasNomina> obtenerTasas() async {
    final data = await _api.get('/nomina/tasas');
    return TasasNomina.fromJson(data);
  }

  Future<NominaCalculadaEmpleado> calcular({
    required String usuarioId,
    String? pais,
    String tipoPago = 'mixto',
    double? salarioBase,
    double totalBonos = 0,
    double? porcentajeCobro,
    Map<String, double>? detallesPago,
  }) async {
    final data = await _api.post('/nomina/calcular', {
      'usuario_id': usuarioId,
      if (pais != null) 'pais': pais,
      'tipo_pago': tipoPago,
      if (salarioBase != null) 'salario_base': salarioBase,
      'total_bonos': totalBonos,
      if (porcentajeCobro != null) 'porcentaje_cobro': porcentajeCobro,
      if (detallesPago != null && detallesPago.isNotEmpty) 'detalles_pago': detallesPago,
    });
    return NominaCalculadaEmpleado.fromJson(data);
  }

  Future<void> procesar({
    required String usuarioId,
    String? pais,
    String tipoPago = 'mixto',
    double? salarioBase,
    double totalBonos = 0,
    double? porcentajeCobro,
    Map<String, double>? detallesPago,
    bool forzarDesglose = false,
    String? notas,
  }) async {
    await _api.post('/nomina/procesar', {
      'usuario_id': usuarioId,
      if (pais != null) 'pais': pais,
      'tipo_pago': tipoPago,
      if (salarioBase != null) 'salario_base': salarioBase,
      'total_bonos': totalBonos,
      if (porcentajeCobro != null) 'porcentaje_cobro': porcentajeCobro,
      if (detallesPago != null && detallesPago.isNotEmpty) 'detalles_pago': detallesPago,
      if (forzarDesglose) 'forzar_desglose': true,
      if (notas != null) 'notas': notas,
    });
  }
}
