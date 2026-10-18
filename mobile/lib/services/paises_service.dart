import '../models/pais_region.dart';
import 'api_service.dart';

/// Catálogo de países vía PocketBase (reglas list/view públicas en `paises`).
class PaisesService {
  PaisesService(this._api);

  final ApiService _api;

  Future<List<PaisRegion>> listarActivos() async {
    final data = await _api.getPocketBaseCollectionRecords(
      'paises',
      query: const {
        'filter': 'activo=true',
        'sort': 'nombre',
        'perPage': '100',
      },
    );
    final items = data['items'];
    if (items is! List) return [];
    final lista = <PaisRegion>[];
    for (final raw in items) {
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
