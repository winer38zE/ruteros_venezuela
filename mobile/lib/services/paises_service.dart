import '../models/pais_region.dart';
import 'api_service.dart';

/// Catálogo de países (endpoint público FastAPI, sin sesión).
class PaisesService {
  PaisesService(this._api);

  final ApiService _api;

  Future<List<PaisRegion>> listarActivos() async {
    final data = await _api.get('/paises');
    if (data is! List) return [];
    return data
        .whereType<Map<String, dynamic>>()
        .map(PaisRegion.fromJson)
        .toList();
  }
}
