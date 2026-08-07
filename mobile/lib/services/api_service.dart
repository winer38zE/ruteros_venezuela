import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);

  @override
  String toString() => message;
}

/// Cliente HTTP centralizado para ED NET PRO — FastAPI multi-tenant.
class ApiService {
  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Alias de [ApiConfig.apiBaseUrl] — punto único de configuración.
  static String get baseUrl => ApiConfig.apiBaseUrl;

  static const _kToken = 'auth_token';
  static const _kUsuarioId = 'usuario_id';
  static const _kUsuarioJson = 'usuario_json';

  final http.Client _client;

  String? _token;
  String? _usuarioId;
  String? _usuarioJson;

  String? get token => _token;
  String? get usuarioId => _usuarioId;
  String? get usuarioJson => _usuarioJson;
  bool get hasSession => _usuarioId != null;

  /// Restaura sesión guardada (shared_preferences).
  Future<void> loadSession() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      _token = prefs.getString(_kToken);
      _usuarioId = prefs.getString(_kUsuarioId);
      _usuarioJson = prefs.getString(_kUsuarioJson);
    } catch (_) {
      await clearSession(persist: false);
    }
  }

  Future<void> saveSession({
    required String token,
    required String usuarioId,
    required String usuarioJson,
  }) async {
    _token = token;
    _usuarioId = usuarioId;
    _usuarioJson = usuarioJson;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString(_kToken, token);
      await prefs.setString(_kUsuarioId, usuarioId);
      await prefs.setString(_kUsuarioJson, usuarioJson);
    } catch (_) {}
  }

  Future<void> clearSession({bool persist = true}) async {
    _token = null;
    _usuarioId = null;
    _usuarioJson = null;
    if (!persist) return;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_kToken);
      await prefs.remove(_kUsuarioId);
      await prefs.remove(_kUsuarioJson);
    } catch (_) {}
  }

  /// Compatibilidad con servicios existentes.
  void setUsuarioId(String? id) {
    _usuarioId = id;
    if (id != null) _token = id;
  }

  Map<String, String> get _headers {
    final h = <String, String>{'Content-Type': 'application/json'};
    if (_token != null && _token!.isNotEmpty) {
      h['Authorization'] = 'Bearer $_token';
    }
    if (_usuarioId != null) {
      h['X-Usuario-Id'] = _usuarioId!;
    }
    return h;
  }

  Uri _uri(String path, [Map<String, String>? query]) {
    final normalized = path.startsWith('/') ? path : '/$path';
    return Uri.parse('$baseUrl$normalized').replace(queryParameters: query);
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    try {
      final res = await _client
          .get(_uri(path, query), headers: _headers)
          .timeout(const Duration(seconds: 30));
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor: $baseUrl');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  Future<dynamic> post(String path, Map<String, dynamic> body) async {
    try {
      final res = await _client
          .post(
            _uri(path),
            headers: _headers,
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 30));
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor: $baseUrl');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  Future<dynamic> patch(String path, Map<String, dynamic> body) async {
    try {
      final res = await _client
          .patch(
            _uri(path),
            headers: _headers,
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 30));
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor: $baseUrl');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  Future<dynamic> put(String path, Map<String, dynamic> body) async {
    try {
      final res = await _client
          .put(
            _uri(path),
            headers: _headers,
            body: jsonEncode(body),
          )
          .timeout(const Duration(seconds: 30));
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor: $baseUrl');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  Future<List<int>> download(String path, {Map<String, String>? query}) async {
    try {
      final res = await _client
          .get(_uri(path, query), headers: _headers)
          .timeout(const Duration(seconds: 60));
      if (res.statusCode >= 400) {
        throw ApiException(res.statusCode, _errorMessage(res));
      }
      return res.bodyBytes;
    } on SocketException {
      throw ApiException(0, 'Sin conexión al descargar. Revisa internet.');
    } on TimeoutException {
      throw ApiException(0, 'Descarga interrumpida por tiempo de espera.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error al descargar: $e');
    }
  }

  dynamic _decode(http.Response res) {
    if (res.statusCode >= 400) {
      throw ApiException(res.statusCode, _errorMessage(res));
    }
    if (res.body.isEmpty) return null;
    return jsonDecode(res.body);
  }

  String _errorMessage(http.Response res) {
    try {
      final data = jsonDecode(res.body);
      if (data is Map && data['detail'] != null) {
        return data['detail'].toString();
      }
    } catch (_) {}
    return 'Error ${res.statusCode}';
  }
}
