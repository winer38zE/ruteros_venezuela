import 'package:flutter/material.dart';
import 'package:google_maps_flutter/google_maps_flutter.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../providers/app_state.dart';
import '../services/cobros_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_list_tile.dart';

/// Puntos de cobro del día para dueño y administrador. No es rastreo continuo.
class SeguimientoRutasScreen extends StatefulWidget {
  const SeguimientoRutasScreen({super.key});

  @override
  State<SeguimientoRutasScreen> createState() => _SeguimientoRutasScreenState();
}

class _SeguimientoRutasScreenState extends State<SeguimientoRutasScreen> {
  List<CobradorOpcion> _cobradores = [];
  String? _cobradorId;
  DateTime _fecha = DateTime.now();
  SeguimientoRuta? _ruta;
  bool _cargando = true;
  String? _error;
  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _hora = DateFormat('HH:mm');

  @override
  void initState() {
    super.initState();
    _cargarCobradores();
  }

  String get _fechaIso => DateFormat('yyyy-MM-dd').format(_fecha);

  Future<void> _cargarCobradores() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final lista = await context.read<AppState>().cobros.cobradoresSeguimiento();
      if (!mounted) return;
      setState(() {
        _cobradores = lista;
        _cobradorId ??= lista.isEmpty ? null : lista.first.id;
      });
      await _cargarRuta();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = '$e';
        _cargando = false;
      });
    }
  }

  Future<void> _cargarRuta() async {
    final id = _cobradorId;
    if (id == null) {
      setState(() {
        _ruta = null;
        _cargando = false;
      });
      return;
    }
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final ruta = await context.read<AppState>().cobros.seguimiento(
            cobradorId: id,
            fecha: _fechaIso,
          );
      if (!mounted) return;
      setState(() => _ruta = ruta);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _elegirFecha() async {
    final elegida = await showDatePicker(
      context: context,
      initialDate: _fecha,
      firstDate: DateTime(2024),
      lastDate: DateTime.now().add(const Duration(days: 1)),
    );
    if (elegida == null) return;
    setState(() => _fecha = elegida);
    await _cargarRuta();
  }

  String _horaDe(String iso) {
    final momento = DateTime.tryParse(iso);
    if (momento == null) return iso.length >= 16 ? iso.substring(11, 16) : iso;
    return _hora.format(momento.toLocal());
  }

  @override
  Widget build(BuildContext context) {
    final puntos = _ruta?.puntos ?? [];
    final conGps = puntos.where((p) => !p.sinUbicacion && p.latitud != null && p.longitud != null).toList();
    final camara = conGps.isEmpty
        ? const CameraPosition(target: LatLng(10.4806, -66.9036), zoom: 11)
        : CameraPosition(target: LatLng(conGps.first.latitud!, conGps.first.longitud!), zoom: 14);

    return FuturisticScaffold(
      title: 'Seguimiento de rutas',
      accentColor: AppColors.neonCyan,
      actions: [
        IconButton(onPressed: _elegirFecha, icon: const Icon(Icons.calendar_month_rounded)),
        IconButton(onPressed: _cargarRuta, icon: const Icon(Icons.refresh_rounded)),
      ],
      body: ListView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        children: [
          DropdownButtonFormField<String>(
            value: _cobradorId,
            decoration: const InputDecoration(labelText: 'Cobrador'),
            items: _cobradores
                .map((c) => DropdownMenuItem(value: c.id, child: Text(c.nombre)))
                .toList(),
            onChanged: (id) {
              setState(() => _cobradorId = id);
              _cargarRuta();
            },
          ),
          const SizedBox(height: 8),
          Text('Fecha $_fechaIso · puntos de cobro, no ubicación continua'),
          const SizedBox(height: 12),
          if (_cargando) const LinearProgressIndicator(),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))),
            ),
          SizedBox(
            height: 260,
            child: ClipRRect(
              borderRadius: BorderRadius.circular(16),
              child: GoogleMap(
                key: ValueKey('$_cobradorId-$_fechaIso-${conGps.length}'),
                initialCameraPosition: camara,
                markers: {
                  for (var i = 0; i < conGps.length; i++)
                    Marker(
                      markerId: MarkerId(conGps[i].cobroId),
                      position: LatLng(conGps[i].latitud!, conGps[i].longitud!),
                      infoWindow: InfoWindow(
                        title: conGps[i].clienteNombre,
                        snippet: _fmt.format(conGps[i].montoUsd),
                      ),
                    ),
                },
                polylines: {
                  if (conGps.length >= 2)
                    Polyline(
                      polylineId: const PolylineId('recorrido'),
                      color: AppColors.neonCyan,
                      width: 4,
                      points: [for (final p in conGps) LatLng(p.latitud!, p.longitud!)],
                    ),
                },
              ),
            ),
          ),
          const SizedBox(height: 16),
          if (puntos.isEmpty && !_cargando)
            const EmptyState(
              icon: Icons.route_rounded,
              message: 'No hay cobros en esa fecha',
            )
          else
            ...puntos.map((p) {
              return GlassListTile(
                accentColor: p.sinUbicacion ? AppColors.amber : AppColors.neonCyan,
                title: Text(p.clienteNombre),
                subtitle: Text(
                  '${_horaDe(p.fecha)} · ${_fmt.format(p.montoUsd)} · ${p.metodo}'
                  '${p.sinUbicacion ? ' · sin ubicación' : ''}',
                ),
              );
            }),
        ],
      ),
    );
  }
}
