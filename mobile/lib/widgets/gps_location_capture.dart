import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../theme/app_theme.dart';
import '../utils/maps_navigation.dart';
import '../screens/cliente_form_screen.dart';

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
    this.direccionResidencia,
    this.direccionTrabajo,
    this.clienteId,
    this.destacados = false,
  });

  final double? latResidencia;
  final double? lngResidencia;
  final double? latTrabajo;
  final double? lngTrabajo;
  final String? direccionResidencia;
  final String? direccionTrabajo;
  final String? clienteId;
  final bool destacados;

  Future<void> _iniciarRuta(
    BuildContext context, {
    required String tipo,
    required String emoji,
    double? lat,
    double? lng,
    String? direccion,
  }) async {
    if (coordenadasValidas(lat, lng)) {
      final ok = await abrirRutaGoogleMaps(latitud: lat!, longitud: lng!);
      if (!context.mounted) return;
      if (!ok) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('No se pudo abrir Google Maps ($tipo)')),
        );
      }
      return;
    }

    final dir = direccion?.trim() ?? '';
    if (!context.mounted) return;

    await showDialog<void>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: Text('$emoji Sin GPS — $tipo'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              dir.isNotEmpty
                  ? 'Este cliente aún no tiene coordenadas GPS registradas para $tipo.'
                  : 'No hay coordenadas GPS ni dirección de texto para $tipo.',
              style: const TextStyle(height: 1.4),
            ),
            if (dir.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text('Dirección registrada:', style: TextStyle(fontSize: 12, color: AppColors.textMuted)),
              const SizedBox(height: 4),
              Text(dir, style: const TextStyle(fontWeight: FontWeight.w700)),
            ],
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
          if (dir.isNotEmpty)
            FilledButton.icon(
              onPressed: () async {
                Navigator.pop(ctx);
                final ok = await abrirRutaPorDireccion(dir);
                if (!context.mounted) return;
                if (!ok) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('No se pudo abrir Maps con la dirección de $tipo')),
                  );
                }
              },
              icon: const Icon(Icons.map_outlined, size: 18),
              label: const Text('Usar dirección'),
            ),
          if (clienteId != null)
            OutlinedButton.icon(
              onPressed: () async {
                Navigator.pop(ctx);
                try {
                  final detalle = await context.read<AppState>().clientes.obtener(clienteId!);
                  if (!context.mounted) return;
                  final ok = await Navigator.push<bool>(
                    context,
                    MaterialPageRoute(
                      builder: (_) => ClienteFormScreen(cliente: detalle),
                    ),
                  );
                  if (ok == true && context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Cliente actualizado — vuelve a intentar la ruta')),
                    );
                  }
                } catch (e) {
                  if (context.mounted) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('$e'), backgroundColor: Colors.red),
                    );
                  }
                }
              },
              icon: const Icon(Icons.edit_location_alt_outlined, size: 18),
              label: const Text('Marcar en mapa'),
            ),        ],
      ),
    );
  }

  Widget _boton({
    required BuildContext context,
    required String emoji,
    required String label,
    required Color color,
    required VoidCallback onPressed,
  }) {
    if (destacados) {
      return FilledButton.icon(
        onPressed: onPressed,
        icon: Text(emoji, style: const TextStyle(fontSize: 18)),
        label: Text(label),
        style: FilledButton.styleFrom(
          backgroundColor: color,
          foregroundColor: AppColors.bgDeep,
          minimumSize: const Size(double.infinity, 48),
          padding: const EdgeInsets.symmetric(vertical: 14),
        ),
      );
    }

    return Expanded(
      child: OutlinedButton.icon(
        onPressed: onPressed,
        icon: Text(emoji, style: const TextStyle(fontSize: 16)),
        label: Text(label),
        style: OutlinedButton.styleFrom(
          foregroundColor: color,
          side: BorderSide(color: color.withValues(alpha: 0.5)),
          padding: const EdgeInsets.symmetric(vertical: 12),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (destacados) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          _boton(
            context: context,
            emoji: '🏠',
            label: 'Ruta Domicilio',
            color: AppColors.neonCyan,
            onPressed: () => _iniciarRuta(
              context,
              tipo: 'domicilio',
              emoji: '🏠',
              lat: latResidencia,
              lng: lngResidencia,
              direccion: direccionResidencia,
            ),
          ),
          const SizedBox(height: 10),
          _boton(
            context: context,
            emoji: '💼',
            label: 'Ruta Trabajo',
            color: AppColors.amber,
            onPressed: () => _iniciarRuta(
              context,
              tipo: 'trabajo',
              emoji: '💼',
              lat: latTrabajo,
              lng: lngTrabajo,
              direccion: direccionTrabajo,
            ),
          ),
        ],
      );
    }

    return Row(
      children: [
        _boton(
          context: context,
          emoji: '🏠',
          label: 'Ruta Domicilio',
          color: AppColors.neonCyan,
          onPressed: () => _iniciarRuta(
            context,
            tipo: 'domicilio',
            emoji: '🏠',
            lat: latResidencia,
            lng: lngResidencia,
            direccion: direccionResidencia,
          ),
        ),
        const SizedBox(width: 10),
        _boton(
          context: context,
          emoji: '💼',
          label: 'Ruta Trabajo',
          color: AppColors.amber,
          onPressed: () => _iniciarRuta(
            context,
            tipo: 'trabajo',
            emoji: '💼',
            lat: latTrabajo,
            lng: lngTrabajo,
            direccion: direccionTrabajo,
          ),
        ),
      ],
    );
  }
}
