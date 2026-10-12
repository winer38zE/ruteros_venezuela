import 'api_client.dart';

/// Opción de motivo o de estado que devuelve el catálogo del backend.
class OpcionCartera {
  final String codigo;
  final String etiqueta;

  const OpcionCartera({required this.codigo, required this.etiqueta});

  factory OpcionCartera.fromJson(Map<String, dynamic> j) => OpcionCartera(
        codigo: j['codigo'] as String,
        etiqueta: j['etiqueta'] as String,
      );
}

class CatalogoCartera {
  final int diasAtrasoMinimo;
  final List<OpcionCartera> motivos;
  final List<OpcionCartera> estados;

  const CatalogoCartera({
    required this.diasAtrasoMinimo,
    required this.motivos,
    required this.estados,
  });

  factory CatalogoCartera.fromJson(Map<String, dynamic> j) => CatalogoCartera(
        diasAtrasoMinimo: j['dias_atraso_minimo'] as int? ?? 21,
        motivos: (j['motivos'] as List? ?? [])
            .map((e) => OpcionCartera.fromJson(e as Map<String, dynamic>))
            .toList(),
        estados: (j['estados'] as List? ?? [])
            .map((e) => OpcionCartera.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  /// Mismos códigos que valida FastAPI, por si el catálogo no carga.
  factory CatalogoCartera.local() => const CatalogoCartera(
        diasAtrasoMinimo: 21,
        motivos: [
          OpcionCartera(codigo: 'desempleado_temporal', etiqueta: 'Desempleado temporal'),
          OpcionCartera(codigo: 'problema_familiar', etiqueta: 'Problema familiar'),
          OpcionCartera(codigo: 'negativa_pago', etiqueta: 'Negativa de pago / Moroso real'),
          OpcionCartera(codigo: 'alquiler_pendiente', etiqueta: 'Alquiler pendiente'),
          OpcionCartera(codigo: 'otro', etiqueta: 'Otro'),
        ],
        estados: [
          OpcionCartera(codigo: 'en_observacion', etiqueta: 'En observación'),
          OpcionCartera(codigo: 'acuerdo_pago', etiqueta: 'Acuerdo de pago'),
          OpcionCartera(codigo: 'cobro_juridico', etiqueta: 'Cobro jurídico/estricto'),
        ],
      );
}

class CreditoCritico {
  final String ventaId;
  final double saldoPendienteUsd;
  final int diasAtraso;
  final String fechaReferencia;
  final String frecuenciaPago;

  const CreditoCritico({
    required this.ventaId,
    required this.saldoPendienteUsd,
    required this.diasAtraso,
    required this.fechaReferencia,
    required this.frecuenciaPago,
  });

  factory CreditoCritico.fromJson(Map<String, dynamic> j) => CreditoCritico(
        ventaId: j['venta_id'].toString(),
        saldoPendienteUsd: (j['saldo_pendiente_usd'] as num?)?.toDouble() ?? 0,
        diasAtraso: j['dias_atraso'] as int? ?? 0,
        fechaReferencia: j['fecha_referencia']?.toString() ?? '',
        frecuenciaPago: j['frecuencia_pago']?.toString() ?? 'contado',
      );
}

class ClienteCritico {
  final String clienteId;
  final String clienteNombre;
  final String? clienteTelefono;
  final String? clienteDireccion;
  final int diasAtraso;
  final double saldoPendienteUsd;
  final List<CreditoCritico> creditos;
  final String? motivo;
  final String? motivoEtiqueta;
  final String? estadoConsideracion;
  final String? estadoEtiqueta;
  final String? ultimaObservacion;
  final String? ultimaNotaFecha;
  final String grupoMotivo;
  final bool enPlazoDeGracia;
  final bool alertaEstricta;
  final AcuerdoPago? acuerdo;

  const ClienteCritico({
    required this.clienteId,
    required this.clienteNombre,
    this.clienteTelefono,
    this.clienteDireccion,
    required this.diasAtraso,
    required this.saldoPendienteUsd,
    required this.creditos,
    this.motivo,
    this.motivoEtiqueta,
    this.estadoConsideracion,
    this.estadoEtiqueta,
    this.ultimaObservacion,
    this.ultimaNotaFecha,
    this.grupoMotivo = 'sin_motivo',
    this.enPlazoDeGracia = false,
    this.alertaEstricta = true,
    this.acuerdo,
  });

  factory ClienteCritico.fromJson(Map<String, dynamic> j) => ClienteCritico(
        clienteId: j['cliente_id'].toString(),
        clienteNombre: j['cliente_nombre']?.toString() ?? '—',
        clienteTelefono: j['cliente_telefono']?.toString(),
        clienteDireccion: j['cliente_direccion']?.toString(),
        diasAtraso: j['dias_atraso'] as int? ?? 0,
        saldoPendienteUsd: (j['saldo_pendiente_usd'] as num?)?.toDouble() ?? 0,
        creditos: (j['creditos'] as List? ?? [])
            .map((e) => CreditoCritico.fromJson(e as Map<String, dynamic>))
            .toList(),
        motivo: j['motivo']?.toString(),
        motivoEtiqueta: j['motivo_etiqueta']?.toString(),
        estadoConsideracion: j['estado_consideracion']?.toString(),
        estadoEtiqueta: j['estado_etiqueta']?.toString(),
        ultimaObservacion: j['ultima_observacion']?.toString(),
        ultimaNotaFecha: j['ultima_nota_fecha']?.toString(),
        grupoMotivo: j['grupo_motivo']?.toString() ?? 'sin_motivo',
        enPlazoDeGracia: j['en_plazo_de_gracia'] == true,
        alertaEstricta: j['alerta_estricta'] != false,
        acuerdo: j['acuerdo'] is Map<String, dynamic>
            ? AcuerdoPago.fromJson(j['acuerdo'] as Map<String, dynamic>)
            : null,
      );

  bool get cabeConsideracion =>
      enPlazoDeGracia ||
      estadoConsideracion == 'en_observacion' ||
      estadoConsideracion == 'acuerdo_pago';

  bool get esCasoCritico =>
      !enPlazoDeGracia &&
      (estadoConsideracion == 'cobro_juridico' || motivo == 'negativa_pago');
}

class ConteoMotivo {
  final String codigo;
  final String etiqueta;
  final int total;

  const ConteoMotivo({
    required this.codigo,
    required this.etiqueta,
    required this.total,
  });

  factory ConteoMotivo.fromJson(Map<String, dynamic> j) => ConteoMotivo(
        codigo: j['codigo']?.toString() ?? '',
        etiqueta: j['etiqueta']?.toString() ?? '',
        total: j['total'] as int? ?? 0,
      );
}

class CarteraCriticaPagina {
  final String motivoMora;
  final List<ConteoMotivo> conteos;
  final List<ClienteCritico> clientes;

  const CarteraCriticaPagina({
    required this.motivoMora,
    required this.conteos,
    required this.clientes,
  });

  factory CarteraCriticaPagina.fromJson(Map<String, dynamic> j) => CarteraCriticaPagina(
        motivoMora: j['motivo_mora']?.toString() ?? 'todos',
        conteos: (j['conteos'] as List? ?? [])
            .map((e) => ConteoMotivo.fromJson(e as Map<String, dynamic>))
            .toList(),
        clientes: (j['clientes'] as List? ?? [])
            .map((e) => ClienteCritico.fromJson(e as Map<String, dynamic>))
            .toList(),
      );

  int totalDe(String codigo) {
    for (final conteo in conteos) {
      if (conteo.codigo == codigo) return conteo.total;
    }
    return 0;
  }
}

class AcuerdoPago {
  final String id;
  final String clienteId;
  final double montoAcordadoUsd;
  final String fechaLimite;
  final int cuotasPactadas;
  final String estado;
  final String estadoEtiqueta;
  final String notaConsideracion;
  final bool enPlazoDeGracia;
  final bool alertaEstricta;

  const AcuerdoPago({
    required this.id,
    this.clienteId = '',
    required this.montoAcordadoUsd,
    required this.fechaLimite,
    required this.cuotasPactadas,
    required this.estado,
    required this.estadoEtiqueta,
    required this.notaConsideracion,
    this.enPlazoDeGracia = false,
    this.alertaEstricta = true,
  });

  factory AcuerdoPago.fromJson(Map<String, dynamic> j) => AcuerdoPago(
        id: j['id']?.toString() ?? '',
        clienteId: j['cliente_id']?.toString() ?? '',
        montoAcordadoUsd: (j['monto_acordado_usd'] as num?)?.toDouble() ?? 0,
        fechaLimite: j['fecha_limite']?.toString() ?? '',
        cuotasPactadas: j['cuotas_pactadas'] as int? ?? 1,
        estado: j['estado']?.toString() ?? '',
        estadoEtiqueta: j['estado_etiqueta']?.toString() ?? '',
        notaConsideracion: j['nota_consideracion']?.toString() ?? '',
        enPlazoDeGracia: j['en_plazo_de_gracia'] == true,
        alertaEstricta: j['alerta_estricta'] != false,
      );
}

class NotaSeguimiento {
  final String id;
  final String clienteId;
  final String usuarioNombre;
  final String fecha;
  final String motivo;
  final String motivoEtiqueta;
  final String estadoConsideracion;
  final String estadoEtiqueta;
  final String observacion;

  const NotaSeguimiento({
    required this.id,
    required this.clienteId,
    required this.usuarioNombre,
    required this.fecha,
    required this.motivo,
    required this.motivoEtiqueta,
    required this.estadoConsideracion,
    required this.estadoEtiqueta,
    required this.observacion,
  });

  factory NotaSeguimiento.fromJson(Map<String, dynamic> j) => NotaSeguimiento(
        id: j['id'].toString(),
        clienteId: j['cliente_id'].toString(),
        usuarioNombre: j['usuario_nombre']?.toString() ?? '—',
        fecha: j['fecha']?.toString() ?? '',
        motivo: j['motivo']?.toString() ?? '',
        motivoEtiqueta: j['motivo_etiqueta']?.toString() ?? '',
        estadoConsideracion: j['estado_consideracion']?.toString() ?? '',
        estadoEtiqueta: j['estado_etiqueta']?.toString() ?? '',
        observacion: j['observacion']?.toString() ?? '',
      );
}

class CarteraCriticaService {
  CarteraCriticaService(this._api);
  final ApiClient _api;

  Future<CatalogoCartera> catalogo() async {
    final data = await _api.get('/cartera-critica/catalogo');
    return CatalogoCartera.fromJson(data as Map<String, dynamic>);
  }

  /// [motivoMora] acepta todos, desempleo, alquiler y moroso_real.
  /// Sin argumento trae la carpeta completa y el conteo de cada motivo.
  Future<CarteraCriticaPagina> listar({String? motivoMora}) async {
    final data = await _api.get(
      '/cartera-critica/',
      query: motivoMora == null || motivoMora.isEmpty
          ? null
          : {'motivo_mora': motivoMora},
    );
    if (data is List) {
      final clientes = data
          .map((e) => ClienteCritico.fromJson(e as Map<String, dynamic>))
          .toList();
      return CarteraCriticaPagina(
        motivoMora: motivoMora ?? 'todos',
        conteos: const [],
        clientes: clientes,
      );
    }
    return CarteraCriticaPagina.fromJson(data as Map<String, dynamic>);
  }

  Future<AcuerdoPago> otorgarAcuerdo({
    required String clienteId,
    required double montoAcordadoUsd,
    required DateTime fechaLimite,
    required int cuotasPactadas,
    required String notaConsideracion,
  }) async {
    final mes = fechaLimite.month.toString().padLeft(2, '0');
    final dia = fechaLimite.day.toString().padLeft(2, '0');
    final data = await _api.post('/cartera/acuerdo-pago', {
      'cliente_id': clienteId,
      'monto_acordado_usd': montoAcordadoUsd,
      'fecha_limite': '${fechaLimite.year}-$mes-$dia',
      'cuotas_pactadas': cuotasPactadas,
      'nota_consideracion': notaConsideracion.trim(),
    });
    return AcuerdoPago.fromJson(data as Map<String, dynamic>);
  }

  Future<List<NotaSeguimiento>> notas(String clienteId) async {
    final data = await _api.get('/cartera-critica/$clienteId/notas') as List;
    return data
        .map((e) => NotaSeguimiento.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<NotaSeguimiento> guardarNota({
    required String clienteId,
    required String motivo,
    required String estadoConsideracion,
    required String observacion,
  }) async {
    final data = await _api.post('/cartera-critica/$clienteId/notas', {
      'motivo': motivo,
      'estado_consideracion': estadoConsideracion,
      'observacion': observacion.trim(),
    });
    return NotaSeguimiento.fromJson(data as Map<String, dynamic>);
  }
}
