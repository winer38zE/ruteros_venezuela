import '../services/api_client.dart';

class CuotaAmortizacion {
  final String id;
  final int numeroCuota;
  final String fechaVencimiento;
  final double montoUsd;
  final double montoPagadoUsd;
  final String estado;
  final String etiquetaPeriodo;
  final String estadoDisplay;
  final double montoPendienteUsd;

  CuotaAmortizacion({
    required this.id,
    required this.numeroCuota,
    required this.fechaVencimiento,
    required this.montoUsd,
    required this.montoPagadoUsd,
    required this.estado,
    this.etiquetaPeriodo = '',
    this.estadoDisplay = 'Pendiente',
    this.montoPendienteUsd = 0,
  });

  factory CuotaAmortizacion.fromJson(Map<String, dynamic> j) => CuotaAmortizacion(
        id: j['id'],
        numeroCuota: j['numero_cuota'],
        fechaVencimiento: j['fecha_vencimiento'],
        montoUsd: (j['monto_usd'] as num).toDouble(),
        montoPagadoUsd: (j['monto_pagado_usd'] as num).toDouble(),
        estado: j['estado'],
        etiquetaPeriodo: j['etiqueta_periodo'] ?? 'Cuota ${j['numero_cuota']}',
        estadoDisplay: j['estado_display'] ?? j['estado'] ?? 'Pendiente',
        montoPendienteUsd: (j['monto_pendiente_usd'] as num?)?.toDouble() ??
            ((j['monto_usd'] as num).toDouble() - (j['monto_pagado_usd'] as num).toDouble()),
      );
}

class DetalleVenta {
  final String id;
  final String productoId;
  final int cantidad;
  final double precioUnitarioUsd;
  final String? productoNombre;

  DetalleVenta({
    required this.id,
    required this.productoId,
    required this.cantidad,
    required this.precioUnitarioUsd,
    this.productoNombre,
  });

  factory DetalleVenta.fromJson(Map<String, dynamic> j) => DetalleVenta(
        id: j['id'].toString(),
        productoId: j['producto_id'].toString(),
        cantidad: (j['cantidad'] as num?)?.toInt() ?? 0,
        precioUnitarioUsd: (j['precio_unitario_usd'] as num?)?.toDouble() ?? 0,
        productoNombre: j['producto_nombre']?.toString(),
      );

  double get subtotal => precioUnitarioUsd * cantidad;
}

class Venta {
  final String id;
  final String clienteId;
  final String vendedorId;
  final double totalUsd;
  final String estado;
  final String frecuenciaPago;
  final String metodoPago;
  final String? referenciaPago;
  final bool tieneComprobante;
  final List<DetalleVenta> detalles;
  final List<CuotaAmortizacion> cuotas;
  final String? fecha;
  final String clienteNombre;
  final String clienteApellido;
  final String? clienteTelefono;
  final String? clienteEmail;
  final double saldoPendienteUsd;
  final String productosResumen;

  Venta({
    required this.id,
    required this.clienteId,
    required this.vendedorId,
    required this.totalUsd,
    required this.estado,
    required this.frecuenciaPago,
    this.metodoPago = 'efectivo',
    this.referenciaPago,
    this.tieneComprobante = false,
    required this.detalles,
    required this.cuotas,
    this.fecha,
    this.clienteNombre = '',
    this.clienteApellido = '',
    this.clienteTelefono,
    this.clienteEmail,
    this.saldoPendienteUsd = 0,
    this.productosResumen = '',
  });

  String get clienteCompleto {
    final partes = [clienteNombre, clienteApellido].where((p) => p.trim().isNotEmpty);
    final nombre = partes.join(' ');
    return nombre.isEmpty ? 'Cliente' : nombre;
  }

  factory Venta.fromJson(Map<String, dynamic> j) => Venta(
        id: j['id'].toString(),
        clienteId: j['cliente_id']?.toString() ?? '',
        vendedorId: j['vendedor_id']?.toString() ?? '',
        totalUsd: (j['total_usd'] as num?)?.toDouble() ?? 0,
        estado: j['estado']?.toString() ?? '',
        frecuenciaPago: j['frecuencia_pago'] ?? 'contado',
        metodoPago: j['metodo_pago'] ?? 'efectivo',
        referenciaPago: j['referencia_pago'],
        tieneComprobante: j['tiene_comprobante'] == true,
        detalles: (j['detalles'] as List? ?? [])
            .map((e) => DetalleVenta.fromJson(e as Map<String, dynamic>))
            .toList(),
        cuotas: (j['cuotas'] as List? ?? [])
            .map((e) => CuotaAmortizacion.fromJson(e as Map<String, dynamic>))
            .toList(),
        fecha: j['fecha']?.toString(),
        clienteNombre: j['cliente_nombre']?.toString() ?? '',
        clienteApellido: j['cliente_apellido']?.toString() ?? '',
        clienteTelefono: j['cliente_telefono']?.toString(),
        clienteEmail: j['cliente_email']?.toString(),
        saldoPendienteUsd: (j['saldo_pendiente_usd'] as num?)?.toDouble() ?? 0,
        productosResumen: j['productos_resumen']?.toString() ?? '',
      );
}

