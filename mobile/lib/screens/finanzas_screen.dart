import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/finanzas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';
import 'nomina_screen.dart';
import 'registrar_movimiento_screen.dart';

class FinanzasScreen extends StatefulWidget {
  const FinanzasScreen({super.key});

  @override
  State<FinanzasScreen> createState() => _FinanzasScreenState();
}

class _FinanzasScreenState extends State<FinanzasScreen> {
  ResumenFinanciero? _resumen;
  List<MovimientoFinanciero> _movimientos = [];
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
      final svc = context.read<AppState>().finanzas;
      final results = await Future.wait([
        svc.obtenerResumen(),
        svc.listarMovimientos(),
      ]);
      _resumen = results[0] as ResumenFinanciero;
      _movimientos = results[1] as List<MovimientoFinanciero>;
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Control Financiero',
      accentColor: AppColors.amber,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      floatingActionButton: NeonFab(
        label: 'Registrar',
        icon: Icons.add_rounded,
        color: AppColors.amber,
        onPressed: () async {
          final ok = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const RegistrarMovimientoScreen(soloGasto: true)),
          );
          if (ok == true) _cargar();
        },
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    children: [
                      if (_resumen != null) _ResumenGrid(resumen: _resumen!, fmt: _fmt),
                      const SizedBox(height: 16),
                      GlassContainer(
                        accentColor: AppColors.violet,
                        onTap: () async {
                          await Navigator.push(
                            context,
                            MaterialPageRoute(builder: (_) => const NominaScreen()),
                          );
                          _cargar();
                        },
                        child: Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: AppColors.violet.withValues(alpha: 0.15),
                                borderRadius: BorderRadius.circular(14),
                              ),
                              child: const Icon(Icons.groups_rounded, color: AppColors.violet),
                            ),
                            const SizedBox(width: 14),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text('Nómina y Pagos', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                                  Text(
                                    'Pendiente: ${_fmt.format(_resumen!.nominaPendienteUsd)}',
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                ],
                              ),
                            ),
                            const Icon(Icons.chevron_right, color: AppColors.textMuted),
                          ],
                        ),
                      ),
                      const SizedBox(height: 20),
                      const SectionTitle(title: 'Movimientos recientes'),
                      if (_movimientos.isEmpty)
                        const EmptyState(icon: Icons.receipt_long_rounded, message: 'Sin movimientos registrados')
                      else
                        ..._movimientos.take(20).map((m) {
                          final esEntrada = m.tipo == 'entrada';
                          final color = esEntrada ? AppColors.emerald : AppColors.amber;
                          return GlassListTile(
                            accentColor: color,
                            leading: Icon(
                              esEntrada ? Icons.arrow_downward_rounded : Icons.arrow_upward_rounded,
                              color: color,
                            ),
                            title: Text(_fmt.format(m.montoUsd)),
                            subtitle: Text('${m.categoria.replaceAll('_', ' ')} · ${m.descripcion}'),
                            trailing: Text(
                              m.fecha.substring(0, 10),
                              style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                            ),
                          );
                        }),
                    ],
                  ),
                ),
    );
  }
}

class _ResumenGrid extends StatelessWidget {
  const _ResumenGrid({required this.resumen, required this.fmt});
  final ResumenFinanciero resumen;
  final NumberFormat fmt;

  @override
  Widget build(BuildContext context) {
    final cards = [
      _Kpi('Entradas', fmt.format(resumen.totalEntradasUsd), AppColors.emerald, Icons.trending_up_rounded),
      _Kpi('Salidas', fmt.format(resumen.totalSalidasUsd), AppColors.amber, Icons.trending_down_rounded),
      _Kpi('Gastos Moto', fmt.format(resumen.gastosMotoUsd), AppColors.neonBlue, Icons.two_wheeler_rounded),
      _Kpi('Nómina Pend.', fmt.format(resumen.nominaPendienteUsd), AppColors.violet, Icons.payments_rounded),
    ];

    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 12,
      crossAxisSpacing: 12,
      childAspectRatio: 1.35,
      children: cards.map((k) => GlassContainer(
            accentColor: k.color,
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Icon(k.icon, color: k.color, size: 22),
                const Spacer(),
                Text(k.label, style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
                Text(k.value, style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16, color: k.color)),
              ],
            ),
          )).toList(),
    );
  }
}

class _Kpi {
  const _Kpi(this.label, this.value, this.color, this.icon);
  final String label;
  final String value;
  final Color color;
  final IconData icon;
}
