import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/cobros_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';

class PanelCobranzaScreen extends StatefulWidget {
  const PanelCobranzaScreen({super.key});

  @override
  State<PanelCobranzaScreen> createState() => _PanelCobranzaScreenState();
}

class _PanelCobranzaScreenState extends State<PanelCobranzaScreen> {
  List<FilaCobranza> _filas = [];
  bool _cargando = true;
  String? _error;
  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _fmtFecha = DateFormat('dd/MM/yyyy');

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
      _filas = await context.read<AppState>().cobros.panelCobranza();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _abonoRapido(FilaCobranza fila) async {
    final ctrl = TextEditingController(
      text: fila.montoProximaCuotaUsd > 0
          ? fila.montoProximaCuotaUsd.toStringAsFixed(2)
          : fila.saldoPendienteUsd.toStringAsFixed(2),
    );
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('Abono rápido'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(fila.clienteNombre, style: const TextStyle(fontWeight: FontWeight.w700)),
            Text(fila.productosResumen),
            const SizedBox(height: 12),
            TextField(
              controller: ctrl,
              keyboardType: TextInputType.number,
              decoration: InputDecoration(
                labelText: 'Monto USD (Saldo: ${_fmt.format(fila.saldoPendienteUsd)})',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Registrar')),
        ],
      ),
    );
    if (ok != true || !mounted) return;

    final monto = double.tryParse(ctrl.text.replaceAll(',', '.'));
    if (monto == null || monto <= 0) return;

    try {
      final tasa = await context.read<AppState>().catalogo.ultimaTasa();
      await context.read<AppState>().cobros.registrarCobro(
            ventaId: fila.id,
            montoUsd: monto,
            monedaPago: 'dolar',
            tasaUsd: tasa.usdBs,
            tasaEur: tasa.eurBs,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Abono de ${_fmt.format(monto)} registrado')),
        );
        _cargar();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Panel de Cobranza',
      accentColor: AppColors.neonCyan,
      actions: [IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar)],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _filas.isEmpty
                  ? const EmptyState(
                      icon: Icons.table_chart_rounded,
                      message: 'No hay cuentas pendientes de cobro',
                    )
                  : RefreshIndicator(
                      onRefresh: _cargar,
                      child: SingleChildScrollView(
                        scrollDirection: Axis.horizontal,
                        child: SingleChildScrollView(
                          child: DataTable(
                            headingRowColor: WidgetStateProperty.all(
                              AppColors.neonCyan.withValues(alpha: 0.08),
                            ),
                            columns: const [
                              DataColumn(label: Text('Cliente')),
                              DataColumn(label: Text('Producto')),
                              DataColumn(label: Text('Precio')),
                              DataColumn(label: Text('Costo')),
                              DataColumn(label: Text('Crédito')),
                              DataColumn(label: Text('Deuda')),
                              DataColumn(label: Text('Abonado')),
                              DataColumn(label: Text('Resta')),
                              DataColumn(label: Text('Próximo pago')),
                              DataColumn(label: Text('Estado')),
                              DataColumn(label: Text('Abono')),
                            ],
                            rows: _filas.map((f) {
                              final proximo = f.proximoPago != null
                                  ? _fmtFecha.format(DateTime.parse(f.proximoPago!))
                                  : '—';
                              final estadoColor = f.estadoCuenta == 'En mora'
                                  ? Colors.red
                                  : AppColors.emerald;
                              return DataRow(cells: [
                                DataCell(Text(f.clienteNombre, style: const TextStyle(fontWeight: FontWeight.w600))),
                                DataCell(SizedBox(width: 120, child: Text(f.productosResumen, maxLines: 2))),
                                DataCell(Text(_fmt.format(f.totalUsd))),
                                DataCell(Text(_fmt.format(f.costoTotalUsd))),
                                DataCell(Text(f.tipoCredito)),
                                DataCell(Text(_fmt.format(f.totalUsd))),
                                DataCell(Text(_fmt.format(f.cobradoUsd), style: const TextStyle(color: AppColors.emerald))),
                                DataCell(Text(_fmt.format(f.saldoPendienteUsd), style: const TextStyle(color: AppColors.amber))),
                                DataCell(Text(proximo)),
                                DataCell(Text(f.estadoCuenta, style: TextStyle(color: estadoColor, fontWeight: FontWeight.w700))),
                                DataCell(
                                  IconButton(
                                    icon: const Icon(Icons.price_check_rounded, color: AppColors.neonCyan),
                                    tooltip: 'Abono rápido',
                                    onPressed: () => _abonoRapido(f),
                                  ),
                                ),
                              ]);
                            }).toList(),
                          ),
                        ),
                      ),
                    ),
    );
  }
}
