import 'api_client.dart';

class DatosBancarios {
  final String? banco;
  final String? tipoCuenta;
  final String? numeroCuenta;
  final String? cedulaNit;
  final bool configurado;

  const DatosBancarios({
    this.banco,
    this.tipoCuenta,
    this.numeroCuenta,
    this.cedulaNit,
    this.configurado = false,
  });

  factory DatosBancarios.fromJson(Map<String, dynamic> j) => DatosBancarios(
        banco: j['banco'] as String?,
        tipoCuenta: j['tipo_cuenta'] as String?,
        numeroCuenta: j['numero_cuenta'] as String?,
        cedulaNit: j['cedula_nit'] as String?,
        configurado: j['configurado'] == true,
      );

  Map<String, dynamic> toJson() => {
        'banco': banco,
        'tipo_cuenta': tipoCuenta,
        'numero_cuenta': numeroCuenta,
        'cedula_nit': cedulaNit,
      };
}

class EmpresaService {
  EmpresaService(this._api);
  final ApiClient _api;

  Future<DatosBancarios> datosBancarios() async {
    final data = await _api.get('/empresas/datos-bancarios');
    return DatosBancarios.fromJson(data as Map<String, dynamic>);
  }

  Future<DatosBancarios> guardarDatosBancarios(DatosBancarios datos) async {
    final data = await _api.put('/empresas/datos-bancarios', datos.toJson());
    return DatosBancarios.fromJson(data as Map<String, dynamic>);
  }
}
