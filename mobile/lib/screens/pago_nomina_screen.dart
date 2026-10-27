import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';

import '../providers/app_state.dart';
import '../services/api_service.dart';
import '../services/nomina_pago_service.dart';
import '../services/usuarios_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class PagoNominaScreen extends StatefulWidget {
  const PagoNominaScreen({super.key});

  @override
  State<PagoNominaScreen> createState() => _PagoNominaScreenState();
}

class _PagoNominaScreenState extends State<PagoNominaScreen> {
  List<UsuarioEquipo> _empleados = [];
  UsuarioEquipo? _empleado;
  TasasNomina? _tasas;
  NominaCalculadaEmpleado? _calculo;

  String _pais = 'VE';
  String _tipoPago = 'mixto';
  bool _cargando = true;
  bool _calculando = false;
  bool _guardando = false;

  final _salarioCtrl = TextEditingController();
  final _bonosCtrl = TextEditingController(text: '0');
  final _pctCobroCtrl = TextEditingController();
  final _usdCtrl = TextEditingController();
  final _vesCtrl = TextEditingController();
  final _copCtrl = TextEditingController();

  final _fmtUsd = NumberFormat.currency(symbol: r'$', decimalDigits: 2);

  @override
  void initState() {
    super.initState();
    _cargarInicial();
  }

  @override
  void dispose() {
    _salarioCtrl.dispose();
    _bonosCtrl.dispose();
    _pctCobroCtrl.dispose();
    _usdCtrl.dispose();
    _vesCtrl.dispose();
    _copCtrl.dispose();
    super.dispose();
  }

  NominaPagoService get _nomina => context.read<AppState>().nominaPago;

