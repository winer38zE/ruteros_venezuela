import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/proveedores_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';

class ProveedoresScreen extends StatefulWidget {
  const ProveedoresScreen({super.key});

  @override
  State<ProveedoresScreen> createState() => _ProveedoresScreenState();
}

class _ProveedoresScreenState extends State<ProveedoresScreen> {
  List<Proveedor> _proveedores = [];
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
      _proveedores = await context.read<AppState>().proveedores.listar();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _nuevoProveedor() async {
    final nombreCtrl = TextEditingController();
    final telCtrl = TextEditingController();
    final contactoCtrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: const Text('Nuevo proveedor'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(controller: nombreCtrl, decoration: const InputDecoration(labelText: 'Nombre / Empresa')),
            TextField(controller: telCtrl, decoration: const InputDecoration(labelText: 'Teléfono')),
            TextField(controller: contactoCtrl, decoration: const InputDecoration(labelText: 'Contacto')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Guardar')),
        ],
      ),
    );
    if (ok != true || nombreCtrl.text.trim().isEmpty) return;
    try {
      await context.read<AppState>().proveedores.crear(
            nombre: nombreCtrl.text.trim(),
            telefono: telCtrl.text.trim().isEmpty ? null : telCtrl.text.trim(),
            contacto: contactoCtrl.text.trim().isEmpty ? null : contactoCtrl.text.trim(),
          );
      _cargar();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    }
  }

  Future<void> _pagarDeuda(Proveedor prov) async {
    if (prov.saldoDeudaUsd <= 0) return;
    final ctrl = TextEditingController(text: prov.saldoDeudaUsd.toStringAsFixed(2));
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        backgroundColor: AppColors.bgCard,
        title: Text('Pagar a ${prov.nombre}'),
        content: TextField(
          controller: ctrl,
          keyboardType: TextInputType.number,
          decoration: InputDecoration(labelText: 'Monto USD (Deuda: ${_fmt.format(prov.saldoDeudaUsd)})'),
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Registrar pago')),
        ],
      ),
    );
    if (ok != true) return;
    final monto = double.tryParse(ctrl.text.replaceAll(',', '.'));
    if (monto == null || monto <= 0) return;
    try {
      await context.read<AppState>().proveedores.registrarPago(prov.id, monto);
      _cargar();
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
    final deudaTotal = _proveedores.fold<double>(0, (s, p) => s + p.saldoDeudaUsd);

    return FuturisticScaffold(
      title: 'Proveedores',
      accentColor: AppColors.violet,
      actions: [IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar)],
      floatingActionButton: NeonFab(
        label: 'Nuevo',
        icon: Icons.add_business_rounded,
        color: AppColors.violet,
        onPressed: _nuevoProveedor,
      ),
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : RefreshIndicator(
                  onRefresh: _cargar,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 100),
                    children: [
                      GlassContainer(
                        accentColor: AppColors.amber,
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Deuda total proveedores', style: TextStyle(fontWeight: FontWeight.w700)),
                            Text(_fmt.format(deudaTotal), style: const TextStyle(color: AppColors.amber, fontWeight: FontWeight.w800)),
                          ],
                        ),
                      ),
                      const SizedBox(height: 12),
                      ..._proveedores.map((p) => GlassListTile(
                            accentColor: AppColors.violet,
                            leading: const Icon(Icons.local_shipping_rounded, color: AppColors.violet),
                            title: Text(p.nombre),
                            subtitle: Text(
                              '${p.telefono ?? "Sin teléfono"} · Deuda: ${_fmt.format(p.saldoDeudaUsd)}',
                            ),
                            trailing: p.saldoDeudaUsd > 0
                                ? IconButton(
                                    icon: const Icon(Icons.payments_rounded, color: AppColors.emerald),
                                    onPressed: () => _pagarDeuda(p),
                                  )
                                : const Icon(Icons.check_circle, color: AppColors.emerald, size: 20),
                          )),
                    ],
                  ),
                ),
    );
  }
}
