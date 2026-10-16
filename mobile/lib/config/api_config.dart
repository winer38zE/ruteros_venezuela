/// Configuración centralizada de red — ED NET PRO Mobile.
class ApiConfig {
  ApiConfig._();

  static const String apiPrefix = '/api/v1';

  /// Producción (Hetzner / Coolify). Incluye `/api/v1`.
  static const String _productionApiBaseUrl =
      'https://api-ruteros.edwuarcardenas.online/api/v1';

  /// Hosts con certificado intermedio incompleto en el servidor (aceptar solo estos).
  /// Quitar cuando el nginx/Coolify sirva la cadena SSL completa.
  static const Set<String> insecureSslHosts = {
    'api-ruteros.edwuarcardenas.online',
  };

  /// Override opcional en compilación:
  /// `flutter run --dart-define=API_BASE_URL=http://192.168.x.x:8000/api/v1`
  static const String _envApiBaseUrl = String.fromEnvironment('API_BASE_URL');

  /// URL base de la API (termina en `/api/v1`).
  static String get apiBaseUrl {
    if (_envApiBaseUrl.isNotEmpty) {
      return _normalizeApiBaseUrl(_envApiBaseUrl);
    }
    return _productionApiBaseUrl;
  }

  /// Origen del servidor sin prefijo de API (útil para health checks).
  static String get serverOrigin {
    if (apiBaseUrl.endsWith(apiPrefix)) {
      return apiBaseUrl.substring(0, apiBaseUrl.length - apiPrefix.length);
    }
    return apiBaseUrl;
  }

  static String _normalizeApiBaseUrl(String url) {
    var normalized = url.trim();
    if (normalized.endsWith('/')) {
      normalized = normalized.substring(0, normalized.length - 1);
    }
    if (normalized.endsWith(apiPrefix)) {
      return normalized;
    }
    return '$normalized$apiPrefix';
  }
}
