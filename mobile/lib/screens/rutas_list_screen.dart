import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/rutas_service.dart';
import '../theme/app_theme.dart';
import '../utils/maps_navigation.dart';
import '../utils/route_estimator.dart';
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
  bool _guardandoOrden = false;
  bool _modoReordenar = false;
  String? _error;
  String _dia = RutasService.diaActual();
  int _visitados = 0;
  int _pendientes = 0;

  static const _dias = RutasService.dias;

  static const _diasLabel = RutasService.diasLabel;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final state = context.read<AppState>();
      final uid = state.usuario?.id;
      if (uid != null) {
        await state.rutas.sincronizarPendientes(uid);
      }
      final result = await state.rutas.rutaDelDia(
        vendedorId: uid,
        dia: _dia,
        fecha: RutasService.fechaActual(),
      );
      _clientes = RutasService.soloDia(result.clientes, _dia);
      _visitados = _clientes.where((c) => c.visitado).length;
      _pendientes = _clientes.where((c) => c.pendiente).length;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  int? get _siguientePendienteIndex {
    for (var i = 0; i < _clientes.length; i++) {
      if (_clientes[i].pendiente) return i;
    }
    return null;
  }

  String? _distanciaDesdeAnterior(int index) {
    if (index <= 0) return null;
    final anterior = _clientes[index - 1];
    final actual = _clientes[index];
    if (!anterior.tieneGps || !actual.tieneGps) return null;
    final km = distanciaKm(
      anterior.latitud!,
      anterior.longitud!,
      actual.latitud!,
      actual.longitud!,
    );
    return formatearDistancia(km);
  }

  void _onReorder(int oldIndex, int newIndex) {
    setState(() {
      if (newIndex > oldIndex) newIndex -= 1;
      final item = _clientes.removeAt(oldIndex);
      _clientes.insert(newIndex, item);
      _clientes = [
        for (var i = 0; i < _clientes.length; i++)
          _clientes[i].copyWith(ordenSecuencial: i + 1),
      ];
    });
  }

  Future<void> _guardarOrden() async {
    setState(() => _guardandoOrden = true);
    try {
      final state = context.read<AppState>();
      final result = await state.rutas.reordenar(
        dia: _dia,
        clientes: _clientes,
        vendedorId: state.usuario?.id,
      );
      setState(() {
        _clientes = RutasService.soloDia(result.clientes, _dia);
        _visitados = _clientes.where((c) => c.visitado).length;
        _pendientes = _clientes.where((c) => c.pendiente).length;
        _modoReordenar = false;
      });
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Orden guardado correctamente')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al guardar: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _guardandoOrden = false);
    }
  }

  Future<void> _marcarVisitado(int index, {String estado = 'visitado'}) async {
    final cliente = _clientes[index];
    if (cliente.visitado && estado == 'visitado') return;

    setState(() {
      _clientes[index] = cliente.copyWith(
        estadoVisita: estado,
        marcadoEn: DateTime.now(),
      );
      _visitados = _clientes.where((c) => c.visitado).length;
      _pendientes = _clientes.where((c) => c.pendiente).length;
    });

    final state = context.read<AppState>();
    final uid = state.usuario?.id;
    if (uid == null) return;

    try {
      await state.rutas.marcarVisita(
        clienteId: cliente.id,
        estado: estado,
        vendedorId: uid,
        fecha: RutasService.fechaActual(),
      );
    } catch (_) {
      final ok = await state.rutas.marcarVisitaConOffline(
        usuarioId: uid,
        clienteId: cliente.id,
        estado: estado,
        vendedorId: uid,
        fecha: RutasService.fechaActual(),
      );
      if (!ok && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Guardado localmente — se sincronizará al reconectar')),
        );
      }
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
      title: _modoReordenar ? 'Reordenar Ruta' : 'Ruta del Día',
      accentColor: AppColors.neonCyan,
      actions: [
        if (_clientes.isNotEmpty)
          IconButton(
            tooltip: _modoReordenar ? 'Salir de reordenar' : 'Reordenar ruta',
            icon: Icon(_modoReordenar ? Icons.close_rounded : Icons.swap_vert_rounded),
            onPressed: () => setState(() => _modoReordenar = !_modoReordenar),
          ),
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      floatingActionButton: _modoReordenar
          ? FloatingActionButton.extended(
              onPressed: _guardandoOrden ? null : _guardarOrden,
              backgroundColor: AppColors.amber,
              icon: _guardandoOrden
                  ? const SizedBox(
                      width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.black),
                    )
                  : const Icon(Icons.save_rounded, color: Colors.black),
              label: Text(
                _guardandoOrden ? 'Guardando…' : 'Guardar orden',
                style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w700),
              ),
            )
          : siguienteIdx != null
              ? FloatingActionButton.extended(
                  onPressed: () => _abrirGps(_clientes[siguienteIdx]),
                  backgroundColor: AppColors.neonCyan,
                  icon: const Icon(Icons.navigation_rounded, color: Colors.black),
                  label: Text(
                    'GPS parada ${_clientes[siguienteIdx].ordenRuta}',
                    style: const TextStyle(color: Colors.black, fontWeight: FontWeight.w700),
                  ),
                )
              : null,
      body: Column(
        children: [
          _buildHeader(siguienteIdx),
          Expanded(
            child: _cargando
                ? const Center(child: CircularProgressIndicator(color: AppColors.neonCyan))
                : _error != null
                    ? _buildError()
                    : _clientes.isEmpty
                        ? _buildEmpty()
                        : _modoReordenar
                            ? _buildListaReordenable()
                            : _buildListaNormal(siguienteIdx),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(int? siguienteIdx) {
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
                final hoy = d == RutasService.diaActual();
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: FilterChip(
                    label: Text('${_diasLabel[d] ?? d}${hoy ? ' · Hoy' : ''}'),
                    selected: sel,
                    onSelected: _modoReordenar
                        ? null
                        : (_) {
                            setState(() => _dia = d);
                            _cargar();
                          },
                    selectedColor: AppColors.neonCyan.withValues(alpha: 0.25),
                    checkmarkColor: AppColors.neonCyan,
                    labelStyle: TextStyle(
                      color: sel ? AppColors.neonCyan : AppColors.textMuted,
                      fontWeight: sel ? FontWeight.w700 : FontWeight.w500,
                    ),
                    side: BorderSide(color: sel ? AppColors.neonCyan : AppColors.glassBorder),
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
                Icon(
                  _modoReordenar ? Icons.drag_handle_rounded : Icons.route_rounded,
                  color: _modoReordenar ? AppColors.amber : AppColors.neonCyan,
                  size: 20,
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    _modoReordenar
                        ? 'Arrastra el recorrido de ${_diasLabel[_dia]} · ${_clientes.length} paradas'
                        : 'Solo ${_diasLabel[_dia]} · orden GPS · $_visitados visitados · $_pendientes pendientes',
                    style: const TextStyle(color: AppColors.textPrimary, fontWeight: FontWeight.w600),
                  ),
                ),
                if (!_modoReordenar && siguienteIdx != null)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppColors.amber.withValues(alpha: 0.15),
                      borderRadius: BorderRadius.circular(20),
                      border: Border.all(color: AppColors.amber.withValues(alpha: 0.5)),
                    ),
                    child: Text(
                      'Siguiente: ${_clientes[siguienteIdx].ordenRuta}',
                      style: const TextStyle(color: AppColors.amber, fontSize: 12, fontWeight: FontWeight.w700),
                    ),
                  ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildListaNormal(int? siguienteIdx) {
    return RefreshIndicator(
      onRefresh: _cargar,
      color: AppColors.neonCyan,
      child: ListView.builder(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
        itemCount: _clientes.length,
        itemBuilder: (ctx, i) => _TarjetaClienteRuta(
        key: ValueKey(_clientes[i].id),
        index: i,
        cliente: _clientes[i],
          esSiguiente: i == siguienteIdx,
          modoReordenar: false,
          distanciaAnterior: _distanciaDesdeAnterior(i),
          onMarcarVisitado: () => _marcarVisitado(i),
          onNoEncontrado: () => _marcarVisitado(i, estado: 'no_encontrado'),
          onAbrirGps: () => _abrirGps(_clientes[i]),
        ),
      ),
    );
  }

  Widget _buildListaReordenable() {
    return ReorderableListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
      itemCount: _clientes.length,
      onReorder: _onReorder,
        itemBuilder: (ctx, i) => _TarjetaClienteRuta(
        key: ValueKey(_clientes[i].id),
        index: i,
        cliente: _clientes[i],
        esSiguiente: false,
        modoReordenar: true,
        distanciaAnterior: null,
        onMarcarVisitado: () {},
        onNoEncontrado: () {},
        onAbrirGps: () {},
      ),
    );
  }

  Widget _buildError() => Center(
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

  Widget _buildEmpty() => Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.map_outlined, size: 64, color: AppColors.textMuted.withValues(alpha: 0.5)),
              const SizedBox(height: 16),
              Text(
                'Sin clientes en el recorrido de ${_diasLabel[_dia]}',
                textAlign: TextAlign.center,
                style: const TextStyle(color: AppColors.textMuted, fontSize: 16),
              ),
            ],
          ),
        ),
      );
}

