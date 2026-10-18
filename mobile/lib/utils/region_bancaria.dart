import '../models/configuracion_bancaria_pais.dart';
import '../models/pais_region.dart';
import '../services/paises_service.dart';

/// Resuelve `configuracion_bancaria` del país de la sesión (memoria o API).
Future<ConfiguracionBancariaPais> configuracionBancariaSesion({
  required PaisesService paises,
  PaisRegion? region,
  PaisRegion? paisUsuario,
  String? paisId,
}) async {
  Map<String, dynamic>? raw =
      paisUsuario?.configuracionBancaria ?? region?.configuracionBancaria;
  if (raw != null && raw.isNotEmpty) {
    return ConfiguracionBancariaPais.fromJson(raw);
  }

  final id = paisId ?? region?.id ?? paisUsuario?.id;
  if (id == null || id.isEmpty) {
    return ConfiguracionBancariaPais.fallbackVenezuela();
  }

  try {
    final lista = await paises.listarActivos();
    for (final p in lista) {
      if (p.id == id && p.configuracionBancaria != null) {
        return ConfiguracionBancariaPais.fromJson(p.configuracionBancaria);
      }
    }
  } catch (_) {}

  return ConfiguracionBancariaPais.fallbackVenezuela();
}
