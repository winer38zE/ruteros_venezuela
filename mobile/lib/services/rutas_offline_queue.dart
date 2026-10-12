import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// Cola local de visitas pendientes de sincronizar con el backend.
class RutasOfflineQueue {
  static String _clave(String usuarioId) => 'rutas_pending_visits_$usuarioId';

  static Future<List<Map<String, dynamic>>> pendientes(String usuarioId) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_clave(usuarioId));
    if (raw == null) return [];
    return (jsonDecode(raw) as List).cast<Map<String, dynamic>>();
  }

  static Future<void> encolar(String usuarioId, Map<String, dynamic> visita) async {
    final lista = await pendientes(usuarioId);
    lista.removeWhere((v) => v['cliente_id'] == visita['cliente_id']);
    lista.add(visita);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_clave(usuarioId), jsonEncode(lista));
  }

  static Future<void> limpiar(String usuarioId) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_clave(usuarioId));
  }

  static Future<void> reemplazar(String usuarioId, List<Map<String, dynamic>> lista) async {
    final prefs = await SharedPreferences.getInstance();
    if (lista.isEmpty) {
      await prefs.remove(_clave(usuarioId));
    } else {
      await prefs.setString(_clave(usuarioId), jsonEncode(lista));
    }
  }
}
