import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/cobros_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/enviar_recibo_button.dart';
import 'nuevo_cobro_screen.dart';
import 'panel_cobranza_screen.dart';

class CobrosListScreen extends StatefulWidget {
  const CobrosListScreen({super.key});

  @override
  State<CobrosListScreen> createState() => _CobrosListScreenState();
}

class _CobrosListScreenState extends State<CobrosListScreen> {
  List<Cobro> _cobros = [];
  bool _cargando = true;
  String? _error;
  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);

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
      _cobros = await context.read<AppState>().cobros.misCobros();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  String _labelMoneda(String m) {
    return CobrosService.monedas.firstWhere((e) => e.$1 == m, orElse: () => (m, m)).$2;
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Mis Cobros',
      accentColor: AppColors.neonCyan,
      actions: [
        IconButton(
          icon: const Icon(Icons.table_chart_rounded),
          tooltip: 'Panel Excel',
          onPressed: () => Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const PanelCobranzaScreen()),
          ),
        ),
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      floatingActionButton: NeonFab(
        label: 'Nuevo Cobro',
        icon: Icons.payments_rounded,
        color: AppColors.neonCyan,
        onPressed: () async {
          final ok = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const NuevoCobroScreen()),
          );
          if (ok == true) _cargar();
        },
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : _cobros.isEmpty
                  ? const EmptyState(
                      icon: Icons.payments_rounded,
                      message: 'No hay cobros registrados',
                    )
                  : RefreshIndicator(
                      onRefresh: _cargar,
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                        children: [
                          SectionTitle(
                            title: 'Historial de cobros',
                            trailing: Text(
                              '${_cobros.length} registros',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                          ..._cobros.map((c) {
                            return GlassListTile(
                              accentColor: AppColors.neonCyan,
                              leading: Container(
                                width: 44,
                                height: 44,
                                decoration: BoxDecoration(
                                  color: AppColors.neonCyan.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: AppColors.neonCyan.withValues(alpha: 0.35)),
                                  boxShadow: [
                                    BoxShadow(
                                      color: AppColors.neonCyan.withValues(alpha: 0.2),
                                      blurRadius: 12,
                                    ),
                                  ],
                                ),
                                child: const Icon(Icons.attach_money_rounded, color: AppColors.neonCyan, size: 22),
                              ),
                              title: Text(_fmt.format(c.montoUsd)),
                              subtitle: Text(
                                '${_labelMoneda(c.monedaPago)} · Venta ${c.ventaId.substring(0, 8)}...',
                              ),
                              trailing: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: AppColors.bgElevated,
                                  borderRadius: BorderRadius.circular(8),
                                  border: Border.all(color: AppColors.glassBorder),
                                ),
                                child: Text(
                                  c.fecha.substring(0, 10),
                                  style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                                ),
                              ),
                              children: [
                                Padding(
                                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
                                  child: EnviarReciboButton(
                                    onEnviar: () => context.read<AppState>().cobros.enviarRecibo(c.id),
                                  ),
                                ),
                              ],
                            );
                          }),
                        ],
                      ),
                    ),
    );
  }
}
