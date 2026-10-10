import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../providers/app_state.dart';
import '../services/cobros_service.dart';
import '../services/tasas_service.dart';
import '../theme/app_theme.dart';
import '../utils/conversion_helper.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/glass_list_tile.dart';
import '../widgets/transferencia_pago.dart';

class NuevoCobroScreen extends StatefulWidget {
  const NuevoCobroScreen({super.key});

  @override
  State<NuevoCobroScreen> createState() => _NuevoCobroScreenState();
}

class _NuevoCobroScreenState extends State<NuevoCobroScreen> {
  List<VentaPendiente> _pendientes = [];
  TasaCambioDetalle? _tasa;

  VentaPendiente? _venta;
  String _moneda = 'usd';
  bool _esTransferencia = false;
  final _montoCtrl = TextEditingController();
  final _referenciaCtrl = TextEditingController();
  String? _comprobanteBase64;
  String? _comprobanteNombre;
  bool _cargando = true;
  bool _guardando = false;

  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _fmtNum = NumberFormat('#,##0.00');

  @override
  void initState() {
    super.initState();
    _montoCtrl.addListener(() => setState(() {}));
    _cargar();
  }

  @override
  void dispose() {
    _montoCtrl.dispose();
    _referenciaCtrl.dispose();
    super.dispose();
  }

  double get _montoIngresado =>
      double.tryParse(_montoCtrl.text.replaceAll(',', '.')) ?? 0;

  double get _montoUsdEquivalente {
    if (_tasa == null || _montoIngresado <= 0) return 0;
    return abonoAMontoUsd(
      monto: _montoIngresado,
      moneda: _moneda,
      tasaBcv: _tasa!.usdBcvBs,
      copPorUsd: _tasa!.copUsd,
    );
  }

