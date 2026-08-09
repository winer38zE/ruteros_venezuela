import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import '../theme/app_theme.dart';
import '../utils/maps_navigation.dart';
import '../utils/route_estimator.dart';

/// Indicador de distancia y ETA hacia domicilio o trabajo del cliente.
class AsistenteRutaWidget extends StatefulWidget {
  const AsistenteRutaWidget({
    super.key,
    this.latResidencia,
    this.lngResidencia,
    this.latTrabajo,
    this.lngTrabajo,
  });

  final double? latResidencia;
  final double? lngResidencia;
  final double? latTrabajo;
  final double? lngTrabajo;

  @override
  State<AsistenteRutaWidget> createState() => _AsistenteRutaWidgetState();
}

class _AsistenteRutaWidgetState extends State<AsistenteRutaWidget> {
  Position? _posicion;
  bool _cargando = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _obtenerUbicacion();
  }

  Future<void> _obtenerUbicacion() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final enabled = await Geolocator.isLocationServiceEnabled();
      if (!enabled) {
        throw Exception('GPS desactivado');
      }
      var permiso = await Geolocator.checkPermission();
      if (permiso == LocationPermission.denied) {
        permiso = await Geolocator.requestPermission();
      }
      if (permiso == LocationPermission.denied ||
          permiso == LocationPermission.deniedForever) {
        throw Exception('Sin permiso de ubicación');
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
          timeLimit: Duration(seconds: 12),
        ),
      );
      if (mounted) setState(() => _posicion = pos);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Widget _filaEstimacion(String emoji, String etiqueta, double? lat, double? lng) {
    if (!coordenadasValidas(lat, lng)) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Row(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 16)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '$etiqueta: sin coordenadas',
                style: TextStyle(fontSize: 12, color: AppColors.textMuted),
              ),
            ),
          ],
        ),
      );
    }

    if (_posicion == null) {
      return Padding(
        padding: const EdgeInsets.only(bottom: 6),
        child: Row(
          children: [
            Text(emoji, style: const TextStyle(fontSize: 16)),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '$etiqueta: activa GPS para estimar ruta',
                style: TextStyle(fontSize: 12, color: AppColors.textMuted),
              ),
            ),
          ],
        ),
      );
    }

    final est = estimarRuta(
      origenLat: _posicion!.latitude,
      origenLng: _posicion!.longitude,
      destinoLat: lat!,
      destinoLng: lng!,
    );
    final color = Color(est.colorHex);

    return Container(
      margin: const EdgeInsets.only(bottom: 8),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 18)),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '$etiqueta · ${formatearDistancia(est.distanciaKm)} · ${formatearEta(est.minutosEstimados)}',
                  style: TextStyle(fontWeight: FontWeight.w700, fontSize: 12, color: color),
                ),
                Text(
                  est.descripcionEstado,
                  style: TextStyle(fontSize: 11, color: AppColors.textMuted),
                ),
              ],
            ),
          ),
          Icon(Icons.route_rounded, size: 18, color: color),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final tieneCoords = coordenadasValidas(widget.latResidencia, widget.lngResidencia) ||
        coordenadasValidas(widget.latTrabajo, widget.lngTrabajo);
    if (!tieneCoords) return const SizedBox.shrink();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Row(
          children: [
            const Icon(Icons.auto_awesome_rounded, size: 16, color: AppColors.violet),
            const SizedBox(width: 6),
            const Text(
              'Asistente de ruta',
              style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13),
            ),
            const Spacer(),
            if (_cargando)
              const SizedBox(
                width: 14,
                height: 14,
                child: CircularProgressIndicator(strokeWidth: 2),
              )
            else
              InkWell(
                onTap: _obtenerUbicacion,
                child: Icon(Icons.my_location_rounded, size: 18, color: AppColors.neonCyan),
              ),
          ],
        ),
        if (_error != null) ...[
          const SizedBox(height: 4),
          Text(_error!, style: const TextStyle(fontSize: 11, color: Colors.orange)),
        ],
        const SizedBox(height: 8),
        _filaEstimacion('🏠', 'Domicilio', widget.latResidencia, widget.lngResidencia),
        _filaEstimacion('💼', 'Trabajo', widget.latTrabajo, widget.lngTrabajo),
      ],
    );
  }
}
