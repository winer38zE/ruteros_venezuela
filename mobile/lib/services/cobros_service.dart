import '../services/api_client.dart';
import 'ventas_service.dart';

class FilaCobranza {
  final String id;
  final String clienteId;
  final String clienteNombre;
  final String? clienteTelefono;
  final String? clienteEmail;
  final String? clienteDireccion;
  final String? clienteDireccionLaboral;
  final double? latitudResidencia;
  final double? longitudResidencia;
  final double? latitudTrabajo;
  final double? longitudTrabajo;
  final String productosResumen;
  final double? costoTotalUsd;
  final double? margenUsd;
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
  final List<CuotaAmortizacion> cuotas;

  FilaCobranza({
    required this.id,
    required this.clienteId,
    required this.clienteNombre,
    this.clienteTelefono,
    this.clienteEmail,
    this.clienteDireccion,
    this.clienteDireccionLaboral,
    this.latitudResidencia,
    this.longitudResidencia,
    this.latitudTrabajo,
    this.longitudTrabajo,
    required this.productosResumen,
    this.costoTotalUsd,
    this.margenUsd,
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
    this.cuotas = const [],
  });

  factory FilaCobranza.fromJson(Map<String, dynamic> j) => FilaCobranza(
        id: j['id'],
        clienteId: j['cliente_id'],
        clienteNombre: j['cliente_nombre'] ?? '—',
        clienteTelefono: j['cliente_telefono'],
        clienteEmail: j['cliente_email'],
        clienteDireccion: j['cliente_direccion'],
        clienteDireccionLaboral: j['cliente_direccion_laboral'],
        latitudResidencia: (j['latitud_residencia'] as num?)?.toDouble(),
        longitudResidencia: (j['longitud_residencia'] as num?)?.toDouble(),
        latitudTrabajo: (j['latitud_trabajo'] as num?)?.toDouble(),
        longitudTrabajo: (j['longitud_trabajo'] as num?)?.toDouble(),
        productosResumen: j['productos_resumen'] ?? '—',
        costoTotalUsd: (j['costo_total_usd'] as num?)?.toDouble(),
        margenUsd: (j['margen_usd'] as num?)?.toDouble(),
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
        cuotas: (j['cuotas'] as List? ?? [])
            .map((e) => CuotaAmortizacion.fromJson(e))
            .toList(),
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
  final String frecuenciaPago;
  final String tipoCredito;
  final String? fecha;

  VentaPendiente({
    required this.id,
    required this.clienteId,
    required this.clienteNombre,
    required this.totalUsd,
    required this.cobradoUsd,
    required this.saldoPendienteUsd,
    required this.estado,
    this.frecuenciaPago = 'contado',
    this.tipoCredito = 'Contado',
    this.fecha,
  });

  factory VentaPendiente.fromJson(Map<String, dynamic> j) => VentaPendiente(
        id: j['id'].toString(),
        clienteId: j['cliente_id'].toString(),
        clienteNombre: j['cliente_nombre'] ?? '—',
        totalUsd: (j['total_usd'] as num?)?.toDouble() ?? 0,
        cobradoUsd: (j['cobrado_usd'] as num?)?.toDouble() ?? 0,
        saldoPendienteUsd: (j['saldo_pendiente_usd'] as num?)?.toDouble() ?? 0,
        estado: j['estado']?.toString() ?? 'pendiente',
        frecuenciaPago: j['frecuencia_pago'] ?? 'contado',
        tipoCredito: j['tipo_credito'] ?? 'Contado',
        fecha: j['fecha']?.toString(),
      );
}

class Cobro {
  final String id;
  final String ventaId;
  final double montoUsd;
  final String monedaPago;
  final String fecha;
  final String? estadoVenta;

  Cobro({
    required this.id,
    required this.ventaId,
    required this.montoUsd,
    required this.monedaPago,
    required this.fecha,
    this.estadoVenta,
  });

  factory Cobro.fromJson(Map<String, dynamic> j) => Cobro(
        id: j['id']?.toString() ?? '',
        ventaId: j['venta_id']?.toString() ?? '',
        montoUsd: (j['monto_usd'] as num?)?.toDouble() ?? 0,
        monedaPago: j['moneda_pago']?.toString() ?? '',
        fecha: j['fecha']?.toString() ?? '',
        estadoVenta: j['estado_venta']?.toString(),
      );
}

class CobradorOpcion {
  final String id;
  final String nombre;
  final String rol;

  CobradorOpcion({required this.id, required this.nombre, required this.rol});

