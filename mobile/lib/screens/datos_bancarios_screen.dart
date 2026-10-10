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
  List<CuentaBancaria> _cuentas = [];
  bool _cargando = true;

  static const _tipos = ['Ahorro', 'Corriente'];

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
    final creada = await showDialog<bool>(
      context: context,
      builder: (ctx) => const _FormularioCuenta(),
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
                    message: 'No hay cuentas. Agrega una transferencia o un Pago Móvil de Venezuela.',
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
                              Text('Cédula: ${c.documento}'),
                            ] else ...[
                              Text('Tipo: ${c.tipoCuenta}'),
                              Text('Número: ${c.numeroCuenta}'),
                              Text('Cédula/RIF: ${c.documento}'),
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

class _FormularioCuenta extends StatefulWidget {
  const _FormularioCuenta();

  @override
  State<_FormularioCuenta> createState() => _FormularioCuentaState();
}

class _FormularioCuentaState extends State<_FormularioCuenta> {
  static const _bancos = [
    'Banco de Venezuela',
    'Banesco',
    'BBVA Provincial',
    'Mercantil',
    'BNC',
    'Bancamiga',
    'Bancaribe',
    'Banco del Tesoro',
    'Banco Exterior',
    'Banplus',
    'Banco Plaza',
    '100% Banco',
    'Otro',
  ];

  final _bancoOtroCtrl = TextEditingController();
  final _numeroCtrl = TextEditingController();
  final _telefonoCtrl = TextEditingController();
  final _titularCtrl = TextEditingController();
  final _documentoCtrl = TextEditingController();
  String _canal = 'transferencia';
  String _banco = 'Banesco';
  String _tipo = 'Ahorro';
  bool _guardando = false;

  @override
  void dispose() {
    _bancoOtroCtrl.dispose();
    _numeroCtrl.dispose();
    _telefonoCtrl.dispose();
    _titularCtrl.dispose();
    _documentoCtrl.dispose();
    super.dispose();
  }

  String get _bancoFinal =>
      _banco == 'Otro' ? _bancoOtroCtrl.text.trim() : _banco;

  Future<void> _guardar() async {
    final pagoMovil = _canal == 'pago_movil';
    if (_bancoFinal.isEmpty ||
        _titularCtrl.text.trim().isEmpty ||
        _documentoCtrl.text.trim().isEmpty ||
        (pagoMovil ? _telefonoCtrl.text.trim().isEmpty : _numeroCtrl.text.trim().isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            pagoMovil
                ? 'Completa banco, teléfono, titular y cédula'
                : 'Completa banco, número, titular y cédula o RIF',
          ),
        ),
      );
      return;
    }
    setState(() => _guardando = true);
    try {
      await context.read<AppState>().empresas.crearCuenta(
            canal: _canal,
            banco: _bancoFinal,
            titular: _titularCtrl.text.trim(),
            documento: _documentoCtrl.text.trim(),
            tipoCuenta: pagoMovil ? null : _tipo,
            numeroCuenta: pagoMovil ? null : _numeroCtrl.text.trim(),
            telefono: pagoMovil ? _telefonoCtrl.text.trim() : null,
          );
      if (!mounted) return;
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
    final pagoMovil = _canal == 'pago_movil';
    return AlertDialog(
      backgroundColor: AppColors.bgCard,
      title: const Text('Cuenta venezolana'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            DropdownButtonFormField<String>(
              value: _canal,
              decoration: const InputDecoration(labelText: 'Medio'),
              items: const [
                DropdownMenuItem(value: 'transferencia', child: Text('Transferencia bancaria')),
                DropdownMenuItem(value: 'pago_movil', child: Text('Pago móvil')),
              ],
              onChanged: (v) => setState(() => _canal = v ?? 'transferencia'),
            ),
            const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _banco,
              decoration: const InputDecoration(labelText: 'Banco'),
              items: _bancos
                  .map((b) => DropdownMenuItem(value: b, child: Text(b)))
                  .toList(),
              onChanged: (v) => setState(() => _banco = v ?? 'Banesco'),
            ),
            if (_banco == 'Otro') ...[
              const SizedBox(height: 8),
              TextField(
                controller: _bancoOtroCtrl,
                decoration: const InputDecoration(labelText: 'Nombre del banco'),
              ),
            ],
            const SizedBox(height: 8),
            if (!pagoMovil)
              DropdownButtonFormField<String>(
                value: _tipo,
                decoration: const InputDecoration(labelText: 'Tipo de cuenta'),
                items: _DatosBancariosScreenState._tipos
                    .map((t) => DropdownMenuItem(value: t, child: Text(t)))
                    .toList(),
                onChanged: (v) => setState(() => _tipo = v ?? 'Ahorro'),
              ),
            if (!pagoMovil) const SizedBox(height: 8),
            if (pagoMovil)
              TextField(
                controller: _telefonoCtrl,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(
                  labelText: 'Teléfono Pago Móvil',
                  hintText: '0412 0000000',
                ),
              )
            else
              TextField(
                controller: _numeroCtrl,
                decoration: const InputDecoration(
                  labelText: 'Número de cuenta',
                  hintText: '0102...',
                ),
              ),
            const SizedBox(height: 8),
            TextField(
              controller: _titularCtrl,
              decoration: const InputDecoration(labelText: 'Titular'),
            ),
            const SizedBox(height: 8),
            TextField(
              controller: _documentoCtrl,
              decoration: InputDecoration(
                labelText: pagoMovil ? 'Cédula' : 'Cédula / RIF',
                hintText: pagoMovil ? 'V-12345678' : 'V-12345678 o J-123456789',
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: _guardando ? null : () => Navigator.pop(context, false), child: const Text('Cancelar')),
        FilledButton(
          onPressed: _guardando ? null : _guardar,
          child: Text(_guardando ? 'Guardando...' : 'Guardar'),
        ),
      ],
    );
  }
}
