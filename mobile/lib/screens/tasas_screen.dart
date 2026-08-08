import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/tasas_service.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';

class TasasScreen extends StatefulWidget {
  const TasasScreen({super.key});

  @override
  State<TasasScreen> createState() => _TasasScreenState();
}

class _TasasScreenState extends State<TasasScreen> {
  TasaCambioDetalle? _ultima;
  bool _cargando = true;
  String? _error;

  final _bcvCtrl = TextEditingController();
  final _paraleloCtrl = TextEditingController();
  final _copCtrl = TextEditingController();
  final _montoConvCtrl = TextEditingController(text: '100');
  String _tipoTasa = 'bcv';
  ConversionResult? _conversion;
  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  @override
  void dispose() {
    _bcvCtrl.dispose();
    _paraleloCtrl.dispose();
    _copCtrl.dispose();
    _montoConvCtrl.dispose();
    super.dispose();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      _ultima = await context.read<AppState>().tasas.ultima();
      _bcvCtrl.text = _ultima!.usdBcvBs.toString();
      _paraleloCtrl.text = _ultima!.usdParaleloBs.toString();
      _copCtrl.text = _ultima!.copUsd.toString();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _guardarTasa() async {
    final bcv = double.tryParse(_bcvCtrl.text.replaceAll(',', '.'));
    final par = double.tryParse(_paraleloCtrl.text.replaceAll(',', '.'));
    final cop = double.tryParse(_copCtrl.text.replaceAll(',', '.'));
    if (bcv == null || par == null || cop == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Completa todas las tasas')),
      );
      return;
    }
    setState(() => _guardando = true);
    try {
      _ultima = await context.read<AppState>().tasas.registrar(
            usdBcvBs: bcv,
            usdParaleloBs: par,
            copUsd: cop,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Tasa registrada correctamente')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _guardando = false);
    }
  }

  Future<void> _probarConversion() async {
    final monto = double.tryParse(_montoConvCtrl.text.replaceAll(',', '.'));
    if (monto == null) return;
    try {
      _conversion = await context.read<AppState>().tasas.convertir(
            monto: monto,
            monedaOrigen: 'usd',
            monedaDestino: 'ves',
            tipoTasaUsd: _tipoTasa,
          );
      setState(() {});
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
    final fmt = NumberFormat('#,##0.00');
    final esDueno = context.watch<AppState>().esDueno;

    return FuturisticScaffold(
      title: 'Tasas de Cambio',
      accentColor: AppColors.amber,
      actions: [IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar)],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(16),
              children: [
                if (_ultima != null)
                  GlassContainer(
                    accentColor: AppColors.amber,
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Tasa activa del día', style: TextStyle(fontWeight: FontWeight.w800)),
                        const SizedBox(height: 8),
                        Text('BCV: ${fmt.format(_ultima!.usdBcvBs)} Bs/USD'),
                        Text('Paralelo: ${fmt.format(_ultima!.usdParaleloBs)} Bs/USD'),
                        Text('COP/USD: ${fmt.format(_ultima!.copUsd)}'),
                        Text('Actualizada: ${_ultima!.fecha.substring(0, 16)}'),
                      ],
                    ),
                  ),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: Colors.red)),
                ],
                if (esDueno) ...[
                  const SizedBox(height: 20),
                  const SectionTitle(title: 'Registrar tasa diaria'),
                  GlassContainer(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        TextField(
                          controller: _bcvCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'USD BCV → VES'),
                        ),
                        TextField(
                          controller: _paraleloCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'USD Paralelo → VES'),
                        ),
                        TextField(
                          controller: _copCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(labelText: 'COP por 1 USD'),
                        ),
                        const SizedBox(height: 12),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton(
                            onPressed: _guardando ? null : _guardarTasa,
                            child: _guardando
                                ? const SizedBox(
                                    width: 20,
                                    height: 20,
                                    child: CircularProgressIndicator(strokeWidth: 2),
                                  )
                                : const Text('Guardar tasa del día'),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 20),
                const SectionTitle(title: 'Calculadora rápida'),
                GlassContainer(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      TextField(
                        controller: _montoConvCtrl,
                        keyboardType: TextInputType.number,
                        decoration: const InputDecoration(labelText: 'Monto USD'),
                      ),
                      DropdownButtonFormField<String>(
                        value: _tipoTasa,
                        decoration: const InputDecoration(labelText: 'Tasa USD activa'),
                        items: const [
                          DropdownMenuItem(value: 'bcv', child: Text('BCV')),
                          DropdownMenuItem(value: 'paralelo', child: Text('Paralelo')),
                        ],
                        onChanged: (v) => setState(() => _tipoTasa = v ?? 'bcv'),
                      ),
                      const SizedBox(height: 8),
                      FilledButton(
                        onPressed: _probarConversion,
                        child: const Text('Convertir a VES'),
                      ),
                      if (_conversion != null) ...[
                        const SizedBox(height: 12),
                        Text(
                          '\$${_conversion!.montoOrigen.toStringAsFixed(2)} USD = '
                          '${fmt.format(_conversion!.montoDestino)} VES',
                          style: const TextStyle(fontWeight: FontWeight.w700, color: AppColors.emerald),
                        ),
                      ],
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