  Future<void> _cargar() async {
    final state = context.read<AppState>();
    try {
      final results = await Future.wait([
        state.cobros.ventasPendientes(),
        state.tasas.ultima(),
      ]);
      _pendientes = results[0] as List<VentaPendiente>;
      _tasa = results[1] as TasaCambioDetalle;
      if (_pendientes.isNotEmpty) {
        _venta = _pendientes.first;
        _actualizarMontoSugerido();
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

  void _actualizarMontoSugerido() {
    if (_venta == null || _tasa == null) return;
    final saldoUsd = _venta!.saldoPendienteUsd;
    switch (_moneda) {
      case 'ves':
        _montoCtrl.text = (saldoUsd * _tasa!.usdBcvBs).toStringAsFixed(2);
      case 'cop':
        _montoCtrl.text = (saldoUsd * _tasa!.copUsd).toStringAsFixed(0);
      default:
        _montoCtrl.text = saldoUsd.toStringAsFixed(2);
    }
  }

  void _onVentaChanged(VentaPendiente? v) {
    setState(() {
      _venta = v;
      _actualizarMontoSugerido();
    });
  }

  void _onMonedaChanged(String? v) {
    setState(() {
      _moneda = v ?? 'usd';
      _actualizarMontoSugerido();
    });
  }

  Future<void> _elegirComprobante() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1600,
      imageQuality: 75,
    );
    if (file == null) return;
    final bytes = await file.readAsBytes();
    if (!mounted) return;
    setState(() {
      _comprobanteBase64 = base64Encode(bytes);
      _comprobanteNombre = file.name;
    });
  }

  Future<void> _registrar() async {
    if (_venta == null || _tasa == null) return;
    final montoUsd = _montoUsdEquivalente;
    if (montoUsd <= 0) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ingresa un monto válido')),
      );
      return;
    }
    if (montoUsd > _venta!.saldoPendienteUsd + 0.01) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            'El abono equivale a ${_fmt.format(montoUsd)} USD. '
            'Máximo saldo: ${_fmt.format(_venta!.saldoPendienteUsd)}',
          ),
        ),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      final cobro = await context.read<AppState>().cobros.registrarCobro(
            ventaId: _venta!.id,
            montoUsd: montoUsd,
            monedaPago: monedaPagoBackend(_moneda),
            tasaUsd: _tasa!.usdBcvBs,
            tasaEur: _tasa!.eurBs,
            cobroId: const Uuid().v4(),
            esTransferencia: _esTransferencia,
            referenciaPago: _esTransferencia ? _referenciaCtrl.text : null,
            comprobanteBase64: _esTransferencia ? _comprobanteBase64 : null,
          );
      if (!mounted) return;
      final porVerificar = cobro.estadoVenta == 'por_verificar';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            porVerificar
                ? 'Cobro registrado. La venta quedó Pagada (Por Verificar).'
                : 'Cobro registrado: ${_fmt.format(montoUsd)} USD '
                    '(${_fmtNum.format(_montoIngresado)} ${etiquetaMoneda(_moneda)})',
          ),
        ),
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
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      DropdownButtonFormField<String>(
                        value: _moneda,
                        decoration: const InputDecoration(
                          labelText: 'Moneda del abono',
                          prefixIcon: Icon(Icons.currency_exchange_rounded),
                        ),
                        dropdownColor: AppColors.bgElevated,
                        items: CobrosService.monedasAbono
                            .map((m) => DropdownMenuItem(value: m.$1, child: Text(m.$2)))
                            .toList(),
                        onChanged: _onMonedaChanged,
                      ),
                      const SizedBox(height: 16),
                      TextField(
                        controller: _montoCtrl,
                        enabled: true,
                        keyboardType: const TextInputType.numberWithOptions(decimal: true),
                        style: const TextStyle(color: AppColors.textPrimary, fontSize: 18),
                        decoration: InputDecoration(
                          labelText: 'Monto en ${etiquetaMoneda(_moneda)}',
                          prefixIcon: const Icon(Icons.attach_money_rounded),
                          helperText: _venta != null
                              ? 'Saldo pendiente: ${_fmt.format(_venta!.saldoPendienteUsd)} USD'
                              : null,
                          filled: true,
                          fillColor: AppColors.bgElevated.withValues(alpha: 0.5),
                        ),
                      ),
                      if (_montoIngresado > 0 && _tasa != null) ...[
                        const SizedBox(height: 16),
                        Container(
                          width: double.infinity,
                          padding: const EdgeInsets.all(14),
                          decoration: BoxDecoration(
                            color: AppColors.emerald.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(color: AppColors.emerald.withValues(alpha: 0.35)),
                          ),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Text(
                                'Equivalencia para el crédito',
                                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 13),
                              ),
                              const SizedBox(height: 6),
                              Text(
                                '≈ ${_fmt.format(_montoUsdEquivalente)} USD se restarán del saldo',
                                style: const TextStyle(
                                  color: AppColors.emerald,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 16,
                                ),
                              ),
                              if (_moneda != 'usd')
                                Text(
                                  'Tasa BCV: ${_fmtNum.format(_tasa!.usdBcvBs)} Bs/USD · '
                                  'COP/USD: ${_fmtNum.format(_tasa!.copUsd)}',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                            ],
                          ),
                        ),
                      ],
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Pago por transferencia'),
                        subtitle: Text(
                          _venta == null
                              ? 'Muestra la cuenta de la empresa y adjunta el comprobante'
                              : _venta!.frecuenciaPago == 'contado'
                                  ? 'Transferencia para venta de contado'
                                  : 'Transferencia para venta a crédito (${_venta!.tipoCredito})',
                        ),
                        value: _esTransferencia,
                        onChanged: (v) => setState(() => _esTransferencia = v),
                      ),
                      if (_esTransferencia) ...[
                        FaseTransferencia(
                          esCredito: _venta != null && _venta!.frecuenciaPago != 'contado',
                          detalleCredito: _venta != null && _venta!.frecuenciaPago != 'contado'
                              ? _venta!.tipoCredito
                              : null,
                          referenciaCtrl: _referenciaCtrl,
                          comprobanteNombre: _comprobanteNombre,
                          onElegirFoto: _elegirComprobante,
                          onQuitarFoto: () => setState(() {
                            _comprobanteBase64 = null;
                            _comprobanteNombre = null;
                          }),
                        ),
                      ],
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
                              Text(
                                'BCV: ${_fmtNum.format(_tasa!.usdBcvBs)} · '
                                'Paralelo: ${_fmtNum.format(_tasa!.usdParaleloBs)} · '
                                'COP/USD: ${_fmtNum.format(_tasa!.copUsd)}',
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                if (_moneda == 'usd')
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
