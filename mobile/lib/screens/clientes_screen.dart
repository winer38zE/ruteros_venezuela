import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../local/cliente_local.dart';
import '../local/isar_db.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';
import '../services/clientes_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_list_tile.dart';
import 'cliente_detalle_screen.dart';
import 'cliente_form_screen.dart';

/// Listado que pinta primero lo guardado en el teléfono.
class ClientesScreen extends StatefulWidget {
  const ClientesScreen({super.key});

  @override
  State<ClientesScreen> createState() => _ClientesScreenState();
}

class _ClientesScreenState extends State<ClientesScreen> {
  final _searchCtrl = TextEditingController();
  String _busqueda = '';
  Future<List<ClienteDetalle>>? _futuroRed;
  Stream<List<ClienteLocal>>? _streamLocal;

  bool get _isarLista => isarInstance != null && isarInstance!.isOpen;

  @override
  void initState() {
    super.initState();
    if (_isarLista) {
      _streamLocal = context.read<AppState>().sync.observarClientes();
    } else {
      _futuroRed = _cargarRed();
    }
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<List<ClienteDetalle>> _cargarRed() {
    return context.read<AppState>().clientes.listar(
          busqueda: _busqueda.isEmpty ? null : _busqueda,
        );
  }

  /// Deslizar la lista: comprueba la red y solo entonces pide el catálogo fresco.
  Future<void> _alDeslizar() async {
    final online = await context.read<AppState>().sync.hayRed();
    if (!mounted) return;
    if (!online) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Trabajando sin conexión - Mostrando datos locales')),
      );
      return;
    }
    await _refrescar();
  }

  Future<void> _refrescar({bool avisar = true}) async {
    try {
      if (_isarLista) {
        await context.read<AppState>().sync.sincronizar(manual: true);
      } else if (mounted) {
        setState(() => _futuroRed = _cargarRed());
        await _futuroRed;
      }
    } catch (e) {
      if (!avisar || !mounted) return;
      final texto = e is ApiException ? e.message : '$e';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(texto), backgroundColor: const Color(0xFFEF4444)),
      );
    }
  }

  bool _coincideLocal(ClienteLocal c) {
    final q = _busqueda.trim().toLowerCase();
    if (q.isEmpty) return true;
    return (c.nombre ?? '').toLowerCase().contains(q) ||
        (c.cedula ?? '').toLowerCase().contains(q) ||
        (c.telefono ?? '').toLowerCase().contains(q);
  }

  bool _soloContado(int? score, bool? esMoroso) {
    return esMoroso == true || (score != null && score < 50);
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Gestión de Clientes',
      accentColor: AppColors.neonCyan,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: () => _alDeslizar()),
      ],
      floatingActionButton: NeonFab(
        label: 'Nuevo cliente',
        icon: Icons.person_add_rounded,
        color: AppColors.neonCyan,
        onPressed: () async {
          final ok = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const ClienteFormScreen()),
          );
          if (ok == true && mounted) await _refrescar(avisar: false);
        },
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: TextField(
              controller: _searchCtrl,
              onChanged: (v) => setState(() => _busqueda = v),
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: const InputDecoration(
                hintText: 'Buscar por nombre, teléfono o cédula…',
                prefixIcon: Icon(Icons.search_rounded),
              ),
            ),
          ),
          Expanded(child: _isarLista ? _listaLocal() : _listaRed()),
        ],
      ),
    );
  }

  Widget _listaLocal() {
    return StreamBuilder<List<ClienteLocal>>(
      stream: _streamLocal,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting && !snapshot.hasData) {
          return const Center(child: CircularProgressIndicator());
        }
        final todos = List<ClienteLocal>.from(snapshot.data ?? []);
        todos.sort(
          (a, b) => (a.nombre ?? '').toLowerCase().compareTo((b.nombre ?? '').toLowerCase()),
        );
        final visibles = todos.where(_coincideLocal).toList();
        final pendientes = todos.where((c) => !c.sincronizado).length;
        return Column(
          children: [
            if (pendientes > 0)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 10, 16, 0),
                child: Text(
                  pendientes == 1
                      ? '1 cliente pendiente por subir'
                      : '$pendientes clientes pendientes por subir',
                  style: const TextStyle(color: AppColors.amber),
                ),
              ),
            Expanded(
              child: RefreshIndicator(
                onRefresh: _alDeslizar,
                child: visibles.isEmpty
                    ? ListView(
                        physics: const AlwaysScrollableScrollPhysics(),
                        children: const [
                          SizedBox(height: 80),
                          EmptyState(
                            icon: Icons.people_outline_rounded,
                            message: 'Sin clientes en el teléfono. Desliza para sincronizar.',
                          ),
                        ],
                      )
                    : ListView.builder(
                        physics: const AlwaysScrollableScrollPhysics(),
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                        itemCount: visibles.length,
                        itemBuilder: (context, index) => _tarjetaLocal(visibles[index]),
                      ),
              ),
            ),
          ],
        );
      },
    );
  }

  Widget _tarjetaLocal(ClienteLocal c) {
    final bloqueado = _soloContado(c.score, c.esMoroso);
    final vencido = c.creditoVencido || c.esMoroso == true;
    final color = vencido
        ? Colors.redAccent
        : bloqueado
            ? AppColors.amber
            : AppColors.neonCyan;
    final idServidor = c.servidorId;
    return GlassListTile(
      accentColor: color,
      onTap: () async {
        if (idServidor == null || idServidor.isEmpty) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(c.errorSync ?? 'Este cliente aún no está en el servidor.'),
            ),
          );
          return;
        }
        await Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => ClienteDetalleScreen(clienteId: idServidor)),
        );
        if (mounted) await _refrescar(avisar: false);
      },
      leading: Icon(
        vencido ? Icons.block_rounded : Icons.person_rounded,
        color: color,
      ),
      title: Text(c.nombre?.isNotEmpty == true ? c.nombre! : 'Sin nombre'),
      subtitle: Text(
        [
          if ((c.cedula ?? '').isNotEmpty) c.cedula!,
          if ((c.telefono ?? '').isNotEmpty) c.telefono!,
          if (c.creditoVencido) 'Vencido',
          if (c.esMoroso == true && !c.creditoVencido) 'Moroso',
          if (!vencido && bloqueado) 'Solo contado',
        ].join(' · '),
      ),
      trailing: _iconoSync(c.sincronizado),
    );
  }

  Widget _iconoSync(bool sincronizado) {
    return Icon(
      sincronizado ? Icons.cloud_done_rounded : Icons.cloud_upload_rounded,
      color: sincronizado ? AppColors.emerald : AppColors.amber,
    );
  }

  Widget _listaRed() {
    return FutureBuilder<List<ClienteDetalle>>(
      future: _futuroRed,
      builder: (context, snapshot) {
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(
            child: Text('${snapshot.error}', style: const TextStyle(color: Color(0xFFEF4444))),
          );
        }
        final q = _busqueda.trim().toLowerCase();
        final clientes = (snapshot.data ?? []).where((c) {
          if (q.isEmpty) return true;
          return c.nombre.toLowerCase().contains(q) ||
              c.identificacion.toLowerCase().contains(q) ||
              (c.telefono ?? '').toLowerCase().contains(q);
        }).toList();
        return RefreshIndicator(
          onRefresh: _alDeslizar,
          child: clientes.isEmpty
              ? ListView(
                  physics: const AlwaysScrollableScrollPhysics(),
                  children: const [
                    SizedBox(height: 80),
                    EmptyState(icon: Icons.people_outline_rounded, message: 'Sin clientes registrados'),
                  ],
                )
              : ListView.builder(
                  physics: const AlwaysScrollableScrollPhysics(),
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                  itemCount: clientes.length,
                  itemBuilder: (context, index) {
                    final c = clientes[index];
                    final color = c.esMoroso
                        ? const Color(0xFFEF4444)
                        : c.soloContado
                            ? AppColors.amber
                            : AppColors.neonCyan;
                    return GlassListTile(
                      accentColor: color,
                      onTap: () async {
                        await Navigator.push(
                          context,
                          MaterialPageRoute(builder: (_) => ClienteDetalleScreen(clienteId: c.id)),
                        );
                        if (mounted) await _refrescar(avisar: false);
                      },
                      leading: Icon(
                        c.esMoroso ? Icons.block_rounded : Icons.person_rounded,
                        color: color,
                      ),
                      title: Text(c.nombre),
                      subtitle: Text(
                        [
                          c.identificacion,
                          c.telefono ?? 'Sin tel.',
                          if (c.esMoroso) 'Moroso',
                          if (!c.esMoroso && c.soloContado) 'Solo contado',
                        ].join(' · '),
                      ),
                      trailing: _iconoSync(true),
                    );
                  },
                ),
        );
      },
    );
  }
}
