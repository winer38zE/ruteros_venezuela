import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../providers/app_state.dart';
import '../services/rutas_service.dart';
import '../theme/app_theme.dart';
import '../utils/maps_navigation.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class RutasListScreen extends StatefulWidget {
  const RutasListScreen({super.key});

  @override
  State<RutasListScreen> createState() => _RutasListScreenState();
}

class _RutasListScreenState extends State<RutasListScreen> {
  List<ClienteRuta> _clientes = [];
  bool _cargando = true;
  String? _error;
  String _dia = RutasService.diaActual();
  final _scrollCtrl = ScrollController();

  static const _dias = [
    'LUNES',
    'MARTES',
    'MIERCOLES',
    'JUEVES',
    'VIERNES',
    'SABADO',
    'DOMINGO',
  ];

  static const _diasLabel = {
    'LUNES': 'Lunes',
    'MARTES': 'Martes',
    'MIERCOLES': 'Miércoles',
    'JUEVES': 'Jueves',
    'VIERNES': 'Viernes',
    'SABADO': 'Sábado',
    'DOMINGO': 'Domingo',
  };

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _scrollCtrl.dispose();
    super.dispose();
  }

  String _claveVisitas() {
    final uid = context.read<AppState>().usuario?.id ?? 'anon';
    final hoy = DateTime.now().toIso8601String().substring(0, 10);
    return 'visitas_ruta_${uid}_$hoy';
  }

  Future<Set<String>> _cargarVisitados() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_claveVisitas());
    if (raw == null) return {};
    final list = jsonDecode(raw) as List;
    return list.map((e) => e.toString()).toSet();
  }

  Future<void> _guardarVisitados(Set<String> ids) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_claveVisitas(), jsonEncode(ids.toList()));
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final state = context.read<AppState>();
      final result = await state.rutas.rutaDelDia(
        vendedorId: state.usuario?.id,
        dia: _dia,
      );
      final visitados = await _cargarVisitados();
      _clientes = result.clientes
          .map((c) => c.copyWith(visitado: visitados.contains(c.id)))
          .toList();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  int? get _siguientePendienteIndex {
    for (var i = 0; i < _clientes.length; i++) {
      if (!_clientes[i].visitado) return i;
    }
    return null;
  }

  int get _visitadosCount => _clientes.where((c) => c.visitado).length;

  Future<void> _marcarVisitado(int index) async {
    final cliente = _clientes[index];
    if (cliente.visitado) return;

    setState(() {
      _clientes[index] = cliente.copyWith(visitado: true);
    });

    final visitados = await _cargarVisitados();
    visitados.add(cliente.id);
    await _guardarVisitados(visitados);

    final nextIdx = _siguientePendienteIndex;
    if (nextIdx != null && _scrollCtrl.hasClients) {
      await Future.delayed(const Duration(milliseconds: 300));
      if (!mounted) return;
      await _scrollCtrl.animateTo(
        nextIdx * 120.0,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeOutCubic,
      );
    }
  }

  Future<void> _abrirGps(ClienteRuta cliente) async {
    if (!cliente.tieneGps) {
      if (cliente.direccion != null && cliente.direccion!.trim().isNotEmpty) {
        await abrirRutaPorDireccion(cliente.direccion!);
      } else if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Sin coordenadas GPS para este cliente')),
        );
      }
      return;
    }
    final ok = await abrirRutaGoogleMaps(
      latitud: cliente.latitud!,
      longitud: cliente.longitud!,
    );
    if (!ok && mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No se pudo abrir Google Maps')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final siguienteIdx = _siguientePendienteIndex;

    return FuturisticScaffold(
      title: 'Ruta del Día',
      accentColor: AppColors.neonCyan,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      body: Column(
        children: [
          _buildHeader(),
          Expanded(
            child: _cargando
                ? const Center(child: CircularProgressIndicator(color: AppColors.neonCyan))
                : _error != null
                    ? _buildError()
                    : _clientes.isEmpty
                        ? _buildEmpty()
                        : RefreshIndicator(
                            onRefresh: _cargar,
                            color: AppColors.neonCyan,
                            child: ListView.builder(
                              controller: _scrollCtrl,
                              padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                              itemCount: _clientes.length,
                              itemBuilder: (ctx, i) => _TarjetaClienteRuta(
                                cliente: _clientes[i],
                                esSiguiente: i == siguienteIdx,
                                onMarcarVisitado: () => _marcarVisitado(i),
                                onAbrirGps: () => _abrirGps(_clientes[i]),
                              ),
                            ),
                          ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 4),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: _dias.map((d) {
                final sel = d == _dia;
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text(_diasLabel[d] ?? d),
                    selected: sel,
                    onSelected: (_) {
                      setState(() => _dia = d);
                      _cargar();
                    },
                    selectedColor: AppColors.neonCyan.withValues(alpha: 0.25),
                    checkmarkColor: AppColors.neonCyan,
                    labelStyle: TextStyle(
                      color: sel ? AppColors.neonCyan : AppColors.textMuted,
                      fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
                    ),
                    side: BorderSide(
                      color: sel ? AppColors.neonCyan : AppColors.glassBorder,
                    ),
                  ),
                );
              }).toList(),
            ),
          ),
          const SizedBox(height: 10),
          GlassContainer(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: [
                Icon(Icons.route_rounded, color: AppColors.neonCyan, size: 20),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    '${_diasLabel[_dia]} · $_visitadosCount/${_clientes.length} visitados',
                    style: const TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
                if (_siguientePendienteIndex != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.amber.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.amber.withValues(alpha: 0.5)),
                    ),
                    child: Text(
                      'Siguiente: ${_clientes[_siguientePendienteIndex!].ordenSecuencial}',
                      style: const TextStyle(
                        color: AppColors.amber,
                        fontSize: 12,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, color: Colors.red, size: 48),
            const SizedBox(height: 12),
            Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: AppColors.textMuted)),
            const SizedBox(height: 16),
            FilledButton(onPressed: _cargar, child: const Text('Reintentar')),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.map_outlined, size: 64, color: AppColors.textMuted.withValues(alpha: 0.5)),
            const SizedBox(height: 16),
            Text(
              'Sin clientes en la ruta de ${_diasLabel[_dia]}',
              textAlign: TextAlign.center,
              style: const TextStyle(color: AppColors.textMuted, fontSize: 16),
            ),
            const SizedBox(height: 8),
            const Text(
              'Asigna dia_visita y orden_secuencial a tus clientes, o registra uno nuevo en calle.',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textMuted, fontSize: 13),
            ),
          ],
        ),
      ),
    );
  }
}

