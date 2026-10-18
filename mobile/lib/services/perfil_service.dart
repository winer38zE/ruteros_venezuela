import 'api_service.dart';

class CuentaBancariaEmpleado {
  final String id;
  final String banco;
  final String tipoCuenta;
  final String? numeroCuenta;
  final String titular;
  final String documentoIdentidad;
  final String canal;
  final String? telefonoPagoMovil;

  CuentaBancariaEmpleado({
    required this.id,
    required this.banco,
    required this.tipoCuenta,
    this.numeroCuenta,
    required this.titular,
    required this.documentoIdentidad,
    required this.canal,
    this.telefonoPagoMovil,
  });

  factory CuentaBancariaEmpleado.fromJson(Map<String, dynamic> j) =>
      CuentaBancariaEmpleado(
        id: j['id'].toString(),
        banco: j['banco'].toString(),
        tipoCuenta: j['tipo_cuenta'].toString(),
        numeroCuenta: j['numero_cuenta']?.toString(),
        titular: j['titular'].toString(),
        documentoIdentidad: j['documento_identidad'].toString(),
        canal: j['canal']?.toString() ?? 'transferencia',
        telefonoPagoMovil: j['telefono_pago_movil']?.toString(),
      );
}

class PerfilService {
  PerfilService(this._api);

  final ApiService _api;

  Future<CuentaBancariaEmpleado?> obtenerCuentaBancaria() async {
    try {
      final data = await _api.get('/perfil/cuenta-bancaria');
      if (data is Map<String, dynamic>) {
        return CuentaBancariaEmpleado.fromJson(data);
      }
    } on ApiException catch (e) {
      if (e.statusCode == 404) return null;
      rethrow;
    }
    return null;
  }

  Future<CuentaBancariaEmpleado> guardarCuentaBancaria({
    required String banco,
    required String tipoCuenta,
    required String titular,
    required String documentoIdentidad,
    required String canal,
    String? numeroCuenta,
    String? telefonoPagoMovil,
  }) async {
    final data = await _api.put('/perfil/cuenta-bancaria', {
      'banco': banco,
      'tipo_cuenta': tipoCuenta,
      'titular': titular,
      'documento_identidad': documentoIdentidad,
      'canal': canal,
      if (numeroCuenta != null) 'numero_cuenta': numeroCuenta,
      if (telefonoPagoMovil != null) 'telefono_pago_movil': telefonoPagoMovil,
    });
    return CuentaBancariaEmpleado.fromJson(data as Map<String, dynamic>);
  }
}
