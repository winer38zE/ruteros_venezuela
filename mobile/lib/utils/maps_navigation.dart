import 'package:url_launcher/url_launcher.dart';

/// Abre Google Maps con navegación hacia coordenadas GPS.
Future<bool> abrirRutaGoogleMaps({
  required double latitud,
  required double longitud,
}) async {
  final uri = Uri.parse(
    'https://www.google.com/maps/dir/?api=1&destination=$latitud,$longitud&travelmode=driving',
  );
  if (await canLaunchUrl(uri)) {
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }
  final fallback = Uri.parse(
    'https://www.google.com/maps/search/?api=1&query=$latitud,$longitud',
  );
  if (await canLaunchUrl(fallback)) {
    return launchUrl(fallback, mode: LaunchMode.externalApplication);
  }
  return false;
}

/// Abre Google Maps usando una dirección de texto cuando no hay GPS.
Future<bool> abrirRutaPorDireccion(String direccion) async {
  final limpia = direccion.trim();
  if (limpia.isEmpty) return false;
  final uri = Uri.parse(
    'https://www.google.com/maps/dir/?api=1&destination=${Uri.encodeComponent(limpia)}&travelmode=driving',
  );
  if (await canLaunchUrl(uri)) {
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }
  return false;
}

bool coordenadasValidas(double? lat, double? lng) {
  if (lat == null || lng == null) return false;
  return lat.abs() > 0.0001 && lng.abs() > 0.0001;
}
