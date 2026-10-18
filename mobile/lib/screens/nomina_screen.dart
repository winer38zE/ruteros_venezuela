import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/finanzas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';

class NominaScreen extends StatefulWidget {
  const NominaScreen({super.key});

  @override
  State<NominaScreen> createState() => _NominaScreenState();
}

class _NominaScreenState extends State<NominaScreen> {
  NominaCalculada? _nomina;
  bool _cargando = true;
  bool _aprobando = false;
  String? _error;
  String _simbolo = r'$';

  NumberFormat get _fmt => NumberFormat.currency(symbol: _simbolo, decimalDigits: 2);

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
      _simbolo = await state.simboloMonedaPersistido();
      _nomina = await state.finanzas.calcularNomina();
      if (_nomina != null && _nomina!.simboloMoneda.isNotEmpty) {
        _simbolo = _nomina!.simboloMoneda;
      }
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _aprobar(DetalleNominaEmpleado emp) async {
    if (emp.pendienteUsd <= 0) return;

    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.bgElevated,
        title: const Text('Aprobar pago'),
        content: Text('¿Registrar pago de ${_fmt.format(emp.pendienteUsd)} a ${emp.empleadoNombre}?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Aprobar')),
        ],
      ),
    );
    if (confirm != true) return;
    if (!mounted) return;

    setState(() => _aprobando = true);
    try {
      await context.read<AppState>().finanzas.aprobarPago(
            empleadoId: emp.empleadoId,
            montoUsd: emp.pendienteUsd,
            descripcion: 'Pago nómina aprobado — ${emp.empleadoNombre}',
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Pago registrado: ${emp.empleadoNombre}')),
        );
      }
      await _cargar();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _aprobando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final moneda = _nomina?.monedaPrincipal ?? context.watch<AppState>().monedaPrincipal;
    return FuturisticScaffold(
      title: 'Nómina de Personal',
      accentColor: AppColors.violet,
      actions: [
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Color(0xFFEF4444))))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if (_nomina != null) ...[
                        GlassContainer(
                          accentColor: AppColors.violet,
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Total pendiente: ${_fmt.format(_nomina!.totalPendienteUsd)}',
                                style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18),
                              ),
                              const SizedBox(height: 4),
                              Text(
                                'Moneda operativa: $moneda',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                              const SizedBox(height: 8),
                              Text(
                                'Vendedor: ${_fmt.format(_nomina!.comisionVendedorPorArticulo)}/artículo · '
                                'Cobrador: ${_nomina!.comisionCobradorPorcentaje.toStringAsFixed(0)}% cobros',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 16),
                        const SectionTitle(title: 'Desglose por empleado'),
                        if (_nomina!.empleados.isEmpty)
                          const EmptyState(icon: Icons.person_off_rounded, message: 'Sin empleados con comisiones')
                        else
                          ..._nomina!.empleados.map((emp) {
                            final color = emp.rol == 'VENDEDOR' ? AppColors.emerald : AppColors.neonCyan;
                            return GlassListTile(
                              accentColor: color,
                              title: Text(emp.empleadoNombre),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text('Rol: ${emp.rol}'),
                                  if (emp.sueldoBaseUsd > 0)
                                    Text('Sueldo base: ${_fmt.format(emp.sueldoBaseUsd)}'),
                                  if (emp.articulosVendidos > 0)
                                    Text(
                                      '${emp.articulosVendidos} artículos → comisión ${_fmt.format(emp.comisionVentasUsd)}',
                                    ),
                                  if (emp.totalCobradoUsd > 0)
                                    Text(
                                      'Cobrado ${_fmt.format(emp.totalCobradoUsd)} → comisión ${_fmt.format(emp.comisionCobrosUsd)}',
                                    ),
                                  Text(
                                    'Calculado: ${_fmt.format(emp.totalCalculadoUsd)} · Pagado: ${_fmt.format(emp.totalPagadoUsd)}',
                                  ),
                                ],
                              ),
                              trailing: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: [
                                  Text(
                                    _fmt.format(emp.pendienteUsd),
                                    style: TextStyle(fontWeight: FontWeight.w800, color: color),
                                  ),
                                  if (emp.pendienteUsd > 0)
                                    TextButton(
                                      onPressed: _aprobando ? null : () => _aprobar(emp),
                                      child: Text(_aprobando ? '...' : 'Aprobar'),
                                    ),
                                ],
                              ),
                            );
                          }),
                      ],
                    ],
                  ),
                ),
    );
  }
}
