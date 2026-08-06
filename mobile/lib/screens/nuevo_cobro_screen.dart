import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../providers/app_state.dart';
import '../services/catalogo_service.dart';
import '../services/cobros_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';

class NuevoCobroScreen extends StatefulWidget {
  const NuevoCobroScreen({super.key});

  @override
  State<NuevoCobroScreen> createState() => _NuevoCobroScreenState();
}

class _NuevoCobroScreenState extends State<NuevoCobroScreen> {
  List<VentaPendiente> _pendientes = [];
  TasaCambio? _tasa;

  VentaPendiente? _venta;
  String _moneda = 'dolar';
  final _montoCtrl = TextEditingController();
  bool _cargando = true;
  bool _guardando = false;

  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _montoCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    final state = context.read<AppState>();
    try {
      final results = await Future.wait([
        state.cobros.ventasPendientes(),
        state.catalogo.ultimaTasa(),
      ]);
      _pendientes = results[0] as List<VentaPendiente>;
      _tasa = results[1] as TasaCambio;
      if (_pendientes.isNotEmpty) {
        _venta = _pendientes.first;
        _montoCtrl.text = _venta!.saldoPendienteUsd.toStringAsFixed(2);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  void _onVentaChanged(VentaPendiente? v) {
    setState(() {
      _venta = v;
      if (v != null) {
        _montoCtrl.text = v.saldoPendienteUsd.toStringAsFixed(2);
      }
    });
  }

  Future<void> _registrar() async {
    if (_venta == null || _tasa == null) return;
    final monto = double.tryParse(_montoCtrl.text);
    if (monto == null || monto <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa un monto válido')),
      );
      return;
    }
    if (monto > _venta!.saldoPendienteUsd + 0.01) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Máximo: ${_fmt.format(_venta!.saldoPendienteUsd)}')),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      await context.read<AppState>().cobros.registrarCobro(
            ventaId: _venta!.id,
            montoUsd: monto,
            monedaPago: _moneda,
            tasaUsd: _tasa!.usdBs,
            tasaEur: _tasa!.eurBs,
            cobroId: const Uuid().v4(),
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Cobro registrado: ${_fmt.format(monto)}')),
      );
      Navigator.pop(context, true);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_cargando) {
      return const FuturisticScaffold(
        title: 'Nuevo Cobro',
        accentColor: AppColors.neonCyan,
        body: Center(child: CircularProgressIndicator()),
      );
    }

    return FuturisticScaffold(
      title: 'Nuevo Cobro — Campo',
      accentColor: AppColors.neonCyan,
      bottomNavigationBar: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton.icon(
            onPressed: _guardando || _venta == null ? null : _registrar,
            icon: _guardando
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.check_circle_rounded),
            label: Text(_guardando ? 'Registrando...' : 'Registrar Cobro'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 52),
              backgroundColor: AppColors.neonCyan,
              foregroundColor: AppColors.bgDeep,
            ),
          ),
        ),
      ),
      body: _pendientes.isEmpty
          ? const EmptyState(
              icon: Icons.check_circle_outline_rounded,
              message: 'No hay ventas pendientes de cobro',
            )
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              children: [
                const SectionTitle(title: 'Selecciona la venta a cobrar'),
                ..._pendientes.map((v) {
                  final selected = _venta?.id == v.id;
                  return GlassListTile(
                    accentColor: AppColors.neonCyan,
                    selected: selected,
                    onTap: () => _onVentaChanged(v),
                    title: Text(v.clienteNombre),
                    subtitle: Text(
                      'Saldo: ${_fmt.format(v.saldoPendienteUsd)} · '
                      'Total: ${_fmt.format(v.totalUsd)} · ${v.estado}',
                    ),
                    trailing: selected
                        ? const Icon(Icons.check_circle_rounded, color: AppColors.neonCyan)
                        : const Icon(Icons.radio_button_unchecked, color: AppColors.textMuted),
                  );
                }),
                const SizedBox(height: 20),
                GlassContainer(
                  accentColor: AppColors.neonCyan,
                  child: Column(
                    children: [
                      TextField(
                        controller: _montoCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        style: const TextStyle(color: AppColors.textPrimary),
                        decoration: InputDecoration(
                          labelText: 'Monto USD',
                          prefixIcon: const Icon(Icons.attach_money_rounded),
                          helperText: _venta != null
                              ? 'Saldo pendiente: ${_fmt.format(_venta!.saldoPendienteUsd)}'
                              : null,
                        ),
                      ),
                      const SizedBox(height: 16),
                      DropdownButtonFormField<String>(
                        value: _moneda,
                        decoration: const InputDecoration(
                          labelText: 'Moneda de pago',
                          prefixIcon: Icon(Icons.currency_exchange_rounded),
                        ),
                        dropdownColor: AppColors.bgElevated,
                        items: CobrosService.monedas
                            .map((m) => DropdownMenuItem(value: m.$1, child: Text(m.$2)))
                            .toList(),
                        onChanged: (v) => setState(() => _moneda = v!),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
                if (_tasa != null)
                  GlassContainer(
                    accentColor: AppColors.neonBlue,
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(10),
                          decoration: BoxDecoration(
                            color: AppColors.neonBlue.withValues(alpha: 0.15),
                            borderRadius: BorderRadius.circular(12),
                          ),
                          child: const Icon(Icons.trending_up_rounded, color: AppColors.neonBlue),
                        ),
                        const SizedBox(width: 14),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text('Tasa del día', style: TextStyle(fontWeight: FontWeight.w700)),
                              Text('USD/Bs: ${_tasa!.usdBs} · EUR/Bs: ${_tasa!.eurBs}'),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                if (_moneda == 'dolar' || _moneda == 'euro')
                  Padding(
                    padding: const EdgeInsets.only(top: 14),
                    child: GlassContainer(
                      accentColor: AppColors.amber,
                      padding: const EdgeInsets.all(14),
                      child: Row(
                        children: [
                          Icon(Icons.info_outline_rounded, color: AppColors.amber.withValues(alpha: 0.9), size: 20),
                          const SizedBox(width: 10),
                          Expanded(
                            child: Text(
                              'Pagos en divisas aplican IGTF según configuración fiscal',
                              style: TextStyle(color: AppColors.amber.withValues(alpha: 0.95), fontSize: 13),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                const SizedBox(height: 80),
              ],
            ),
    );
  }
}
