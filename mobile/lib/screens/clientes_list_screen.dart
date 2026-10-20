import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../l10n/regional_copy.dart';
import '../providers/app_state.dart';
import '../services/clientes_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/score_badge.dart';
import 'cliente_detalle_screen.dart';
import 'cliente_form_screen.dart';

class ClientesListScreen extends StatefulWidget {
  const ClientesListScreen({super.key});

  @override
  State<ClientesListScreen> createState() => _ClientesListScreenState();
}

class _ClientesListScreenState extends State<ClientesListScreen> {
  List<ClienteDetalle> _clientes = [];
  bool _cargando = true;
  String? _error;
  final _searchCtrl = TextEditingController();
  String _busqueda = '';

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      _clientes = await context.read<AppState>().clientes.listar(
            busqueda: _busqueda.isEmpty ? null : _busqueda,
          );
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  void _onBuscar(String value) {
    setState(() => _busqueda = value);
    _cargar();
  }

  Future<void> _nuevoCliente() async {
    final ok = await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => const ClienteFormScreen()),
    );
    if (ok == true) _cargar();
  }

  @override
  Widget build(BuildContext context) {
    final copy = RegionalCopy.fromEsVenezuela(context.watch<AppState>().esVenezuela);
    return FuturisticScaffold(
      title: 'Gestión de Clientes',
      accentColor: AppColors.neonCyan,
      actions: [IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar)],
      floatingActionButton: NeonFab(
        label: 'Nuevo cliente',
        icon: Icons.person_add_rounded,
        color: AppColors.neonCyan,
        onPressed: _nuevoCliente,
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
            child: TextField(
              controller: _searchCtrl,
              onSubmitted: _onBuscar,
              onChanged: (v) {
                if (v.isEmpty) _onBuscar('');
              },
              style: const TextStyle(color: AppColors.textPrimary),
              decoration: InputDecoration(
                hintText: 'Buscar por nombre, teléfono o cédula…',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.search),
                  onPressed: () => _onBuscar(_searchCtrl.text),
                ),
              ),
            ),
          ),
          Expanded(
            child: _cargando
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
                    : RefreshIndicator(
                        onRefresh: _cargar,
                        child: _clientes.isEmpty
                            ? ListView(
                                children: [
                                  const SizedBox(height: 80),
                                  EmptyState(
                                    icon: Icons.people_outline_rounded,
                                    message: copy.emptyClientesTitulo,
                                    detail: copy.emptyClientesDetalle,
                                    actionLabel: 'Crear cliente',
                                    onAction: _nuevoCliente,
                                  ),
                                ],
                              )
                            : ListView.builder(
                                padding: const EdgeInsets.fromLTRB(16, 12, 16, 100),
                                itemCount: _clientes.length,
                                itemBuilder: (context, index) {
                                  final c = _clientes[index];
                                  final color = scoreColor(c);
                                  return GlassListTile(
                                    accentColor: color,
                                    onTap: () async {
                                      await Navigator.push(
                                        context,
                                        MaterialPageRoute(builder: (_) => ClienteDetalleScreen(clienteId: c.id)),
                                      );
                                      _cargar();
                                    },
                                    leading: Icon(Icons.person_rounded, color: color),
                                    title: Text(c.nombre),
                                    subtitle: Text('${c.identificacion} · ${c.telefono ?? "Sin tel."}'),
                                    trailing: ScoreBadge(score: c.scoreCredito, estado: c.estadoCredito, compact: true),
                                  );
                                },
                              ),
                      ),
          ),
        ],
      ),
    );
  }
}