class _TarjetaClienteRuta extends StatelessWidget {
  const _TarjetaClienteRuta({
    super.key,
    required this.index,
    required this.cliente,
    required this.esSiguiente,
    required this.modoReordenar,
    required this.distanciaAnterior,
    required this.onMarcarVisitado,
    required this.onNoEncontrado,
    required this.onAbrirGps,
  });

  final int index;
  final ClienteRuta cliente;
  final bool esSiguiente;
  final bool modoReordenar;
  final String? distanciaAnterior;
  final VoidCallback onMarcarVisitado;
  final VoidCallback onNoEncontrado;
  final VoidCallback onAbrirGps;

  @override
  Widget build(BuildContext context) {
    final visitado = cliente.visitado;
    final noEnc = cliente.noEncontrado;

    Color borderColor;
    if (modoReordenar) {
      borderColor = AppColors.amber.withValues(alpha: 0.5);
    } else if (esSiguiente) {
      borderColor = AppColors.amber;
    } else if (visitado) {
      borderColor = AppColors.emerald.withValues(alpha: 0.4);
    } else if (noEnc) {
      borderColor = Colors.orange.withValues(alpha: 0.5);
    } else {
      borderColor = AppColors.glassBorder;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: borderColor, width: esSiguiente ? 2 : 1),
          boxShadow: esSiguiente
              ? [BoxShadow(color: AppColors.amber.withValues(alpha: 0.25), blurRadius: 12, spreadRadius: 1)]
              : null,
        ),
        child: GlassContainer(
          padding: const EdgeInsets.all(14),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (modoReordenar) ...[
                ReorderableDragStartListener(
                  index: index,
                  child: const Padding(
                    padding: EdgeInsets.only(right: 8, top: 8),
                    child: Icon(Icons.drag_handle_rounded, color: AppColors.amber),
                  ),
                ),
              ],
              _buildOrden(),
              const SizedBox(width: 12),
              Expanded(child: _buildInfo()),
              if (!modoReordenar) ...[
                const SizedBox(width: 8),
                _buildAcciones(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildOrden() {
    final color = cliente.visitado
        ? AppColors.emerald
        : cliente.noEncontrado
            ? Colors.orange
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
        '${cliente.ordenRuta}.',
        style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 15),
      ),
    );
  }

