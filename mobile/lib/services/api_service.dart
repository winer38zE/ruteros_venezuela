import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:http/io_client.dart';
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
  ApiService({http.Client? client}) : _client = client ?? createHttpClient();

  /// Cliente HTTP con soporte para cadena SSL incompleta en hosts de confianza.
  static http.Client createHttpClient() {
    if (kIsWeb) {
      return http.Client();
    }
    final io = HttpClient();
    io.badCertificateCallback = (X509Certificate cert, String host, int port) {
      return ApiConfig.insecureSslHosts.contains(host);
    };
    return IOClient(io);
  }

  /// Alias de [ApiConfig.apiBaseUrl] — punto único de configuración.
  static String get baseUrl => ApiConfig.apiBaseUrl;

  static const _kToken = 'auth_token';
  static const _kUsuarioId = 'usuario_id';
  static const _kUsuarioJson = 'usuario_json';

  final http.Client _client;

  String? _token;
  String? _usuarioId;
  String? _usuarioJson;

  /// Se invoca ante HTTP 401 (token expirado o sesión inválida).
  Future<void> Function(ApiException error)? onUnauthorized;

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

  /// GET `/health/ready` en el origen del servidor (fuera de `/api/v1`).
  Future<Map<String, dynamic>> fetchHealthReady() async {
    final uri = Uri.parse('${ApiConfig.serverOrigin}/health/ready');
    try {
      final res = await _client
          .get(uri, headers: const {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 20));
      if (res.statusCode >= 200 && res.statusCode < 300) {
        final data = jsonDecode(res.body);
        if (data is Map<String, dynamic>) return data;
        return {'status': 'ready', 'raw': data};
      }
      if (res.statusCode == 502 || res.statusCode == 503 || res.statusCode == 504) {
        throw ApiException(
          res.statusCode,
          'Servidor no disponible (${res.statusCode}). Intenta de nuevo.',
        );
      }
      throw ApiException(res.statusCode, _errorMessage(res));
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor.');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  /// Lectura pública de una colección PocketBase (sin sesión FastAPI).
  Future<Map<String, dynamic>> getPocketBaseCollectionRecords(
    String collection, {
    Map<String, String>? query,
  }) async {
    final uri = ApiConfig.pocketBaseCollectionRecordsUri(collection, query: query);
    try {
      final res = await _client
          .get(uri, headers: const {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 30));
      final data = _decode(res);
      if (data is Map<String, dynamic>) return data;
      throw ApiException(0, 'Respuesta inválida de PocketBase');
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y PocketBase.');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado al cargar países.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error al leer PocketBase: $e');
    }
  }

  Future<dynamic> get(String path, {Map<String, String>? query}) async {
    try {
      final res = await _client
          .get(_uri(path, query), headers: _headers)
          .timeout(const Duration(seconds: 30));
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor.');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  Future<dynamic> post(
    String path,
    Map<String, dynamic> body, {
    Duration timeout = const Duration(seconds: 30),
  }) async {
    try {
      final res = await _client
          .post(
            _uri(path),
            headers: _headers,
            body: jsonEncode(body),
          )
          .timeout(timeout);
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor.');
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
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor.');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  /// POST multipart a una URL absoluta (p. ej. `/api/ai/...` fuera de `/api/v1`).
  Future<dynamic> postMultipartAbsolute(
    String absoluteUrl,
    Map<String, String> fields, {
    required String fileField,
    required List<int> bytes,
    required String filename,
    Duration timeout = const Duration(seconds: 60),
  }) async {
    try {
      final request = http.MultipartRequest('POST', Uri.parse(absoluteUrl));
      request.headers.addAll(_headers);
      request.headers.remove('Content-Type');
      request.fields.addAll(fields);
      request.files.add(http.MultipartFile.fromBytes(fileField, bytes, filename: filename));
      final streamed = await _client.send(request).timeout(timeout);
      final res = await http.Response.fromStream(streamed);
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor.');
    } on TimeoutException {
      throw ApiException(0, 'Tiempo de espera agotado. Revisa tu conexión.');
    } on ApiException {
      rethrow;
    } catch (e) {
      throw ApiException(0, 'Error de red: $e');
    }
  }

  Future<dynamic> postMultipart(
    String path,
    Map<String, String> fields, {
    required String fileField,
    required List<int> bytes,
    required String filename,
    Duration timeout = const Duration(seconds: 60),
  }) async {
    try {
      final request = http.MultipartRequest('POST', _uri(path));
      request.headers.addAll(_headers);
      request.headers.remove('Content-Type');
      request.fields.addAll(fields);
      request.files.add(http.MultipartFile.fromBytes(fileField, bytes, filename: filename));
      final streamed = await _client.send(request).timeout(timeout);
      final res = await http.Response.fromStream(streamed);
      return _decode(res);
    } on SocketException {
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor.');
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
      throw ApiException(0, 'Sin conexión. Verifica internet y el servidor.');
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
      final exc = ApiException(res.statusCode, _errorMessage(res));
      if (res.statusCode == 401 &&
          onUnauthorized != null &&
          !_esRutaLogin(res.request?.url.path ?? '')) {
        unawaited(onUnauthorized!(exc));
      }
      throw exc;
    }
    if (res.body.isEmpty) return null;
    return jsonDecode(res.body);
  }

  static bool _esRutaLogin(String path) =>
      path.contains('/auth/login') || path.endsWith('/auth/login');

  String _errorMessage(http.Response res) {
    if (kDebugMode && res.statusCode >= 400) {
      debugPrint('API ${res.statusCode} ${res.request?.url}: ${res.body}');
    }
    if (res.statusCode >= 500) {
      try {
        final data = jsonDecode(res.body);
        if (data is Map && data['detail'] != null) {
          return data['detail'].toString();
        }
      } catch (_) {}
      return 'No se pudo guardar. Intenta de nuevo.';
    }
    if (res.statusCode == 401) {
      try {
        final data = jsonDecode(res.body);
        if (data is Map && data['detail'] != null) {
          return data['detail'].toString();
        }
      } catch (_) {}
      return 'Sesión inválida. Vuelve a iniciar sesión.';
    }
    if (res.statusCode == 502 || res.statusCode == 503 || res.statusCode == 504) {
      return 'Servidor no disponible, reintenta';
    }
    try {
      final data = jsonDecode(res.body);
      if (data is Map) {
        if (data['detail'] != null) {
          return data['detail'].toString();
        }
        if (data['message'] != null) {
          return data['message'].toString();
        }
      }
    } catch (_) {}
    if (res.statusCode == 404) {
      return 'Not Found';
    }
    return 'Error ${res.statusCode}';
  }
}