class _TarjetaClienteRuta extends StatelessWidget {
  const _TarjetaClienteRuta({
    required this.cliente,
    required this.esSiguiente,
    required this.onMarcarVisitado,
    required this.onAbrirGps,
  });

  final ClienteRuta cliente;
  final bool esSiguiente;
  final VoidCallback onMarcarVisitado;
  final VoidCallback onAbrirGps;

  @override
  Widget build(BuildContext context) {
    final visitado = cliente.visitado;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          border: Border.all(
            color: esSiguiente
                ? AppColors.amber
                : visitado
                    ? AppColors.emerald.withValues(alpha: 0.4)
                    : AppColors.glassBorder,
            width: esSiguiente ? 2 : 1,
          ),
          boxShadow: esSiguiente
              ? [
                  BoxShadow(
                    color: AppColors.amber.withValues(alpha: 0.25),
                    blurRadius: 12,
                    spreadRadius: 1,
                  ),
                ]
              : null,
        ),
        child: GlassContainer(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildOrden(),
              const SizedBox(width: 12),
              Expanded(child: _buildInfo()),
              const SizedBox(width: 8),
              _buildAcciones(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOrden() {
    final color = cliente.visitado
        ? AppColors.emerald
        : esSiguiente
            ? AppColors.amber
            : AppColors.neonCyan;

    return Container(
      width: 40,
      height: 40,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        '${cliente.ordenSecuencial}.',
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w800,
          fontSize: 15,
        ),
      ),
    );
  }

  Widget _buildInfo() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                cliente.nombre,
                style: TextStyle(
                  color: cliente.visitado ? AppColors.textMuted : AppColors.textPrimary,
                  fontWeight: FontWeight.w700,
                  fontSize: 15,
                  decoration: cliente.visitado ? TextDecoration.lineThrough : null,
                ),
              ),
            ),
            _buildEtiquetaTipo(),
          ],
        ),
        const SizedBox(height: 4),
        if (cliente.direccion != null && cliente.direccion!.isNotEmpty)
          Text(
            cliente.direccion!,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
          ),
        const SizedBox(height: 6),
        Row(
          children: [
            Icon(
              visitado ? Icons.check_circle_rounded : Icons.radio_button_unchecked,
              size: 16,
              color: visitado ? AppColors.emerald : AppColors.textMuted,
            ),
            const SizedBox(width: 4),
            Text(
              visitado ? 'Visitado' : 'Pendiente',
              style: TextStyle(
                color: visitado ? AppColors.emerald : AppColors.textMuted,
                fontSize: 12,
                fontWeight: FontWeight.w600,
              ),
            ),
            if (esSiguiente) ...[
              const SizedBox(width: 8),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                decoration: BoxDecoration(
                  color: AppColors.amber.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text(
                  'SIGUIENTE',
                  style: TextStyle(
                    color: AppColors.amber,
                    fontSize: 10,
                    fontWeight: FontWeight.w800,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
            ],
          ],
        ),
      ],
    );
  }

  bool get visitado => cliente.visitado;

  Widget _buildEtiquetaTipo() {
    final esNuevo = cliente.esNuevo;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: esNuevo
            ? AppColors.violet.withValues(alpha: 0.2)
            : AppColors.neonBlue.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: esNuevo
              ? AppColors.violet.withValues(alpha: 0.6)
              : AppColors.neonBlue.withValues(alpha: 0.4),
        ),
      ),
      child: Text(
        esNuevo ? 'Cliente Nuevo' : 'Cliente Frecuente',
        style: TextStyle(
          color: esNuevo ? AppColors.violet : AppColors.neonBlue,
          fontSize: 10,
          fontWeight: FontWeight.w700,
        ),
      ),
    );
  }

  Widget _buildAcciones() {
    return Column(
      children: [
        IconButton(
          tooltip: 'Navegar con GPS',
          onPressed: onAbrirGps,
          icon: Icon(
            Icons.navigation_rounded,
            color: cliente.tieneGps ? AppColors.neonCyan : AppColors.textMuted,
          ),
          style: IconButton.styleFrom(
            backgroundColor: AppColors.neonCyan.withValues(alpha: 0.1),
          ),
        ),
        const SizedBox(height: 4),
        IconButton(
          tooltip: visitado ? 'Ya visitado' : 'Marcar visitado',
          onPressed: visitado ? null : onMarcarVisitado,
          icon: Icon(
            visitado ? Icons.task_alt_rounded : Icons.check_rounded,
            color: visitado ? AppColors.emerald : AppColors.emerald.withValues(alpha: 0.8),
          ),
          style: IconButton.styleFrom(
            backgroundColor: AppColors.emerald.withValues(alpha: visitado ? 0.2 : 0.1),
          ),
        ),
      ],
    );
  }
}
