import 'dart:math';

/// Velocidad urbana promedio (km/h) para estimar ETA sin API de tráfico.
const double _velocidadUrbanaKmh = 28.0;

class EstimacionRuta {
  const EstimacionRuta({
    required this.distanciaKm,
    required this.minutosEstimados,
    required this.estadoRuta,
    required this.descripcionEstado,
    required this.colorHex,
  });

  final double distanciaKm;
  final int minutosEstimados;
  final String estadoRuta;
  final String descripcionEstado;
  final int colorHex;
}

/// Distancia Haversine entre dos puntos GPS (km).
double distanciaKm(double lat1, double lng1, double lat2, double lng2) {
  const r = 6371.0;
  final dLat = _rad(lat2 - lat1);
  final dLng = _rad(lng2 - lng1);
  final a = sin(dLat / 2) * sin(dLat / 2) +
      cos(_rad(lat1)) * cos(_rad(lat2)) * sin(dLng / 2) * sin(dLng / 2);
  final c = 2 * atan2(sqrt(a), sqrt(1 - a));
  return r * c;
}

double _rad(double deg) => deg * pi / 180;

/// Estima tiempo y estado de ruta según distancia (heurística urbana).
EstimacionRuta estimarRuta({
  required double origenLat,
  required double origenLng,
  required double destinoLat,
  required double destinoLng,
}) {
  final km = distanciaKm(origenLat, origenLng, destinoLat, destinoLng);
  final minutos = max(1, (km / _velocidadUrbanaKmh * 60).round());

  if (km < 2) {
    return EstimacionRuta(
      distanciaKm: km,
      minutosEstimados: minutos,
      estadoRuta: 'cerca',
      descripcionEstado: 'Ruta corta · tráfico ligero',
      colorHex: 0xFF10B981,
    );
  }
  if (km < 8) {
    return EstimacionRuta(
      distanciaKm: km,
      minutosEstimados: minutos,
      estadoRuta: 'media',
      descripcionEstado: 'Ruta urbana · revisar tráfico en Maps',
      colorHex: 0xFFF59E0B,
    );
  }
  return EstimacionRuta(
    distanciaKm: km,
    minutosEstimados: minutos,
    estadoRuta: 'lejana',
    descripcionEstado: 'Ruta larga · priorizar salida temprana',
    colorHex: 0xFFEF4444,
  );
}

String formatearDistancia(double km) {
  if (km < 1) return '${(km * 1000).round()} m';
  return '${km.toStringAsFixed(1)} km';
}

String formatearEta(int minutos) {
  if (minutos < 60) return '~$minutos min';
  final h = minutos ~/ 60;
  final m = minutos % 60;
  return m > 0 ? '~$h h $m min' : '~$h h';
}