  factory CobradorOpcion.fromJson(Map<String, dynamic> j) => CobradorOpcion(
        id: j['id'].toString(),
        nombre: j['nombre']?.toString() ?? 'Cobrador',
        rol: j['rol']?.toString() ?? '',
      );
}

class PuntoCobro {
  final String cobroId;
  final String fecha;
  final String clienteNombre;
  final double montoUsd;
  final String metodo;
  final double? latitud;
  final double? longitud;
  final bool sinUbicacion;

  PuntoCobro({
    required this.cobroId,
    required this.fecha,
    required this.clienteNombre,
    required this.montoUsd,
    required this.metodo,
    this.latitud,
    this.longitud,
    this.sinUbicacion = true,
  });

  factory PuntoCobro.fromJson(Map<String, dynamic> j) => PuntoCobro(
        cobroId: j['cobro_id'].toString(),
        fecha: j['fecha']?.toString() ?? '',
        clienteNombre: j['cliente_nombre']?.toString() ?? 'Cliente',
        montoUsd: (j['monto_usd'] as num?)?.toDouble() ?? 0,
        metodo: j['metodo']?.toString() ?? '',
        latitud: (j['latitud'] as num?)?.toDouble(),
        longitud: (j['longitud'] as num?)?.toDouble(),
        sinUbicacion: j['sin_ubicacion'] != false,
      );
}

class SeguimientoRuta {
  final String cobradorId;
  final String cobradorNombre;
  final String fecha;
  final List<PuntoCobro> puntos;

  SeguimientoRuta({
    required this.cobradorId,
    required this.cobradorNombre,
    required this.fecha,
    required this.puntos,
  });

  factory SeguimientoRuta.fromJson(Map<String, dynamic> j) => SeguimientoRuta(
        cobradorId: j['cobrador_id'].toString(),
        cobradorNombre: j['cobrador_nombre']?.toString() ?? '',
        fecha: j['fecha']?.toString() ?? '',
        puntos: (j['puntos'] as List? ?? [])
            .map((e) => PuntoCobro.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class CobrosService {
  CobrosService(this._api);
  final ApiClient _api;

  static const monedasAbono = [
    ('usd', 'Dólares'),
    ('ves', 'Bolívares'),
    ('cop', 'Pesos'),
  ];

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
    bool esTransferencia = false,
    String? canal,
    String? referenciaPago,
    String? comprobanteBase64,
    String? cuentaBancariaId,
    double? latitud,
    double? longitud,
    double? precisionMetros,
  }) async {
    final body = {
      'venta_id': ventaId,
      'monto_usd': montoUsd,
      'moneda_pago': monedaPago,
      'tasa_usd_aplicada': tasaUsd,
      'tasa_eur_aplicada': tasaEur,
      'es_transferencia': esTransferencia,
      if (canal != null) 'canal': canal,
      if (cobroId != null) 'id': cobroId,
      if (latitud != null && longitud != null) 'latitud': latitud,
      if (latitud != null && longitud != null) 'longitud': longitud,
      if (latitud != null && longitud != null && precisionMetros != null)
        'precision_metros': precisionMetros,
      if (referenciaPago != null && referenciaPago.trim().isNotEmpty)
        'referencia_pago': referenciaPago.trim(),
      if (comprobanteBase64 != null && comprobanteBase64.isNotEmpty)
        'comprobante_base64': comprobanteBase64,
      if (cuentaBancariaId != null) 'cuenta_bancaria_id': cuentaBancariaId,
    };
    final data = await _api.post('/cobros/', body);
    return Cobro.fromJson(data);
  }

  Future<String> enviarRecibo(String cobroId) async {
    final data = await _api.post('/cobros/$cobroId/enviar-recibo', {});
    return data['mensaje'] as String? ?? 'Recibo enviado';
  }

  Future<List<CobradorOpcion>> cobradoresSeguimiento() async {
    final data = await _api.get('/cobros/seguimiento/cobradores') as List;
    return data.map((e) => CobradorOpcion.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<SeguimientoRuta> seguimiento({required String cobradorId, required String fecha}) async {
    final data = await _api.get(
      '/cobros/seguimiento',
      query: {'cobrador_id': cobradorId, 'fecha': fecha},
    ) as Map<String, dynamic>;
    return SeguimientoRuta.fromJson(data);
  }

  Future<String> enviarComprobanteWhatsapp(String cobroId, {String? metodo}) async {
    final data = await _api.post(
      '/cobros/$cobroId/comprobante/whatsapp',
      {if (metodo != null) 'metodo': metodo},
      timeout: const Duration(seconds: 60),
    );
    return data['mensaje'] as String? ?? 'Comprobante enviado por WhatsApp';
  }
}
