import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/ventas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/enviar_recibo_button.dart';
import 'nueva_venta_screen.dart';

class VentasListScreen extends StatefulWidget {
  const VentasListScreen({super.key});

  @override
  State<VentasListScreen> createState() => _VentasListScreenState();
}

class _VentasListScreenState extends State<VentasListScreen> {
  List<Venta> _ventas = [];
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
      _ventas = await context.read<AppState>().ventas.misVentas();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Mis Ventas',
      accentColor: AppColors.emerald,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      floatingActionButton: NeonFab(
        label: 'Nueva Venta',
        icon: Icons.add_shopping_cart_rounded,
        color: AppColors.emerald,
        onPressed: () async {
          final ok = await Navigator.push<bool>(
            context,
            MaterialPageRoute(builder: (_) => const NuevaVentaScreen()),
          );
          if (ok == true) _cargar();
        },
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : _ventas.isEmpty
                  ? const EmptyState(
                      icon: Icons.point_of_sale_rounded,
                      message: 'No hay ventas registradas',
                    )
                  : RefreshIndicator(
                      onRefresh: _cargar,
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                        children: [
                          SectionTitle(
                            title: 'Historial de ventas',
                            trailing: Text(
                              '${_ventas.length} registros',
                              style: Theme.of(context).textTheme.bodySmall,
                            ),
                          ),
                          ..._ventas.map((v) {
                            return GlassListTile(
                              accentColor: AppColors.emerald,
                              leading: Container(
                                width: 44,
                                height: 44,
                                decoration: BoxDecoration(
                                  color: AppColors.emerald.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(12),
                                  border: Border.all(color: AppColors.emerald.withValues(alpha: 0.35)),
                                ),
                                alignment: Alignment.center,
                                child: Text(
                                  '${v.detalles.length}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w800,
                                    color: AppColors.emerald,
                                  ),
                                ),
                              ),
                              title: Text(_fmt.format(v.totalUsd)),
                              subtitle: Row(
                                children: [
                                  StatusBadge.estado(v.estado),
                                  const SizedBox(width: 8),
                                  Text('ID ${v.id.substring(0, 8)}'),
                                ],
                              ),
                              children: [
                                if (v.detalles.isEmpty)
                                  const Padding(
                                    padding: EdgeInsets.all(12),
                                    child: Text('Venta sin detalle de productos'),
                                  )
                                else
                                  ...v.detalles.map(
                                    (d) => Padding(
                                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                                      child: Row(
                                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                        children: [
                                          Text('${d.cantidad} uds × \$${d.precioUnitarioUsd}'),
                                          Text(
                                            _fmt.format(d.subtotal),
                                            style: const TextStyle(fontWeight: FontWeight.w600),
                                          ),
                                        ],
                                      ),
                                    ),
                                  ),
                                Padding(
                                  padding: const EdgeInsets.fromLTRB(12, 4, 12, 12),
                                  child: EnviarReciboButton(
                                    onEnviar: () => context.read<AppState>().ventas.enviarRecibo(v.id),
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
