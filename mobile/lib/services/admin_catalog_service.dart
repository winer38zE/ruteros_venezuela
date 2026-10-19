import 'api_service.dart';

class CountryAdmin {
  final String id;
  final String nombre;
  final String codigoIso;
  final String? bandera;
  final List<String> paymentCurrencies;
  final bool activo;

  CountryAdmin({
    required this.id,
    required this.nombre,
    required this.codigoIso,
    this.bandera,
    required this.paymentCurrencies,
    required this.activo,
  });

  factory CountryAdmin.fromJson(Map<String, dynamic> j) => CountryAdmin(
        id: j['id'].toString(),
        nombre: j['nombre'] as String,
        codigoIso: j['codigo_iso'] as String,
        bandera: j['bandera'] as String?,
        paymentCurrencies: (j['payment_currencies'] as List<dynamic>?)
                ?.map((e) => e.toString())
                .toList() ??
            [],
        activo: j['activo'] as bool? ?? true,
      );
}

class PayrollRuleAdmin {
  final String id;
  final String paisId;
  final int year;
  final double salarioMinimo;
  final String monedaSalario;
  final bool verified;
  final bool borrador;
  final String? sourceUrl;

  PayrollRuleAdmin({
    required this.id,
    required this.paisId,
    required this.year,
    required this.salarioMinimo,
    required this.monedaSalario,
    required this.verified,
    required this.borrador,
    this.sourceUrl,
  });

  factory PayrollRuleAdmin.fromJson(Map<String, dynamic> j) => PayrollRuleAdmin(
        id: j['id'].toString(),
        paisId: j['pais_id'].toString(),
        year: j['year'] as int,
        salarioMinimo: (j['salario_minimo_mensual'] as num).toDouble(),
        monedaSalario: j['moneda_salario'] as String,
        verified: j['verified'] as bool? ?? false,
        borrador: j['borrador'] as bool? ?? false,
        sourceUrl: j['source_url'] as String?,
      );
}

class AdminCatalogService {
  AdminCatalogService(this._api);
  final ApiService _api;

  Future<List<CountryAdmin>> listarPaises() async {
    final data = await _api.get('/admin/countries');
    return (data as List<dynamic>)
        .map((e) => CountryAdmin.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<PayrollRuleAdmin>> listarReglas({int? year}) async {
    final q = year != null ? '?year=$year' : '';
    final data = await _api.get('/admin/payroll-rules$q');
    return (data as List<dynamic>)
        .map((e) => PayrollRuleAdmin.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<void> duplicarReglasAnio({
    required int desdeYear,
    required int haciaYear,
  }) async {
    await _api.post(
      '/admin/payroll-rules/duplicar-anio?desde_year=$desdeYear&hacia_year=$haciaYear',
      {},
    );
  }
}