class ItemCarrito {
  final String productoId;
  final String nombre;
  final int cantidad;
  final double precioUnitario;
  final String tipoPrecio;

  ItemCarrito({
    required this.productoId,
    required this.nombre,
    required this.cantidad,
    required this.precioUnitario,
    required this.tipoPrecio,
  });

  double get subtotal => precioUnitario * cantidad;

  Map<String, dynamic> toDetalleJson() => {
        'producto_id': productoId,
        'cantidad': cantidad,
        'tipo_precio': tipoPrecio,
      };
}

class VentasService {
  VentasService(this._api);
  final ApiClient _api;

  Future<List<Venta>> misVentas({String? q}) async {
    final data = await _api.get(
      '/ventas/mis-ventas',
      query: (q == null || q.trim().isEmpty) ? null : {'q': q.trim()},
    ) as List;
    return data.map((e) => Venta.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<CuotaAmortizacion>> amortizacion(String ventaId) async {
    final data = await _api.get('/ventas/$ventaId/amortizacion') as List;
    return data.map((e) => CuotaAmortizacion.fromJson(e)).toList();
  }

  Future<Venta> aprobarBorrador(String ventaId) async {
    final data = await _api.post('/ventas/$ventaId/aprobar', {});
    return Venta.fromJson(data);
  }

  Future<Venta> crearVenta({
    required String clienteId,
    required double totalUsd,
    required double tasaUsd,
    required double tasaEur,
    required String frecuenciaPago,
    required List<ItemCarrito> items,
    String? almacenId,
    String? ventaId,
    int? numeroCuotas,
    String tipoTasaUsd = 'bcv',
    bool esBorrador = false,
    double? latitudResidencia,
    double? longitudResidencia,
    double? latitudTrabajo,
    double? longitudTrabajo,
    String metodoPago = 'efectivo',
    String? referenciaPago,
    String? comprobanteBase64,
    String? cuentaBancariaId,
  }) async {
    final body = {
      'cliente_id': clienteId,
      'total_usd': totalUsd,
      'tasa_usd_aplicada': tasaUsd,
      'tasa_eur_aplicada': tasaEur,
      'frecuencia_pago': frecuenciaPago,
      'tipo_tasa_usd': tipoTasaUsd,
      'es_borrador': esBorrador,
      'metodo_pago': metodoPago,
      if (referenciaPago != null && referenciaPago.trim().isNotEmpty)
        'referencia_pago': referenciaPago.trim(),
      if (comprobanteBase64 != null && comprobanteBase64.isNotEmpty)
        'comprobante_base64': comprobanteBase64,
      if (cuentaBancariaId != null) 'cuenta_bancaria_id': cuentaBancariaId,
      if (numeroCuotas != null) 'numero_cuotas': numeroCuotas,
      if (almacenId != null) 'almacen_id': almacenId,
      if (ventaId != null) 'id': ventaId,
      if (latitudResidencia != null) 'latitud_residencia': latitudResidencia,
      if (longitudResidencia != null) 'longitud_residencia': longitudResidencia,
      if (latitudTrabajo != null) 'latitud_trabajo': latitudTrabajo,
      if (longitudTrabajo != null) 'longitud_trabajo': longitudTrabajo,
      'detalles': items.map((i) => i.toDetalleJson()).toList(),
    };
    final data = await _api.post('/ventas/', body);
    return Venta.fromJson(data);
  }

  Future<Venta> verificarPago(String ventaId) async {
    final data = await _api.post('/ventas/$ventaId/verificar', {});
    return Venta.fromJson(data);
  }

  Future<String> enviarRecibo(String ventaId) async {
    final data = await _api.post('/ventas/$ventaId/enviar-recibo', {});
    return data['mensaje'] as String? ?? 'Comprobante enviado';
  }

  Future<String> enviarReciboWhatsapp(String ventaId) async {
    final data = await _api.post('/ventas/$ventaId/recibo/whatsapp', {});
    return data['mensaje'] as String? ?? 'Recibo enviado por WhatsApp';
  }

  Future<String> enviarComprobanteWhatsapp(String ventaId) async {
    final data = await _api.post(
      '/ventas/$ventaId/comprobante/whatsapp',
      {},
      timeout: const Duration(seconds: 60),
    );
    return data['mensaje'] as String? ?? 'Comprobante enviado por WhatsApp';
  }
}
