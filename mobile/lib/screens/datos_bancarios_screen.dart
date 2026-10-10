import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/empresa_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class DatosBancariosScreen extends StatefulWidget {
  const DatosBancariosScreen({super.key});

  @override
  State<DatosBancariosScreen> createState() => _DatosBancariosScreenState();
}

class _DatosBancariosScreenState extends State<DatosBancariosScreen> {
  final _bancoCtrl = TextEditingController();
  final _numeroCtrl = TextEditingController();
  final _cedulaCtrl = TextEditingController();
  String _tipoCuenta = 'Ahorro';
  bool _cargando = true;
  bool _guardando = false;

  static const _tipos = ['Ahorro', 'Corriente'];

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _bancoCtrl.dispose();
    _numeroCtrl.dispose();
    _cedulaCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    try {
      final datos = await context.read<AppState>().empresas.datosBancarios();
      _bancoCtrl.text = datos.banco ?? '';
      _numeroCtrl.text = datos.numeroCuenta ?? '';
      _cedulaCtrl.text = datos.cedulaNit ?? '';
      final tipo = (datos.tipoCuenta ?? '').trim();
      if (_tipos.contains(tipo)) _tipoCuenta = tipo;
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

  Future<void> _guardar() async {
    if (_bancoCtrl.text.trim().isEmpty || _numeroCtrl.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Indica el banco y el número de cuenta')),
      );
      return;
    }
    setState(() => _guardando = true);
    try {
      await context.read<AppState>().empresas.guardarDatosBancarios(
            DatosBancarios(
              banco: _bancoCtrl.text.trim(),
              tipoCuenta: _tipoCuenta,
              numeroCuenta: _numeroCtrl.text.trim(),
              cedulaNit: _cedulaCtrl.text.trim(),
            ),
          );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Datos bancarios guardados')),
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
    return FuturisticScaffold(
      title: 'Cuenta de transferencia',
      accentColor: AppColors.neonBlue,
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
              children: [
                GlassContainer(
                  accentColor: AppColors.neonBlue,
                  child: Column(
                    children: [
                      TextField(
                        controller: _bancoCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Banco',
                          prefixIcon: Icon(Icons.account_balance_rounded),
                        ),
                      ),
                      const SizedBox(height: 12),
                      DropdownButtonFormField<String>(
                        value: _tipoCuenta,
                        decoration: const InputDecoration(
                          labelText: 'Tipo de cuenta',
                          prefixIcon: Icon(Icons.account_balance_wallet_outlined),
                        ),
                        items: _tipos
                            .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                            .toList(),
                        onChanged: (v) => setState(() => _tipoCuenta = v ?? 'Ahorro'),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _numeroCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Número de cuenta',
                          prefixIcon: Icon(Icons.numbers_rounded),
                        ),
                      ),
                      const SizedBox(height: 12),
                      TextField(
                        controller: _cedulaCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Cédula / NIT del titular',
                          prefixIcon: Icon(Icons.badge_outlined),
                        ),
                      ),
                      const SizedBox(height: 20),
                      FilledButton.icon(
                        onPressed: _guardando ? null : _guardar,
                        icon: _guardando
                            ? const SizedBox(
                                width: 18,
                                height: 18,
                                child: CircularProgressIndicator(strokeWidth: 2),
                              )
                            : const Icon(Icons.save_rounded),
                        label: Text(_guardando ? 'Guardando...' : 'Guardar'),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