  Future<void> _cargarInicial() async {
    setState(() => _cargando = true);
    try {
      final state = context.read<AppState>();
      final paisSesion = state.region ?? state.usuario?.pais;
      final iso = paisSesion?.codigoIso.toUpperCase();
      if (iso == 'CO' || iso == 'VE') {
        _pais = iso!;
      } else if (state.esVenezuela) {
        _pais = 'VE';
      }
      final todos = await state.usuarios.listar();
      _empleados = todos
          .where((u) => u.activo && (u.rol == 'VENDEDOR' || u.rol == 'COBRADOR'))
          .toList();
      _tasas = await _nomina.obtenerTasas();
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error al cargar: $e'), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Map<String, double>? _detallesDesdeCampos() {
    if (_pais != 'VE') return null;
    final usd = double.tryParse(_usdCtrl.text.replaceAll(',', '.')) ?? 0;
    final ves = double.tryParse(_vesCtrl.text.replaceAll(',', '.')) ?? 0;
    final cop = double.tryParse(_copCtrl.text.replaceAll(',', '.')) ?? 0;
    if (usd <= 0 && ves <= 0 && cop <= 0) return null;
    return {'USD': usd, 'VES': ves, 'COP': cop};
  }

  void _rellenarDesglose(NominaCalculadaEmpleado c) {
    _usdCtrl.text = _numStr(c.detallesPago['USD']);
    _vesCtrl.text = _numStr(c.detallesPago['VES']);
    _copCtrl.text = _numStr(c.detallesPago['COP']);
  }

  String _numStr(double? v) {
    if (v == null || v == 0) return '';
    return v.toStringAsFixed(2);
  }

  Future<void> _recalcular() async {
    if (_empleado == null) return;
    setState(() => _calculando = true);
    try {
      final salario = double.tryParse(_salarioCtrl.text.replaceAll(',', '.'));
      final bonos = double.tryParse(_bonosCtrl.text.replaceAll(',', '.')) ?? 0;
      final pct = double.tryParse(_pctCobroCtrl.text.replaceAll(',', '.'));
      final calc = await _nomina.calcular(
        usuarioId: _empleado!.id,
        pais: _pais,
        tipoPago: _tipoPago,
        salarioBase: salario,
        totalBonos: bonos,
        porcentajeCobro: pct,
        detallesPago: _detallesDesdeCampos(),
      );
      setState(() {
        _calculo = calc;
        if (_salarioCtrl.text.trim().isEmpty) {
          _salarioCtrl.text = calc.salarioBase.toStringAsFixed(2);
        }
        _rellenarDesglose(calc);
      });
      if (calc.advertenciaDetalle != null && mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(calc.advertenciaDetalle!), backgroundColor: Colors.orange),
        );
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _calculando = false);
    }
  }

  void _onCambioMonedaLocal(String moneda, String value) {
    final tasas = _tasas ?? _calculo?.tasas;
    if (tasas == null || _calculo == null) return;
    final monto = double.tryParse(value.replaceAll(',', '.')) ?? 0;
    if (monto <= 0) return;
    final usdToVes = (tasas['USD_TO_VES'] as num?)?.toDouble() ?? 887.30;
    final usdToCop = (tasas['USD_TO_COP'] as num?)?.toDouble() ?? 3144.0;
    final totalUsd = _calculo!.totalPagarUsd;
    double eqUsd = 0;
    if (moneda == 'USD') eqUsd = monto;
    if (moneda == 'VES' && usdToVes > 0) eqUsd = monto / usdToVes;
    if (moneda == 'COP' && usdToCop > 0) eqUsd = monto / usdToCop;
    final restoUsd = (totalUsd - eqUsd).clamp(0, double.infinity);
    if (moneda != 'USD') _usdCtrl.text = restoUsd.toStringAsFixed(2);
  }

  Future<void> _guardar() async {
    if (_empleado == null || _calculo == null) {
      await _recalcular();
      if (_calculo == null) return;
    }
    final confirm = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        backgroundColor: AppColors.bgElevated,
        title: const Text('Confirmar pago'),
        content: Text(
          'Registrar pago de ${_fmtUsd.format(_calculo!.totalPagarUsd)} a ${_empleado!.nombre}?',
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          FilledButton(onPressed: () => Navigator.pop(context, true), child: const Text('Guardar')),
        ],
      ),
    );
    if (confirm != true || !mounted) return;

    setState(() => _guardando = true);
    try {
      await _nomina.procesar(
        usuarioId: _empleado!.id,
        pais: _pais,
        tipoPago: _tipoPago,
        salarioBase: double.tryParse(_salarioCtrl.text.replaceAll(',', '.')),
        totalBonos: double.tryParse(_bonosCtrl.text.replaceAll(',', '.')) ?? 0,
        porcentajeCobro: double.tryParse(_pctCobroCtrl.text.replaceAll(',', '.')),
        detallesPago: _detallesDesdeCampos(),
        forzarDesglose: _calculo?.advertenciaDetalle != null,
        notas: 'Pago nómina ${_tipoPago} — ${_empleado!.nombre}',
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Pago de nómina registrado')),
        );
        Navigator.pop(context, true);
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: const Color(0xFFEF4444)),
        );
      }
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return FuturisticScaffold(
      title: 'Pago de Nómina',
      accentColor: AppColors.violet,
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  DropdownButtonFormField<String>(
                    value: _pais,
                    decoration: const InputDecoration(labelText: 'País'),
                    items: const [
                      DropdownMenuItem(value: 'VE', child: Text('Venezuela')),
                      DropdownMenuItem(value: 'CO', child: Text('Colombia')),
                    ],
                    onChanged: (v) {
                      if (v == null) return;
                      setState(() {
                        _pais = v;
                        _calculo = null;
                      });
                    },
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<UsuarioEquipo>(
                    value: _empleado,
                    decoration: const InputDecoration(labelText: 'Empleado'),
                    items: _empleados
                        .map((e) => DropdownMenuItem(value: e, child: Text('${e.nombre} (${e.rol})')))
                        .toList(),
                    onChanged: (e) => setState(() {
                      _empleado = e;
                      _calculo = null;
                    }),
                  ),
                  const SizedBox(height: 12),
                  DropdownButtonFormField<String>(
                    value: _tipoPago,
                    decoration: const InputDecoration(labelText: 'Esquema de pago'),
                    items: const [
                      DropdownMenuItem(value: 'salario_basico', child: Text('Salario básico')),
                      DropdownMenuItem(value: 'comision', child: Text('Comisiones')),
                      DropdownMenuItem(value: 'mixto', child: Text('Mixto (base + comisiones)')),
                    ],
                    onChanged: (v) => setState(() {
                      _tipoPago = v ?? 'mixto';
                      _calculo = null;
                    }),
                  ),
                  const SizedBox(height: 16),
                  TextField(
                    controller: _salarioCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: _pais == 'CO' ? 'Salario base (COP)' : 'Salario base (USD ref.)',
                      hintText: _pais == 'CO' ? '2.000.000' : '240',
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _bonosCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: InputDecoration(
                      labelText: _pais == 'CO' ? 'Bonos (COP)' : 'Bonos (USD)',
                    ),
                  ),
                  const SizedBox(height: 8),
                  TextField(
                    controller: _pctCobroCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Porcentaje de cobro (opcional, cobradores)',
                      suffixText: '%',
                    ),
                  ),
                  const SizedBox(height: 12),
                  FilledButton.icon(
                    onPressed: _empleado == null || _calculando ? null : _recalcular,
                    icon: _calculando
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.calculate_rounded),
                    label: Text(_calculando ? 'Calculando…' : 'Calcular comisiones del mes'),
                  ),
                  if (_tasas != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      'Tasas: 1 USD = ${_tasas!.usdToVes.toStringAsFixed(2)} VES · '
                      '${_tasas!.usdToCop.toStringAsFixed(0)} COP',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                  if (_calculo != null) ...[
                    const SizedBox(height: 20),
                    GlassContainer(
                      accentColor: AppColors.violet,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Total a pagar: ${_fmtUsd.format(_calculo!.totalPagarUsd)}',
                            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 20),
                          ),
                          Text('Comisiones: ${_fmtUsd.format(_calculo!.totalComisiones)}'),
                          if (_calculo!.numVentas > 0)
                            Text('Ventas del periodo: ${_calculo!.numVentas}'),
                          if (_calculo!.totalCobradoUsd > 0)
                            Text('Cobrado: ${_fmtUsd.format(_calculo!.totalCobradoUsd)}'),
                          Text(
                            'Equivalente local (${_calculo!.monedaPrincipal}): '
                            '${_calculo!.totalPagarLocal.toStringAsFixed(2)}',
                          ),
                        ],
                      ),
                    ),
                    if (_pais == 'VE') ...[
                      const SizedBox(height: 16),
                      const Text('Desglose multi-moneda (Venezuela)', style: TextStyle(fontWeight: FontWeight.w700)),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _usdCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Monto en USD', prefixText: r'$ '),
                        onChanged: (v) => _onCambioMonedaLocal('USD', v),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _vesCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Monto en VES (Bs.)'),
                        onChanged: (v) => _onCambioMonedaLocal('VES', v),
                      ),
                      const SizedBox(height: 8),
                      TextField(
                        controller: _copCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        decoration: const InputDecoration(labelText: 'Monto en COP'),
                        onChanged: (v) => _onCambioMonedaLocal('COP', v),
                      ),
                    ],
                    const SizedBox(height: 24),
                    FilledButton.icon(
                      onPressed: _guardando ? null : _guardar,
                      icon: _guardando
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.save_rounded),
                      label: Text(_guardando ? 'Guardando…' : 'Guardar pago'),
                    ),
                  ],
                ],
              ),
            ),
    );
  }
}
