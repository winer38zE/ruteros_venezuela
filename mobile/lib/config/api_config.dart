import '../services/api_service.dart';

class ApiConfig {
  /// URL base para la app móvil en dispositivo físico (red LAN).
  static String get baseUrl => ApiService.baseUrl.replaceAll('/api/v1', '');

  static const String apiPrefix = '/api/v1';
}
