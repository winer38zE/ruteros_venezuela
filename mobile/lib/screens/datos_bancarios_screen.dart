import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/empresa_service.dart';
import '../theme/app_theme.dart';
import '../utils/region_bancaria.dart';
import '../widgets/cuenta_bancaria_form_dialog.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class DatosBancariosScreen extends StatefulWidget {
  const DatosBancariosScreen({super.key});

  @override
  State<DatosBancariosScreen> createState() => _DatosBancariosScreenState();
}

class _DatosBancariosScreenState extends State<DatosBancariosScreen> {
  List<CuentaBancaria> _cuentas = [];
  bool _cargando = true;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    setState(() => _cargando = true);
    try {
      final cuentas = await context.read<AppState>().empresas.cuentasBancarias();
      if (!mounted) return;
      setState(() => _cuentas = cuentas);
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

  Future<void> _agregar() async {
    final state = context.read<AppState>();
    final config = await configuracionBancariaSesion(
      paises: state.paises,
      region: state.region,
      paisUsuario: state.usuario?.pais,
      paisId: state.usuario?.paisId,
    );
    if (!mounted) return;
    final creada = await showDialog<bool>(
      context: context,
      builder: (_) => CuentaBancariaFormDialog(
        config: config,
        titulo: 'Cuenta de cobro (${state.region?.nombre ?? "región"})',
        onGuardar: (data) async {
          await state.empresas.crearCuenta(
            canal: data.canal,
            banco: data.banco,
            titular: data.titular,
            documento: data.documentoIdentidad,
            tipoCuenta: data.tipoCuenta,
            numeroCuenta: data.numeroCuenta,
            telefono: data.telefonoPagoMovil,
          );
        },
      ),
    );
    if (creada == true) _cargar();
  }

  Future<void> _archivar(CuentaBancaria cuenta) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('Quitar cuenta'),
        content: Text('Se ocultará ${cuenta.banco} · ${cuenta.numeroCuenta} de las transferencias.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Quitar')),
        ],
      ),
    );
    if (ok != true || !mounted) return;
    try {
      await context.read<AppState>().empresas.archivarCuenta(cuenta.id);
      if (!mounted) return;
      await _cargar();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Cuentas de transferencia',
      accentColor: AppColors.neonBlue,
      actions: [
        IconButton(onPressed: _agregar, icon: const Icon(Icons.add_rounded)),
      ],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              children: [
                if (_cuentas.isEmpty)
                  const EmptyState(
                    icon: Icons.account_balance_rounded,
                    message: 'No hay cuentas. Agrega una según los bancos de tu país.',
                  )
                else
                  ..._cuentas.map(
                    (c) => Padding(
                      padding: const EdgeInsets.only(bottom: 12),
                      child: GlassContainer(
                        accentColor: AppColors.neonBlue,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              c.esPagoMovil ? '${c.banco} · Pago móvil' : '${c.banco} · Transferencia',
                              style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                            ),
                            const SizedBox(height: 6),
                            if (c.esPagoMovil) ...[
                              Text('Teléfono: ${c.datoCopiable}'),
                              Text('Documento: ${c.documento}'),
                            ] else ...[
                              Text('Tipo: ${c.tipoCuenta}'),
                              Text('Número: ${c.numeroCuenta}'),
                              Text('Documento: ${c.documento}'),
                            ],
                            Text('Titular: ${c.titular}'),
                            Align(
                              alignment: Alignment.centerRight,
                              child: TextButton.icon(
                                onPressed: () => _archivar(c),
                                icon: const Icon(Icons.archive_outlined),
                                label: const Text('Quitar'),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                const SizedBox(height: 8),
                FilledButton.icon(
                  onPressed: _agregar,
                  icon: const Icon(Icons.add_rounded),
                  label: const Text('Agregar cuenta'),
                ),
              ],
            ),
    );
  }
}
