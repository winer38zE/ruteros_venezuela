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

class CuentaBancaria {
  final String id;
  final String banco;
  final String tipoCuenta;
  final String numeroCuenta;
  final String titular;
  final String documento;
  final String canal;
  final String telefono;

  const CuentaBancaria({
    required this.id,
    required this.banco,
    required this.tipoCuenta,
    required this.numeroCuenta,
    required this.titular,
    required this.documento,
    this.canal = 'transferencia',
    this.telefono = '',
  });

  factory CuentaBancaria.fromJson(Map<String, dynamic> j) => CuentaBancaria(
        id: j['id'].toString(),
        banco: j['banco'] ?? '',
        tipoCuenta: j['tipo_cuenta'] ?? '',
        numeroCuenta: j['numero_cuenta'] ?? '',
        titular: j['titular'] ?? '',
        documento: j['documento'] ?? '',
        canal: j['canal'] ?? 'transferencia',
        telefono: j['telefono'] ?? '',
      );

  bool get esPagoMovil => canal == 'pago_movil';

  String get datoCopiable => esPagoMovil
      ? (telefono.trim().isNotEmpty ? telefono : numeroCuenta)
      : numeroCuenta;

  String get etiqueta => esPagoMovil ? '$banco · Pago móvil' : '$banco · $tipoCuenta';
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

  Future<List<CuentaBancaria>> cuentasBancarias() async {
    final data = await _api.get('/empresas/cuentas-bancarias') as List;
    return data.map((e) => CuentaBancaria.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<CuentaBancaria> crearCuenta({
    required String canal,
    required String banco,
    required String titular,
    required String documento,
    String? tipoCuenta,
    String? numeroCuenta,
    String? telefono,
  }) async {
    final data = await _api.post('/empresas/cuentas-bancarias', {
      'canal': canal,
      'banco': banco,
      'titular': titular,
      'documento': documento,
      if (tipoCuenta != null) 'tipo_cuenta': tipoCuenta,
      if (numeroCuenta != null) 'numero_cuenta': numeroCuenta,
      if (telefono != null) 'telefono': telefono,
    });
    return CuentaBancaria.fromJson(data as Map<String, dynamic>);
  }

  Future<void> archivarCuenta(String id) async {
    await _api.post('/empresas/cuentas-bancarias/$id/archivar', {});
  }
}
