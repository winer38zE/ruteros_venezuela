import '../models/pais_region.dart';
import 'api_service.dart';

/// Catálogo de países vía FastAPI (proxy admin → PocketBase).
class PaisesService {
  PaisesService(this._api);

  final ApiService _api;

  Future<List<PaisRegion>> listarActivos() async {
    final data = await _api.get('/paises');
    if (data is! List) return [];
    final lista = <PaisRegion>[];
    for (final raw in data) {
      if (raw is! Map<String, dynamic>) continue;
      try {
        final p = PaisRegion.fromJson(raw);
        if (p.valido) lista.add(p);
      } catch (_) {}
    }
    lista.sort((a, b) => a.nombre.compareTo(b.nombre));
    return lista;
  }
}
