import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../models/pais_region.dart';

/// Región operativa (país + moneda) persistida tras el login.
class RegionSessionService {
  RegionSessionService({FlutterSecureStorage? storage})
      : _storage = storage ??
            const FlutterSecureStorage(
              aOptions: AndroidOptions(encryptedSharedPreferences: true),
            );

  static const _kRegionJson = 'region_pais_json';

  final FlutterSecureStorage _storage;

  Future<void> guardar(PaisRegion region) async {
    await _storage.write(key: _kRegionJson, value: jsonEncode(region.toJson()));
  }

  Future<PaisRegion?> leer() async {
    final raw = await _storage.read(key: _kRegionJson);
    if (raw == null || raw.isEmpty) return null;
    try {
      final data = jsonDecode(raw);
      if (data is Map<String, dynamic>) {
        return PaisRegion.fromJson(data);
      }
    } catch (_) {}
    return null;
  }

  Future<void> limpiar() async {
    await _storage.delete(key: _kRegionJson);
  }
}
