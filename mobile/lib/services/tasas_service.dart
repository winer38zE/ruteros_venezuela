import '../services/api_client.dart';

class TasaCambioDetalle {
  final String id;
  final double usdBcvBs;
  final double usdParaleloBs;
  final double copUsd;
  final double? copVes;
  final double eurBs;
  final String momento;
  final String fecha;

  TasaCambioDetalle({
    required this.id,
    required this.usdBcvBs,
    required this.usdParaleloBs,
    required this.copUsd,
    this.copVes,
    required this.eurBs,
    required this.momento,
    required this.fecha,
  });

  factory TasaCambioDetalle.fromJson(Map<String, dynamic> j) => TasaCambioDetalle(
        id: j['id'],
        usdBcvBs: (j['usd_bcv_bs'] ?? j['usd_bs'] as num).toDouble(),
        usdParaleloBs: (j['usd_paralelo_bs'] ?? j['usd_bs'] as num).toDouble(),
        copUsd: (j['cop_usd'] as num?)?.toDouble() ?? 0,
        copVes: (j['cop_ves'] as num?)?.toDouble(),
        eurBs: (j['eur_bs'] as num?)?.toDouble() ?? 0,
        momento: j['momento'] ?? 'manana',
        fecha: j['fecha'],
      );
}

class ConversionResult {
  final double montoOrigen;
  final String monedaOrigen;
  final double montoDestino;
  final String monedaDestino;

  ConversionResult({
    required this.montoOrigen,
    required this.monedaOrigen,
    required this.montoDestino,
    required this.monedaDestino,
  });

  factory ConversionResult.fromJson(Map<String, dynamic> j) => ConversionResult(
        montoOrigen: (j['monto_origen'] as num).toDouble(),
        monedaOrigen: j['moneda_origen'],
        montoDestino: (j['monto_destino'] as num).toDouble(),
        monedaDestino: j['moneda_destino'],
      );
}

class TasaSincronizacionResult {
  final bool exito;
  final String momento;
  final int empresasActualizadas;
  final double usdBcvBs;
  final double usdParaleloBs;
  final double copUsd;
  final Map<String, dynamic> fuentes;
  final String mensaje;
  final TasaCambioDetalle? tasa;

  TasaSincronizacionResult({
    required this.exito,
    required this.momento,
    required this.empresasActualizadas,
    required this.usdBcvBs,
    required this.usdParaleloBs,
    required this.copUsd,
    required this.fuentes,
    required this.mensaje,
    this.tasa,
  });

  factory TasaSincronizacionResult.fromJson(Map<String, dynamic> j) =>
      TasaSincronizacionResult(
        exito: j['exito'] ?? true,
        momento: j['momento'] ?? 'manana',
        empresasActualizadas: j['empresas_actualizadas'] ?? 0,
        usdBcvBs: (j['usd_bcv_bs'] as num).toDouble(),
        usdParaleloBs: (j['usd_paralelo_bs'] as num).toDouble(),
        copUsd: (j['cop_usd'] as num).toDouble(),
        fuentes: Map<String, dynamic>.from(j['fuentes'] ?? {}),
        mensaje: j['mensaje'] ?? 'Sincronizado',
        tasa: j['tasa'] != null ? TasaCambioDetalle.fromJson(j['tasa']) : null,
      );
}

class TasasService {
  TasasService(this._api);
  final ApiClient _api;

  Future<TasaCambioDetalle> ultima() async {
    final data = await _api.get('/tasas-cambio/ultima');
    return TasaCambioDetalle.fromJson(data);
  }

  Future<List<TasaCambioDetalle>> historial() async {
    final data = await _api.get('/tasas-cambio/') as List;
    return data.map((e) => TasaCambioDetalle.fromJson(e)).toList();
  }

  Future<TasaCambioDetalle> registrar({
    required double usdBcvBs,
    required double usdParaleloBs,
    required double copUsd,
    double eurBs = 0,
    String momento = 'manana',
  }) async {
    final data = await _api.post('/tasas-cambio/', {
      'usd_bcv_bs': usdBcvBs,
      'usd_paralelo_bs': usdParaleloBs,
      'cop_usd': copUsd,
      'eur_bs': eurBs,
      'momento': momento,
    });
    return TasaCambioDetalle.fromJson(data);
  }

  Future<ConversionResult> convertir({
    required double monto,
    required String monedaOrigen,
    required String monedaDestino,
    String tipoTasaUsd = 'bcv',
  }) async {
    final data = await _api.post('/tasas-cambio/convertir', {
      'monto': monto,
      'moneda_origen': monedaOrigen,
      'moneda_destino': monedaDestino,
      'tipo_tasa_usd': tipoTasaUsd,
    });
    return ConversionResult.fromJson(data);
  }

  Future<TasaSincronizacionResult> sincronizarAuto() async {
    final data = await _api.post('/tasas-cambio/sincronizar-auto', {});
    return TasaSincronizacionResult.fromJson(data);
  }
}
