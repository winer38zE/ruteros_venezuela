import '../services/api_client.dart';

class ClienteDetalle {
  final String id;
  final String nombre;
  final String identificacion;
  final String? telefono;
  final String? telefonoSecundario;
  final String? direccion;
  final String? puntoReferencia;
  final String? empresaTrabajo;
  final String? direccionLaboral;
  final String? refFamiliarNombre;
  final String? refFamiliarParentesco;
  final String? refFamiliarTelefono;
  final String? email;
  final int scoreCredito;
  final String nivelRiesgo;
  final String estadoCredito;
  final String tipoCliente;

  ClienteDetalle({
    required this.id,
    required this.nombre,
    required this.identificacion,
    this.telefono,
    this.telefonoSecundario,
    this.direccion,
    this.puntoReferencia,
    this.empresaTrabajo,
    this.direccionLaboral,
    this.refFamiliarNombre,
    this.refFamiliarParentesco,
    this.refFamiliarTelefono,
    this.email,
    required this.scoreCredito,
    required this.nivelRiesgo,
    required this.estadoCredito,
    required this.tipoCliente,
  });

  factory ClienteDetalle.fromJson(Map<String, dynamic> j) => ClienteDetalle(
        id: j['id'],
        nombre: j['nombre'],
        identificacion: j['identificacion'] ?? '',
        telefono: j['telefono'],
        telefonoSecundario: j['telefono_secundario'],
        direccion: j['direccion'],
        puntoReferencia: j['punto_referencia'],
        empresaTrabajo: j['empresa_trabajo'],
        direccionLaboral: j['direccion_laboral'],
        refFamiliarNombre: j['ref_familiar_nombre'],
        refFamiliarParentesco: j['ref_familiar_parentesco'],
        refFamiliarTelefono: j['ref_familiar_telefono'],
        email: j['email'],
        scoreCredito: j['score_credito'] ?? 70,
        nivelRiesgo: j['nivel_riesgo'] ?? 'bueno',
        estadoCredito: j['estado_credito'] ?? 'Bueno',
        tipoCliente: j['tipo_cliente'] ?? 'detal',
      );

  bool get bloqueadoCredito => scoreCredito <= 35;
  bool get creditoExcelente => scoreCredito >= 85;
}

class HistorialBuroItem {
  final String fecha;
  final String tipo;
  final String mensaje;

  HistorialBuroItem({required this.fecha, required this.tipo, required this.mensaje});

  factory HistorialBuroItem.fromJson(Map<String, dynamic> j) => HistorialBuroItem(
        fecha: j['fecha'],
        tipo: j['tipo'],
        mensaje: j['mensaje'],
      );
}

class BuroCreditoResult {
  final String identificacion;
  final bool encontrado;
  final int? scoreGlobal;
  final String? nivelRiesgo;
  final String? estadoCredito;
  final List<HistorialBuroItem> historial;

  BuroCreditoResult({
    required this.identificacion,
    required this.encontrado,
    this.scoreGlobal,
    this.nivelRiesgo,
    this.estadoCredito,
    this.historial = const [],
  });

  factory BuroCreditoResult.fromJson(Map<String, dynamic> j) => BuroCreditoResult(
        identificacion: j['identificacion'],
        encontrado: j['encontrado'] ?? false,
        scoreGlobal: j['score_global'],
        nivelRiesgo: j['nivel_riesgo'],
        estadoCredito: j['estado_credito'],
        historial: (j['historial_cumplimiento'] as List? ?? [])
            .map((e) => HistorialBuroItem.fromJson(e))
            .toList(),
      );
}

class ClienteAutocompletado {
  final String identificacion;
  final bool enRed;
  final String? nombreCompleto;
  final String? telefono;
  final String? telefonoSecundario;
  final String? direccion;
  final String? puntoReferencia;
  final String? empresaTrabajo;
  final String? direccionLaboral;
  final String? refFamiliarNombre;
  final String? refFamiliarParentesco;
  final String? refFamiliarTelefono;
  final String? email;
  final int? scoreGlobal;
  final String? nivelRiesgo;
  final String? estadoCredito;

  ClienteAutocompletado({
    required this.identificacion,
    this.enRed = false,
    this.nombreCompleto,
    this.telefono,
    this.telefonoSecundario,
    this.direccion,
    this.puntoReferencia,
    this.empresaTrabajo,
    this.direccionLaboral,
    this.refFamiliarNombre,
    this.refFamiliarParentesco,
    this.refFamiliarTelefono,
    this.email,
    this.scoreGlobal,
    this.nivelRiesgo,
    this.estadoCredito,
  });

  factory ClienteAutocompletado.fromJson(Map<String, dynamic> j) => ClienteAutocompletado(
        identificacion: j['identificacion'],
        enRed: j['en_red'] ?? false,
        nombreCompleto: j['nombre_completo'],
        telefono: j['telefono'],
        telefonoSecundario: j['telefono_secundario'],
        direccion: j['direccion'],
        puntoReferencia: j['punto_referencia'],
        empresaTrabajo: j['empresa_trabajo'],
        direccionLaboral: j['direccion_laboral'],
        refFamiliarNombre: j['ref_familiar_nombre'],
        refFamiliarParentesco: j['ref_familiar_parentesco'],
        refFamiliarTelefono: j['ref_familiar_telefono'],
        email: j['email'],
        scoreGlobal: j['score_global'],
        nivelRiesgo: j['nivel_riesgo'],
        estadoCredito: j['estado_credito'],
      );
}

class ClientesService {
  ClientesService(this._api);
  final ApiClient _api;

  static const parentescos = [
    'Padre/Madre',
    'Hermano/a',
    'Cónyuge',
    'Tío/a',
    'Amigo/a',
    'Vecino/a',
    'Otro',
  ];

  Future<List<ClienteDetalle>> listar({String? busqueda}) async {
    final data = await _api.get('/clientes/', query: busqueda != null ? {'q': busqueda} : null) as List;
    return data.map((e) => ClienteDetalle.fromJson(e)).toList();
  }

  Future<ClienteDetalle> obtener(String id) async {
    final data = await _api.get('/clientes/$id');
    return ClienteDetalle.fromJson(data);
  }

  Future<ClienteDetalle> crear(Map<String, dynamic> body) async {
    final data = await _api.post('/clientes/', body);
    return ClienteDetalle.fromJson(data);
  }

  Future<ClienteDetalle> actualizar(String id, Map<String, dynamic> body) async {
    final data = await _api.put('/clientes/$id', body);
    return ClienteDetalle.fromJson(data);
  }

  Future<BuroCreditoResult> consultarBuro(String identificacion) async {
    final ident = identificacion.replaceAll(RegExp(r'[^a-zA-Z0-9]'), '').toUpperCase();
    final data = await _api.get('/clientes/buro/$ident');
    return BuroCreditoResult.fromJson(data);
  }

  Future<ClienteAutocompletado> verificarIdentificacion(String identificacion) async {
    final ident = identificacion.replaceAll(RegExp(r'[^a-zA-Z0-9]'), '').toUpperCase();
    final data = await _api.get('/clientes/verificar/$ident');
    return ClienteAutocompletado.fromJson(data);
  }
}
