import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import '../theme/app_theme.dart';
import '../utils/maps_navigation.dart';

class GpsCoords {
  const GpsCoords({required this.latitud, required this.longitud});
  final double latitud;
  final double longitud;
}

/// Botón de captura GPS + mapa en miniatura de confirmación.
class GpsLocationCapture extends StatefulWidget {
  const GpsLocationCapture({
    super.key,
    required this.etiqueta,
    this.latitud,
    this.longitud,
    required this.onCoordsChanged,
    this.color = AppColors.emerald,
  });

  final String etiqueta;
  final double? latitud;
  final double? longitud;
  final ValueChanged<GpsCoords> onCoordsChanged;
  final Color color;

  @override
  State<GpsLocationCapture> createState() => _GpsLocationCaptureState();
}

class _GpsLocationCaptureState extends State<GpsLocationCapture> {
  bool _capturando = false;
  String? _error;
  GoogleMapController? _mapCtrl;

  LatLng get _posicion {
    if (widget.latitud != null && widget.longitud != null) {
      return LatLng(widget.latitud!, widget.longitud!);
    }
    return const LatLng(10.4806, -66.9036);
  }

  Set<Marker> get _markers {
    if (widget.latitud == null || widget.longitud == null) return {};
    return {
      Marker(
        markerId: MarkerId(widget.etiqueta),
        position: LatLng(widget.latitud!, widget.longitud!),
      ),
    };
  }

  Future<void> _capturarGps() async {
    setState(() {
      _capturando = true;
      _error = null;
    });
    try {
      final enabled = await Geolocator.isLocationServiceEnabled();
      if (!enabled) {
        throw Exception('Activa el GPS del dispositivo');
      }

      var permiso = await Geolocator.checkPermission();
      if (permiso == LocationPermission.denied) {
        permiso = await Geolocator.requestPermission();
      }
      if (permiso == LocationPermission.denied ||
          permiso == LocationPermission.deniedForever) {
        throw Exception('Permiso de ubicación denegado');
      }

      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 20),
        ),
      );

      widget.onCoordsChanged(GpsCoords(latitud: pos.latitude, longitud: pos.longitude));
      _mapCtrl?.animateCamera(
        CameraUpdate.newLatLngZoom(LatLng(pos.latitude, pos.longitude), 16),
      );
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _capturando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final tieneCoords = widget.latitud != null && widget.longitud != null;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FilledButton.icon(
          onPressed: _capturando ? null : _capturarGps,
          icon: _capturando
              ? const SizedBox(
                  width: 18,
                  height: 18,
                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                )
              : const Text('📍', style: TextStyle(fontSize: 18)),
          label: Text(
            _capturando
                ? 'Obteniendo GPS…'
                : '📍 Capturar Ubicación GPS Actual — ${widget.etiqueta}',
            textAlign: TextAlign.center,
          ),
          style: FilledButton.styleFrom(
            backgroundColor: widget.color,
            foregroundColor: AppColors.bgDeep,
            minimumSize: const Size(double.infinity, 48),
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
          ),
        ),
        if (_error != null) ...[
          const SizedBox(height: 8),
          Text(_error!, style: const TextStyle(color: Colors.red, fontSize: 12)),
        ],
        if (tieneCoords) ...[
          const SizedBox(height: 10),
          Text(
            'Lat: ${widget.latitud!.toStringAsFixed(6)} · Lng: ${widget.longitud!.toStringAsFixed(6)}',
            style: TextStyle(fontSize: 12, color: AppColors.textMuted),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(14),
            child: SizedBox(
              height: 160,
              child: GoogleMap(
                initialCameraPosition: CameraPosition(target: _posicion, zoom: 15),
                markers: _markers,
                myLocationEnabled: false,
                myLocationButtonEnabled: false,
                zoomControlsEnabled: false,
                liteModeEnabled: true,
                onMapCreated: (c) => _mapCtrl = c,
              ),
            ),
          ),
        ],
      ],
    );
  }
}

/// Botones de ruta a domicilio / trabajo para cobradores.
class BotonesRutaCliente extends StatelessWidget {
  const BotonesRutaCliente({
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

  Future<void> _abrir(BuildContext context, double lat, double lng, String tipo) async {
    final ok = await abrirRutaGoogleMaps(latitud: lat, longitud: lng);
    if (!context.mounted) return;
    if (!ok) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('No se pudo abrir Google Maps ($tipo)')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final domicilioOk = coordenadasValidas(latResidencia, lngResidencia);
    final trabajoOk = coordenadasValidas(latTrabajo, lngTrabajo);

    return Row(
      children: [
        Expanded(
          child: OutlinedButton.icon(
            onPressed: domicilioOk
                ? () => _abrir(context, latResidencia!, lngResidencia!, 'domicilio')
                : null,
            icon: const Text('🚪', style: TextStyle(fontSize: 16)),
            label: const Text('Ruta a Domicilio'),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.neonCyan,
              side: BorderSide(color: AppColors.neonCyan.withValues(alpha: 0.5)),
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: OutlinedButton.icon(
            onPressed: trabajoOk
                ? () => _abrir(context, latTrabajo!, lngTrabajo!, 'trabajo')
                : null,
            icon: const Text('💼', style: TextStyle(fontSize: 16)),
            label: const Text('Ruta a Trabajo'),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.amber,
              side: BorderSide(color: AppColors.amber.withValues(alpha: 0.5)),
              padding: const EdgeInsets.symmetric(vertical: 12),
            ),
          ),
        ),
      ],
    );
  }
}
