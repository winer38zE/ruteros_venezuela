import '../services/api_client.dart';

class ResumenContable {
  final String pais;
  final double totalVentasUsd;
  final double totalCobradoUsd;
  final double cuentasPorCobrarUsd;
  final double ivaEstimadoUsd;
  final int asientosGenerados;

  ResumenContable({
    required this.pais,
    required this.totalVentasUsd,
    required this.totalCobradoUsd,
    required this.cuentasPorCobrarUsd,
    required this.ivaEstimadoUsd,
    required this.asientosGenerados,
  });

  factory ResumenContable.fromJson(Map<String, dynamic> j) => ResumenContable(
        pais: j['pais'],
        totalVentasUsd: (j['total_ventas_usd'] as num).toDouble(),
        totalCobradoUsd: (j['total_cobrado_usd'] as num).toDouble(),
        cuentasPorCobrarUsd: (j['cuentas_por_cobrar_usd'] as num).toDouble(),
        ivaEstimadoUsd: (j['iva_estimado_usd'] as num).toDouble(),
        asientosGenerados: j['asientos_generados'],
      );
}

class ExportacionExcelInfo {
  final String empresa;
  final String pais;
  final String? rif;
  final int totalVentas;
  final int totalCobros;
  final int totalAsientos;
  final double valorInventarioUsd;
  final List<String> hojas;
  final String? fechaDesde;
  final String? fechaHasta;

  ExportacionExcelInfo({
    required this.empresa,
    required this.pais,
    this.rif,
    required this.totalVentas,
    required this.totalCobros,
    required this.totalAsientos,
    required this.valorInventarioUsd,
    required this.hojas,
    this.fechaDesde,
    this.fechaHasta,
  });

  factory ExportacionExcelInfo.fromJson(Map<String, dynamic> j) =>
      ExportacionExcelInfo(
        empresa: j['empresa'],
        pais: j['pais'],
        rif: j['rif'],
        totalVentas: j['total_ventas'],
        totalCobros: j['total_cobros'],
        totalAsientos: j['total_asientos'],
        valorInventarioUsd: (j['valor_inventario_usd'] as num).toDouble(),
        hojas: List<String>.from(j['hojas']),
        fechaDesde: j['fecha_desde'],
        fechaHasta: j['fecha_hasta'],
      );
}

class ContabilidadService {
  ContabilidadService(this._api);
  final ApiClient _api;

  Map<String, String> _queryFechas({DateTime? fechaDesde, DateTime? fechaHasta}) {
    final q = <String, String>{};
    if (fechaDesde != null) {
      q['fecha_desde'] = DateTime(fechaDesde.year, fechaDesde.month, fechaDesde.day).toIso8601String();
    }
    if (fechaHasta != null) {
      final fin = DateTime(fechaHasta.year, fechaHasta.month, fechaHasta.day, 23, 59, 59);
      q['fecha_hasta'] = fin.toIso8601String();
    }
    return q;
  }

  Future<ResumenContable> obtenerResumen() async {
    final data = await _api.get('/contabilidad/resumen');
    return ResumenContable.fromJson(data);
  }

  Future<ExportacionExcelInfo> infoExportacion({
    DateTime? fechaDesde,
    DateTime? fechaHasta,
  }) async {
    final data = await _api.get(
      '/contabilidad/exportar-excel/info',
      query: _queryFechas(fechaDesde: fechaDesde, fechaHasta: fechaHasta),
    );
    return ExportacionExcelInfo.fromJson(data);
  }

  Future<List<int>> descargarExcel({
    DateTime? fechaDesde,
    DateTime? fechaHasta,
  }) =>
      _api.download(
        '/contabilidad/exportar-excel',
        query: _queryFechas(fechaDesde: fechaDesde, fechaHasta: fechaHasta),
      );
}
