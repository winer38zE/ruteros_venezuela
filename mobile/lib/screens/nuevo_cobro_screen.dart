import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:flutter/services.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:uuid/uuid.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';
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
  String _canalCobro = 'efectivo';

  bool get _pagoElectronico => _canalCobro == 'transferencia' || _canalCobro == 'pago_movil';

  bool get _tieneFotoComprobante =>
      _comprobanteBytes != null && _comprobanteBytes!.isNotEmpty;
  String? _cuentaBancariaId;
  final _montoCtrl = TextEditingController();
  final _referenciaCtrl = TextEditingController();
  String? _comprobanteBase64;
  Uint8List? _comprobanteBytes;
  String? _comprobanteNombre;
  bool _cargando = true;
  bool _guardando = false;
  String? _errorCarga;

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

  /// Sin permiso o sin señal el cobro sigue. El servidor lo marca sin ubicación.
  Future<({double lat, double lng, double precision})?> _ubicacionSiHay() async {
    try {
      final enabled = await Geolocator.isLocationServiceEnabled();
      if (!enabled) return null;
      var permiso = await Geolocator.checkPermission();
      if (permiso == LocationPermission.denied) {
        permiso = await Geolocator.requestPermission();
      }
      if (permiso == LocationPermission.denied || permiso == LocationPermission.deniedForever) {
        return null;
      }
      final pos = await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.high,
          timeLimit: Duration(seconds: 8),
        ),
      );
      return (lat: pos.latitude, lng: pos.longitude, precision: pos.accuracy);
    } catch (_) {
      return null;
    }
  }

  String _fechaCorta(String? iso) {
    if (iso == null || iso.length < 10) return 'sin fecha';
    return iso.substring(0, 10);
  }

  String _captionComprobante() {
    final cliente = _venta?.clienteNombre.trim();
    final nombre = (cliente == null || cliente.isEmpty) ? 'Cliente' : cliente;
    final medio = _canalCobro == 'pago_movil' ? 'pago móvil' : 'transferencia';
    final ref = _referenciaCtrl.text.trim();
    final referencia = ref.isEmpty ? '' : ' - Referencia: $ref';
    return 'Pago por $medio - Cliente: $nombre - Monto: ${_fmt.format(_montoUsdEquivalente)} dólares$referencia';
  }

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
      _errorCarga = null;
      if (_pendientes.isNotEmpty) {
        _venta = _pendientes.first;
        _actualizarMontoSugerido();
      }
    } catch (e) {
      _errorCarga = '$e';
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

  Future<void> _registrar() async {
    if (_pagoElectronico && !_tieneFotoComprobante) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Por favor adjunta el comprobante antes de continuar')),
      );
      return;
    }
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
            'El abono equivale a ${_fmt.format(montoUsd)} dólares. '
            'Máximo saldo: ${_fmt.format(_venta!.saldoPendienteUsd)}',
          ),
        ),
      );
      return;
    }

    setState(() => _guardando = true);
    try {
      final gps = await _ubicacionSiHay();
      final cobro = await context.read<AppState>().cobros.registrarCobro(
            ventaId: _venta!.id,
            montoUsd: montoUsd,
            monedaPago: monedaPagoBackend(_moneda),
            tasaUsd: _tasa!.usdBcvBs,
            tasaEur: _tasa!.eurBs,
            cobroId: const Uuid().v4(),
            latitud: gps?.lat,
            longitud: gps?.lng,
            precisionMetros: gps?.precision,
            esTransferencia: _canalCobro != 'efectivo',
            canal: _canalCobro == 'efectivo' ? null : _canalCobro,
            referenciaPago: _canalCobro != 'efectivo' ? _referenciaCtrl.text : null,
            comprobanteBase64: _canalCobro != 'efectivo' ? _comprobanteBase64 : null,
            cuentaBancariaId: _canalCobro != 'efectivo' ? _cuentaBancariaId : null,
          );
      if (!mounted) return;
      final porVerificar = cobro.estadoVenta == 'por_verificar';
      final msg = porVerificar
          ? 'Cobro registrado. La venta quedó Pagada (Por Verificar).'
          : 'Cobro registrado: ${_fmt.format(montoUsd)} dólares '
              '(${_fmtNum.format(_montoIngresado)} ${etiquetaMoneda(_moneda)})';
      if (_canalCobro != 'efectivo') {
        final cobros = context.read<AppState>().cobros;
        final canal = _canalCobro;
        await mostrarEnvioComprobanteWhatsapp(
          context: context,
          resumen: msg,
          tieneFoto: _comprobanteBase64 != null && _comprobanteBase64!.isNotEmpty,
          onEnviar: () => cobros.enviarComprobanteWhatsapp(cobro.id, metodo: canal),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(msg)));
      }
      if (!mounted) return;
      Navigator.pop(context, true);
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: const Color(0xFFEF4444)),
        );
      }
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
            onPressed: _guardando || _venta == null || (_pagoElectronico && !_tieneFotoComprobante)
                ? null
                : _registrar,
            icon: _guardando
                ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                : const Icon(Icons.check_circle_rounded),
            label: Text(_guardando ? 'Registrando...' : 'Registrar Cobro'),
            style: FilledButton.styleFrom(
              minimumSize: const Size(double.infinity, 52),
              backgroundColor: _pagoElectronico && !_tieneFotoComprobante ? Colors.grey : AppColors.neonCyan,
              foregroundColor: _pagoElectronico && !_tieneFotoComprobante ? Colors.white70 : AppColors.bgDeep,
              disabledBackgroundColor: Colors.grey,
              disabledForegroundColor: Colors.white70,
            ),
          ),
        ),
      ),
      body: _errorCarga != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Text(_errorCarga!, textAlign: TextAlign.center, style: const TextStyle(color: Color(0xFFEF4444))),
              ),
            )
          : _pendientes.isEmpty
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
                      '${_fechaCorta(v.fecha)} · ${v.estado}',
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
                              ? 'Saldo pendiente: ${_fmt.format(_venta!.saldoPendienteUsd)} dólares'
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
                                '≈ ${_fmt.format(_montoUsdEquivalente)} dólares se restarán del saldo',
                                style: const TextStyle(
                                  color: AppColors.emerald,
                                  fontWeight: FontWeight.w800,
                                  fontSize: 16,
                                ),
                              ),
                              if (_moneda != 'usd')
                                Text(
                                  'Tasa BCV: ${_fmtNum.format(_tasa!.usdBcvBs)} bolívares por dólar · '
                                  'pesos por dólar: ${_fmtNum.format(_tasa!.copUsd)}',
                                  style: Theme.of(context).textTheme.bodySmall,
                                ),
                            ],
                          ),
                        ),
                      ],
                      DropdownButtonFormField<String>(
                        value: _canalCobro,
                        decoration: const InputDecoration(
                          labelText: 'Medio de pago en Venezuela',
                          prefixIcon: Icon(Icons.account_balance_rounded),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'efectivo', child: Text('Efectivo')),
                          DropdownMenuItem(value: 'transferencia', child: Text('Transferencia bancaria')),
                          DropdownMenuItem(value: 'pago_movil', child: Text('Pago móvil')),
                        ],
                        onChanged: (v) => setState(() {
                          _canalCobro = v ?? 'efectivo';
                          _cuentaBancariaId = null;
                          _comprobanteBase64 = null;
                          _comprobanteBytes = null;
                          _comprobanteNombre = null;
                        }),
                      ),
                      if (_canalCobro != 'efectivo') ...[
                        FaseTransferencia(
                          esCredito: _venta != null && _venta!.frecuenciaPago != 'contado',
                          canal: _canalCobro,
                          detalleCredito: _venta != null && _venta!.frecuenciaPago != 'contado'
                              ? _venta!.tipoCredito
                              : null,
                          referenciaCtrl: _referenciaCtrl,
                          onComprobante: (base64, nombre) {
                            setState(() {
                              _comprobanteBase64 = base64;
                              _comprobanteNombre = nombre;
                              _comprobanteBytes =
                                  (base64 == null || base64.isEmpty) ? null : base64Decode(base64);
                            });
                          },
                          onCuentaChanged: (cuenta) => _cuentaBancariaId = cuenta?.id,
                        ),
                        const SizedBox(height: 12),
                        BotonEnviarComprobanteWhatsapp(
                          imagen: _comprobanteBytes,
                          nombreArchivo: _comprobanteNombre,
                          caption: _captionComprobante(),
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
                                'pesos por dólar: ${_fmtNum.format(_tasa!.copUsd)}',
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
