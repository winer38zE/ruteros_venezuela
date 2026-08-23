import '../services/api_client.dart';

class ClienteRuta {
  final String id;
  final String? vendedorId;
  final String nombre;
  final String? direccion;
  final String diaVisita;
  final int ordenSecuencial;
  final double? latitud;
  final double? longitud;
  final String tipoVisitaRuta;
  final String? telefono;

  /// Estado local de visita (no persiste en backend).
  bool visitado;

  ClienteRuta({
    required this.id,
    this.vendedorId,
    required this.nombre,
    this.direccion,
    required this.diaVisita,
    required this.ordenSecuencial,
    this.latitud,
    this.longitud,
    required this.tipoVisitaRuta,
    this.telefono,
    this.visitado = false,
  });

  bool get esFrecuente => tipoVisitaRuta == 'frecuente';
  bool get esNuevo => tipoVisitaRuta == 'nuevo';
  bool get tieneGps =>
      latitud != null && longitud != null && latitud!.abs() > 0.0001 && longitud!.abs() > 0.0001;

  ClienteRuta copyWith({bool? visitado}) => ClienteRuta(
        id: id,
        vendedorId: vendedorId,
        nombre: nombre,
        direccion: direccion,
        diaVisita: diaVisita,
        ordenSecuencial: ordenSecuencial,
        latitud: latitud,
        longitud: longitud,
        tipoVisitaRuta: tipoVisitaRuta,
        telefono: telefono,
        visitado: visitado ?? this.visitado,
      );

  factory ClienteRuta.fromJson(Map<String, dynamic> j) => ClienteRuta(
        id: j['id'].toString(),
        vendedorId: j['vendedor_id']?.toString(),
        nombre: j['nombre'] ?? '—',
        direccion: j['direccion'],
        diaVisita: j['dia_visita'] ?? 'LUNES',
        ordenSecuencial: (j['orden_secuencial'] as num?)?.toInt() ?? 0,
        latitud: (j['latitud'] as num?)?.toDouble(),
        longitud: (j['longitud'] as num?)?.toDouble(),
        tipoVisitaRuta: j['tipo_visita_ruta'] ?? 'frecuente',
        telefono: j['telefono'],
      );
}

class RutasDiaResult {
  final String vendedorId;
  final String dia;
  final int totalClientes;
  final List<ClienteRuta> clientes;

  RutasDiaResult({
    required this.vendedorId,
    required this.dia,
    required this.totalClientes,
    required this.clientes,
  });

  factory RutasDiaResult.fromJson(Map<String, dynamic> j) => RutasDiaResult(
        vendedorId: j['vendedor_id'].toString(),
        dia: j['dia'] ?? 'LUNES',
        totalClientes: (j['total_clientes'] as num?)?.toInt() ?? 0,
        clientes: (j['clientes'] as List? ?? [])
            .map((e) => ClienteRuta.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class RutasService {
  RutasService(this._api);
  final ApiClient _api;

  static const _dias = [
    'LUNES',
    'MARTES',
    'MIERCOLES',
    'JUEVES',
    'VIERNES',
    'SABADO',
    'DOMINGO',
  ];

  static String diaActual() {
    final now = DateTime.now();
    return _dias[now.weekday - 1];
  }

  Future<RutasDiaResult> rutaDelDia({
    String? vendedorId,
    String? dia,
  }) async {
    final params = <String, String>{};
    if (vendedorId != null) params['vendedor_id'] = vendedorId;
    if (dia != null) params['dia'] = dia;

    final query = params.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&');
    final path = query.isEmpty ? '/rutas/dia' : '/rutas/dia?$query';

    final data = await _api.get(path) as Map<String, dynamic>;
    return RutasDiaResult.fromJson(data);
  }
}
