import '../services/api_client.dart';
import 'rutas_offline_queue.dart';

class ClienteRuta {
  final String id;
  final String? vendedorId;
  final String nombre;
  final String? direccion;
  final String diaVisita;
  final String diaRuta;
  final int ordenSecuencial;
  final int ordenRuta;
  final double? latitud;
  final double? longitud;
  final String tipoVisitaRuta;
  final String? telefono;
  final String estadoVisita;
  final DateTime? marcadoEn;

  ClienteRuta({
    required this.id,
    this.vendedorId,
    required this.nombre,
    this.direccion,
    required this.diaVisita,
    required this.diaRuta,
    required this.ordenSecuencial,
    required this.ordenRuta,
    this.latitud,
    this.longitud,
    required this.tipoVisitaRuta,
    this.telefono,
    this.estadoVisita = 'pendiente',
    this.marcadoEn,
  });

  bool get esFrecuente => tipoVisitaRuta == 'frecuente';
  bool get esNuevo => tipoVisitaRuta == 'nuevo';
  bool get visitado => estadoVisita == 'visitado';
  bool get noEncontrado => estadoVisita == 'no_encontrado';
  bool get pendiente => estadoVisita == 'pendiente';
  bool get tieneGps =>
      latitud != null && longitud != null && latitud!.abs() > 0.0001 && longitud!.abs() > 0.0001;

  ClienteRuta copyWith({
    int? ordenSecuencial,
    String? estadoVisita,
    DateTime? marcadoEn,
  }) =>
      ClienteRuta(
        id: id,
        vendedorId: vendedorId,
        nombre: nombre,
        direccion: direccion,
        diaVisita: diaVisita,
        diaRuta: diaRuta,
        ordenSecuencial: ordenSecuencial ?? ordenRuta,
        ordenRuta: ordenSecuencial ?? ordenRuta,
        latitud: latitud,
        longitud: longitud,
        tipoVisitaRuta: tipoVisitaRuta,
        telefono: telefono,
        estadoVisita: estadoVisita ?? this.estadoVisita,
        marcadoEn: marcadoEn ?? this.marcadoEn,
      );

  factory ClienteRuta.fromJson(Map<String, dynamic> j) {
    final diaRaw = (j['dia_ruta'] ?? j['dia_visita'] ?? 'Lunes').toString();
    final orden = (j['orden_ruta'] as num?)?.toInt() ?? (j['orden_secuencial'] as num?)?.toInt() ?? 0;
    final canon = RutasService.canonDia(diaRaw);
    return ClienteRuta(
        id: j['id'].toString(),
        vendedorId: j['vendedor_id']?.toString(),
        nombre: j['nombre'] ?? '—',
        direccion: j['direccion'],
        diaVisita: canon,
        diaRuta: RutasService.etiquetaDia(canon),
        ordenSecuencial: orden,
        ordenRuta: orden,
        latitud: (j['latitud'] as num?)?.toDouble(),
        longitud: (j['longitud'] as num?)?.toDouble(),
        tipoVisitaRuta: j['tipo_visita_ruta'] ?? 'frecuente',
        telefono: j['telefono'],
        estadoVisita: j['estado_visita'] ?? 'pendiente',
        marcadoEn: j['marcado_en'] != null ? DateTime.tryParse(j['marcado_en'].toString()) : null,
      );
  }
}

class RutasDiaResult {
  final String vendedorId;
  final String dia;
  final String fecha;
  final int totalClientes;
  final int visitados;
  final int pendientes;
  final List<ClienteRuta> clientes;

  RutasDiaResult({
    required this.vendedorId,
    required this.dia,
    required this.fecha,
    required this.totalClientes,
    required this.visitados,
    required this.pendientes,
    required this.clientes,
  });