  Widget _buildInfo() {
    String estadoLabel;
    Color estadoColor;
    IconData estadoIcon;

    if (cliente.visitado) {
      estadoLabel = 'Visitado';
      estadoColor = AppColors.emerald;
      estadoIcon = Icons.check_circle_rounded;
    } else if (cliente.noEncontrado) {
      estadoLabel = 'No encontrado';
      estadoColor = Colors.orange;
      estadoIcon = Icons.location_off_rounded;
    } else {
      estadoLabel = 'Pendiente';
      estadoColor = AppColors.textMuted;
      estadoIcon = Icons.radio_button_unchecked;
    }

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
        if (cliente.direccion != null && cliente.direccion!.isNotEmpty) ...[
          const SizedBox(height: 4),
          Text(
            cliente.direccion!,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
          ),
        ],
        if (distanciaAnterior != null) ...[
          const SizedBox(height: 4),
          Text(
            '$distanciaAnterior desde la parada anterior',
            style: const TextStyle(color: AppColors.neonCyan, fontSize: 12, fontWeight: FontWeight.w600),
          ),
        ],
        const SizedBox(height: 6),
        Row(
          children: [
            Icon(estadoIcon, size: 16, color: estadoColor),
            const SizedBox(width: 4),
            Text(estadoLabel, style: TextStyle(color: estadoColor, fontSize: 12, fontWeight: FontWeight.w600)),
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
                  style: TextStyle(color: AppColors.amber, fontSize: 10, fontWeight: FontWeight.w800),
                ),
              ),
            ],
          ],
        ),
      ],
    );
  }

  Widget _buildEtiquetaTipo() {
    final esNuevo = cliente.esNuevo;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: esNuevo ? AppColors.violet.withValues(alpha: 0.2) : AppColors.neonBlue.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: esNuevo ? AppColors.violet.withValues(alpha: 0.6) : AppColors.neonBlue.withValues(alpha: 0.4),
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
          icon: Icon(Icons.navigation_rounded, color: cliente.tieneGps ? AppColors.neonCyan : AppColors.textMuted),
          style: IconButton.styleFrom(backgroundColor: AppColors.neonCyan.withValues(alpha: 0.1)),
        ),
        IconButton(
          tooltip: cliente.visitado ? 'Ya visitado' : 'Marcar visitado',
          onPressed: cliente.visitado ? null : onMarcarVisitado,
          icon: Icon(
            cliente.visitado ? Icons.task_alt_rounded : Icons.check_rounded,
            color: AppColors.emerald,
          ),
          style: IconButton.styleFrom(backgroundColor: AppColors.emerald.withValues(alpha: 0.1)),
        ),
        IconButton(
          tooltip: 'No encontrado',
          onPressed: cliente.visitado || cliente.noEncontrado ? null : onNoEncontrado,
          icon: Icon(Icons.location_off_rounded, color: Colors.orange.withValues(alpha: 0.8)),
          style: IconButton.styleFrom(backgroundColor: Colors.orange.withValues(alpha: 0.1)),
        ),
      ],
    );
  }
}
