import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';
import '../services/tasas_service.dart';
import '../services/tasas_login_cache.dart';
import '../theme/app_theme.dart';
import '../utils/conversion_helper.dart';
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
  String _monedaOrigen = 'usd';
  DesgloseMoneda? _desglose;
  bool _guardando = false;
  bool _sincronizando = false;
  Map<String, dynamic>? _ultimasFuentes;

  @override
  void initState() {
    super.initState();
    _montoConvCtrl.addListener(_recalcularDesglose);
    _cargar();
  }

  void _recalcularDesglose() {
    if (_ultima == null) return;
    final monto = double.tryParse(_montoConvCtrl.text.replaceAll(',', '.'));
    if (monto == null || monto <= 0) {
      if (_desglose != null) setState(() => _desglose = null);
      return;
    }
    setState(() {
      _desglose = calcularDesglose(
        monto: monto,
        monedaOrigen: _monedaOrigen,
        tasaBcv: _ultima!.usdBcvBs,
        tasaParalelo: _ultima!.usdParaleloBs,
        copPorUsd: _ultima!.copUsd,
        tipoTasaActiva: _tipoTasa,
      );
    });
  }

  @override
  void dispose() {
    _bcvCtrl.dispose();
    _paraleloCtrl.dispose();
    _copCtrl.dispose();
    _montoConvCtrl.dispose();
    super.dispose();
  }

  void _aplicarTasaEnPantalla(TasaCambioDetalle t) {
    setState(() {
      _ultima = t;
      _error = null;
      _bcvCtrl.text = t.usdBcvBs.toString();
      _paraleloCtrl.text = t.usdParaleloBs.toString();
      _copCtrl.text = t.copUsd.toString();
    });
    _recalcularDesglose();
  }

  Future<void> _cargar() async {
    setState(() {
      _cargando = true;
      _error = null;
    });
    try {
      final t = await context.read<AppState>().tasas.ultima();
      if (!mounted) return;
      _aplicarTasaEnPantalla(t);
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _ultima = null;
        _error = e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _ultima = null;
        _error = e.toString();
      });
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _persistirCacheLogin(TasaCambioDetalle t) async {
    await TasasLoginCache.guardar(
      usdBcvBs: t.usdBcvBs,
      usdParaleloBs: t.usdParaleloBs,
    );
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
      final t = await context.read<AppState>().tasas.registrar(
            usdBcvBs: bcv,
            usdParaleloBs: par,
            copUsd: cop,
          );
      if (!mounted) return;
      _aplicarTasaEnPantalla(t);
      await _persistirCacheLogin(t);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Tasa registrada correctamente'),
          backgroundColor: AppColors.emerald,
        ),
      );
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red),
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

  Future<void> _sincronizarAuto() async {
    setState(() => _sincronizando = true);
    try {
      final result = await context.read<AppState>().tasas.sincronizarAuto();
      if (!mounted) return;

      TasaCambioDetalle? t = result.tasa;
      if (t == null && result.usdBcvBs > 0) {
        t = TasaCambioDetalle(
          id: '',
          usdBcvBs: result.usdBcvBs,
          usdParaleloBs: result.usdParaleloBs,
          copUsd: result.copUsd,
          eurBs: 0,
          momento: result.momento,
          fecha: DateTime.now().toIso8601String(),
        );
      }
      if (t != null) {
        _aplicarTasaEnPantalla(t);
        await _persistirCacheLogin(t);
      } else {
        await _cargar();
      }

      setState(() => _ultimasFuentes = result.fuentes);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            result.exito
                ? 'Tasas actualizadas (${result.momento}): BCV ${result.usdBcvBs.toStringAsFixed(2)}'
                : result.mensaje,
          ),
          backgroundColor: result.exito ? AppColors.emerald : Colors.orange,
        ),
      );
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
        );
      }
    } finally {
      if (mounted) setState(() => _sincronizando = false);
    }
  }

  Widget _filaDesglose(String etiqueta, String valor, {Color? color}) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: Text(etiqueta, style: TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ),
          Text(
            valor,
            style: TextStyle(
              fontWeight: FontWeight.w700,
              fontSize: 15,
              color: color ?? AppColors.textPrimary,
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final fmt = NumberFormat('#,##0.00');
    final state = context.watch<AppState>();
    final esDueno = state.esDueno;
    final puedeSincronizar = state.puedeOperaciones;

    return FuturisticScaffold(
      title: 'Tasas de Cambio',
      accentColor: AppColors.amber,
      actions: [
        if (puedeSincronizar)
          IconButton(
            icon: _sincronizando
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.cloud_sync_rounded),
            tooltip: 'Sincronizar tasas',
            onPressed: _sincronizando ? null : _sincronizarAuto,
          ),
        IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar),
      ],
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
                        Text('Momento: ${_ultima!.momento}'),
                        Text('Actualizada: ${_ultima!.fecha.substring(0, 16)}'),
                      ],
                    ),
                  ),
                if (puedeSincronizar) ...[
                  const SizedBox(height: 12),
                  SizedBox(
                    width: double.infinity,
                    child: FilledButton.icon(
                      onPressed: _sincronizando ? null : _sincronizarAuto,
                      icon: _sincronizando
                          ? const SizedBox(
                              width: 18,
                              height: 18,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.cloud_download_rounded),
                      label: Text(
                        _sincronizando ? 'Obteniendo tasas...' : 'Sincronizar tasas automáticamente',
                      ),
                      style: FilledButton.styleFrom(
                        backgroundColor: AppColors.neonBlue,
                        foregroundColor: AppColors.bgDeep,
                        minimumSize: const Size(double.infinity, 48),
                      ),
                    ),
                  ),
                  if (_ultimasFuentes != null) ...[
                    const SizedBox(height: 8),
                    Text(
                      'Fuentes: BCV=${_ultimasFuentes!['usd_bcv']}, '
                      'Paralelo=${_ultimasFuentes!['usd_paralelo']}, '
                      'COP=${_ultimasFuentes!['cop_usd']}',
                      style: Theme.of(context).textTheme.bodySmall,
                    ),
                  ],
                ],
                if (_ultima == null && _error != null) ...[
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
                const SectionTitle(title: 'Desglose automático y ejemplo rápido'),
                GlassContainer(
                  padding: const EdgeInsets.all(16),
                  accentColor: AppColors.emerald,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      TextField(
                        controller: _montoConvCtrl,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        style: const TextStyle(color: AppColors.textPrimary, fontSize: 18),
                        decoration: InputDecoration(
                          labelText: 'Monto a convertir',
                          prefixIcon: const Icon(Icons.calculate_outlined),
                          suffixText: etiquetaMoneda(_monedaOrigen),
                        ),
                      ),
                      const SizedBox(height: 12),
                      Row(
                        children: [
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              value: _monedaOrigen,
                              decoration: const InputDecoration(labelText: 'Moneda ingresada'),
                              dropdownColor: AppColors.bgElevated,
                              items: const [
                                DropdownMenuItem(value: 'usd', child: Text('USD — Dólares')),
                                DropdownMenuItem(value: 'ves', child: Text('VES — Bolívares')),
                                DropdownMenuItem(value: 'cop', child: Text('COP — Pesos')),
                              ],
                              onChanged: (v) {
                                setState(() => _monedaOrigen = v ?? 'usd');
                                _recalcularDesglose();
                              },
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: DropdownButtonFormField<String>(
                              value: _tipoTasa,
                              decoration: const InputDecoration(labelText: 'Tasa VES activa'),
                              dropdownColor: AppColors.bgElevated,
                              items: const [
                                DropdownMenuItem(value: 'bcv', child: Text('BCV')),
                                DropdownMenuItem(value: 'paralelo', child: Text('Paralelo')),
                              ],
                              onChanged: (v) {
                                setState(() => _tipoTasa = v ?? 'bcv');
                                _recalcularDesglose();
                              },
                            ),
                          ),
                        ],
                      ),
                      if (_desglose != null) ...[
                        const SizedBox(height: 16),
                        const Divider(height: 1),
                        const SizedBox(height: 12),
                        Text(
                          _monedaOrigen == 'usd'
                              ? 'Equivalentes de \$${fmt.format(_desglose!.montoOrigen)} USD'
                              : 'Equivalente en USD y otras monedas',
                          style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                        ),
                        const SizedBox(height: 8),
                        _filaDesglose(
                          '→ Bolívares BCV',
                          '${fmt.format(_desglose!.vesBcv)} Bs',
                          color: AppColors.amber,
                        ),
                        _filaDesglose(
                          '→ Bolívares Paralelo',
                          '${fmt.format(_desglose!.vesParalelo)} Bs',
                          color: AppColors.violet,
                        ),
                        _filaDesglose(
                          '→ Pesos Colombianos',
                          '${NumberFormat('#,##0').format(_desglose!.cop)} COP',
                          color: AppColors.neonBlue,
                        ),
                        if (_monedaOrigen != 'usd') ...[
                          const Divider(height: 24),
                          _filaDesglose(
                            '≈ Dólares (USD)',
                            '\$${fmt.format(_desglose!.usd)}',
                            color: AppColors.emerald,
                          ),
                        ],
                        const SizedBox(height: 8),
                        Text(
                          'Tasa BCV: ${fmt.format(_ultima!.usdBcvBs)} · '
                          'Paralelo: ${fmt.format(_ultima!.usdParaleloBs)} · '
                          'COP/USD: ${fmt.format(_ultima!.copUsd)}',
                          style: Theme.of(context).textTheme.bodySmall,
                        ),
                      ] else if (_ultima != null)
                        Padding(
                          padding: const EdgeInsets.only(top: 12),
                          child: Text(
                            'Ingresa un monto para ver el desglose instantáneo',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                        ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}