  factory RutasDiaResult.fromJson(Map<String, dynamic> j) => RutasDiaResult(
        vendedorId: j['vendedor_id'].toString(),
        dia: j['dia'] ?? 'LUNES',
        fecha: j['fecha']?.toString() ?? '',
        totalClientes: (j['total_clientes'] as num?)?.toInt() ?? 0,
        visitados: (j['visitados'] as num?)?.toInt() ?? 0,
        pendientes: (j['pendientes'] as num?)?.toInt() ?? 0,
        clientes: (j['clientes'] as List? ?? [])
            .map((e) => ClienteRuta.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class ResumenVendedorRuta {
  final String vendedorId;
  final String vendedorNombre;
  final int totalClientes;
  final int visitados;
  final int pendientes;
  final int noEncontrados;
  final double porcentajeAvance;

  ResumenVendedorRuta({
    required this.vendedorId,
    required this.vendedorNombre,
    required this.totalClientes,
    required this.visitados,
    required this.pendientes,
    required this.noEncontrados,
    required this.porcentajeAvance,
  });

  factory ResumenVendedorRuta.fromJson(Map<String, dynamic> j) => ResumenVendedorRuta(
        vendedorId: j['vendedor_id'].toString(),
        vendedorNombre: j['vendedor_nombre'] ?? '—',
        totalClientes: (j['total_clientes'] as num?)?.toInt() ?? 0,
        visitados: (j['visitados'] as num?)?.toInt() ?? 0,
        pendientes: (j['pendientes'] as num?)?.toInt() ?? 0,
        noEncontrados: (j['no_encontrados'] as num?)?.toInt() ?? 0,
        porcentajeAvance: (j['porcentaje_avance'] as num?)?.toDouble() ?? 0,
      );
}

class RutasResumenResult {
  final String fecha;
  final String dia;
  final List<ResumenVendedorRuta> vendedores;

  RutasResumenResult({
    required this.fecha,
    required this.dia,
    required this.vendedores,
  });

  factory RutasResumenResult.fromJson(Map<String, dynamic> j) => RutasResumenResult(
        fecha: j['fecha']?.toString() ?? '',
        dia: j['dia'] ?? '',
        vendedores: (j['vendedores'] as List? ?? [])
            .map((e) => ResumenVendedorRuta.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class RutasService {
  RutasService(this._api);
  final ApiClient _api;

  static const dias = [
    'LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO',
  ];

  static const diasEtiqueta = [
    'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo',
  ];

  static const diasLabel = {
    'LUNES': 'Lunes',
    'MARTES': 'Martes',
    'MIERCOLES': 'Miércoles',
    'JUEVES': 'Jueves',
    'VIERNES': 'Viernes',
    'SABADO': 'Sábado',
    'DOMINGO': 'Domingo',
  };

  static String canonDia(String raw) {
    final limpio = raw
        .trim()
        .toUpperCase()
        .replaceAll('Á', 'A')
        .replaceAll('É', 'E')
        .replaceAll('Í', 'I')
        .replaceAll('Ó', 'O')
        .replaceAll('Ú', 'U');
    return dias.contains(limpio) ? limpio : limpio;
  }

  static String etiquetaDia(String raw) => diasLabel[canonDia(raw)] ?? raw.trim();

  static String diaActual() => dias[DateTime.now().weekday - 1];

  static String etiquetaDiaActual() => diasEtiqueta[DateTime.now().weekday - 1];

  /// Deja únicamente el recorrido del día elegido, en el orden de visita GPS.
  static List<ClienteRuta> soloDia(List<ClienteRuta> clientes, String dia) {
    final canon = canonDia(dia);
    final lista = clientes.where((c) => c.diaVisita == canon || canonDia(c.diaRuta) == canon).toList();
    lista.sort((a, b) => a.ordenRuta.compareTo(b.ordenRuta));
    return lista;
  }

  static RutasDiaResult recortarDia(RutasDiaResult result, String dia) {
    final clientes = soloDia(result.clientes, dia);
    return RutasDiaResult(
      vendedorId: result.vendedorId,
      dia: canonDia(dia),
      fecha: result.fecha,
      totalClientes: clientes.length,
      visitados: clientes.where((c) => c.visitado).length,
      pendientes: clientes.where((c) => c.pendiente).length,
      clientes: clientes,
    );
  }

  static String fechaActual() => DateTime.now().toIso8601String().substring(0, 10);

  String _query(Map<String, String> params) {
    if (params.isEmpty) return '';
    return '?${params.entries.map((e) => '${e.key}=${Uri.encodeComponent(e.value)}').join('&')}';
  }

  Future<RutasDiaResult> rutaDelDia({
    String? vendedorId,
    String? dia,
    String? fecha,
  }) async {
    final params = <String, String>{};
    if (vendedorId != null) params['vendedor_id'] = vendedorId;
    if (dia != null) params['dia'] = dia;
    if (fecha != null) params['fecha'] = fecha;

    final data = await _api.get('/rutas/dia${_query(params)}') as Map<String, dynamic>;
    final result = RutasDiaResult.fromJson(data);
    return recortarDia(result, dia ?? result.dia);
  }

  Future<RutasDiaResult> reordenar({
    required String dia,
    required List<ClienteRuta> clientes,
    String? vendedorId,
  }) async {
    final body = {
      'dia': dia,
      if (vendedorId != null) 'vendedor_id': vendedorId,
      'orden': clientes
          .map((c) => {
                'cliente_id': c.id,
                'orden_ruta': c.ordenRuta,
                'orden_secuencial': c.ordenRuta,
              })
          .toList(),
    };
    final data = await _api.put('/rutas/dia/reordenar', body) as Map<String, dynamic>;
    return recortarDia(RutasDiaResult.fromJson(data), dia);
  }

  Future<void> marcarVisita({
    required String clienteId,
    String estado = 'visitado',
    String? notas,
    double? latitudVisita,
    double? longitudVisita,
    String? fecha,
    String? vendedorId,
  }) async {
    final params = <String, String>{};
    if (vendedorId != null) params['vendedor_id'] = vendedorId;

    await _api.post('/rutas/visitas${_query(params)}', {
      'cliente_id': clienteId,
      'estado': estado,
      if (notas != null) 'notas': notas,
      if (latitudVisita != null) 'latitud_visita': latitudVisita,
      if (longitudVisita != null) 'longitud_visita': longitudVisita,
      if (fecha != null) 'fecha': fecha,
    });
  }

  Future<void> sincronizarPendientes(String usuarioId) async {
    final pendientes = await RutasOfflineQueue.pendientes(usuarioId);
    if (pendientes.isEmpty) return;

    final restantes = <Map<String, dynamic>>[];
    for (final visita in pendientes) {
      try {
        await _api.post('/rutas/visitas', visita);
      } catch (_) {
        restantes.add(visita);
      }
    }
    await RutasOfflineQueue.reemplazar(usuarioId, restantes);
  }

  Future<bool> marcarVisitaConOffline({
    required String usuarioId,
    required String clienteId,
    String estado = 'visitado',
    String? vendedorId,
    String? fecha,
  }) async {
    final payload = {
      'cliente_id': clienteId,
      'estado': estado,
      if (fecha != null) 'fecha': fecha,
    };
    try {
      final params = vendedorId != null ? {'vendedor_id': vendedorId} : <String, String>{};
      await _api.post('/rutas/visitas${_query(params)}', payload);
      return true;
    } catch (_) {
      await RutasOfflineQueue.encolar(usuarioId, payload);
      return false;
    }
  }

  Future<RutasResumenResult> resumen({String? fecha, String? dia}) async {
    final params = <String, String>{};
    if (fecha != null) params['fecha'] = fecha;
    if (dia != null) params['dia'] = dia;

    final data = await _api.get('/rutas/resumen${_query(params)}') as Map<String, dynamic>;
    return RutasResumenResult.fromJson(data);
  }
}
