import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/app_state.dart';
import '../services/api_service.dart';
import '../services/cobros_service.dart';
import '../services/tasas_service.dart';
import '../theme/app_theme.dart';
import '../utils/conversion_helper.dart';
import '../widgets/futuristic_screen.dart';
import '../widgets/glass_container.dart';
import '../widgets/gps_location_capture.dart';
import '../widgets/asistente_ruta_widget.dart';
import '../widgets/enviar_recibo_button.dart';
import 'cartera_critica_screen.dart';

class PanelCobranzaScreen extends StatefulWidget {
  const PanelCobranzaScreen({super.key});

  @override
  State<PanelCobranzaScreen> createState() => _PanelCobranzaScreenState();
}

class _PanelCobranzaScreenState extends State<PanelCobranzaScreen> {
  List<FilaCobranza> _filas = [];
  bool _cargando = true;
  String? _error;
  final _fmt = NumberFormat.currency(symbol: '\$', decimalDigits: 2);
  final _fmtFecha = DateFormat('dd/MM/yyyy');

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
      _filas = await context.read<AppState>().cobros.panelCobranza();
    } catch (e) {
      _error = e.toString();
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  Future<void> _llamar(String? telefono) async {
    if (telefono == null || telefono.isEmpty) return;
    final uri = Uri.parse('tel:$telefono');
    if (await canLaunchUrl(uri)) await launchUrl(uri);
  }

  Future<void> _whatsapp(String? telefono) async {
    if (telefono == null || telefono.isEmpty) return;
    final digits = telefono.replaceAll(RegExp(r'\D'), '');
    final uri = Uri.parse('https://wa.me/$digits');
    if (await canLaunchUrl(uri)) await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  Color _colorEstadoCuota(String estado) {
    switch (estado) {
      case 'Pagado':
        return AppColors.emerald;
      case 'Vencido':
        return Colors.red;
      case 'Parcial':
        return AppColors.amber;
      default:
        return AppColors.neonBlue;
    }
  }

  Future<void> _abonoRapido(FilaCobranza fila, {double? montoSugeridoUsd}) async {
    TasaCambioDetalle? tasa;
    try {
      tasa = await context.read<AppState>().tasas.ultima();
    } catch (_) {}

    final sugerido = montoSugeridoUsd ??
        (fila.montoProximaCuotaUsd > 0 ? fila.montoProximaCuotaUsd : fila.saldoPendienteUsd);
    final montoCtrl = TextEditingController(text: sugerido.toStringAsFixed(2));
    var moneda = 'usd';

    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) {
          final montoIngresado = double.tryParse(montoCtrl.text.replaceAll(',', '.')) ?? 0;
          final montoUsd = tasa != null && montoIngresado > 0
              ? abonoAMontoUsd(
                  monto: montoIngresado,
                  moneda: moneda,
                  tasaBcv: tasa.usdBcvBs,
                  copPorUsd: tasa.copUsd,
                )
              : montoIngresado;

          return AlertDialog(
            backgroundColor: AppColors.bgCard,
            title: const Text('Registrar abono'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(fila.clienteNombre, style: const TextStyle(fontWeight: FontWeight.w700)),
                Text(fila.productosResumen),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  initialValue: moneda,
                  decoration: const InputDecoration(labelText: 'Moneda del abono'),
                  dropdownColor: AppColors.bgElevated,
                  items: CobrosService.monedasAbono
                      .map((m) => DropdownMenuItem(value: m.$1, child: Text(m.$2)))
                      .toList(),
                  onChanged: (v) {
                    setDialogState(() {
                      moneda = v ?? 'usd';
                      if (tasa != null) {
                        switch (moneda) {
                          case 'ves':
                            montoCtrl.text = (sugerido * tasa.usdBcvBs).toStringAsFixed(2);
                          case 'cop':
                            montoCtrl.text = (sugerido * tasa.copUsd).toStringAsFixed(0);
                          default:
                            montoCtrl.text = sugerido.toStringAsFixed(2);
                        }
                      }
                    });
                  },
                ),
                const SizedBox(height: 8),
                TextField(
                  controller: montoCtrl,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: InputDecoration(
                    labelText: 'Monto en ${etiquetaMoneda(moneda)}',
                    helperText: 'Saldo: ${_fmt.format(fila.saldoPendienteUsd)} dólares',
                  ),
                  onChanged: (_) => setDialogState(() {}),
                ),
                if (montoIngresado > 0) ...[
                  const SizedBox(height: 8),
                  Text(
                    '≈ ${_fmt.format(montoUsd)} dólares al saldo',
                    style: const TextStyle(color: AppColors.emerald, fontWeight: FontWeight.w700),
                  ),
                ],
              ],
            ),
            actions: [
              TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Cancelar')),
              FilledButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Registrar')),
            ],
          );
        },
      ),
    );
    if (ok != true || !mounted) return;

    final montoUsd = tasa != null
        ? abonoAMontoUsd(
            monto: double.tryParse(montoCtrl.text.replaceAll(',', '.')) ?? 0,
            moneda: moneda,
            tasaBcv: tasa.usdBcvBs,
            copPorUsd: tasa.copUsd,
          )
        : double.tryParse(montoCtrl.text.replaceAll(',', '.')) ?? 0;
    if (montoUsd <= 0) return;

    try {
      final tasaFinal = tasa ?? await context.read<AppState>().tasas.ultima();
      await context.read<AppState>().cobros.registrarCobro(
            ventaId: fila.id,
            montoUsd: montoUsd,
            monedaPago: monedaPagoBackend(moneda),
            tasaUsd: tasaFinal.usdBcvBs,
            tasaEur: tasaFinal.eurBs,
          );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Abono de ${_fmt.format(montoUsd)} dólares registrado')),
        );
        _cargar();
      }
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message), backgroundColor: Colors.red),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('$e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  Widget _resumenChip(String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 10),
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.12),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: color.withValues(alpha: 0.3)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(label, style: TextStyle(fontSize: 11, color: AppColors.textMuted)),
            const SizedBox(height: 4),
            Text(value, style: TextStyle(fontWeight: FontWeight.w800, color: color, fontSize: 14)),
          ],
        ),
      ),
    );
  }

  Widget _carpetaMoraCritica() {
    return GlassContainer(
      margin: const EdgeInsets.only(bottom: 14),
      accentColor: const Color(0xFFEF4444),
      onTap: () {
        Navigator.push(
          context,
          MaterialPageRoute(builder: (_) => const CarteraCriticaScreen()),
        );
      },
      child: const Row(
        children: [
          Icon(Icons.folder_special_rounded, color: Color(0xFFEF4444)),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Carpeta de mora +3 semanas',
                  style: TextStyle(fontWeight: FontWeight.w800),
                ),
                Text(
                  'Clientes con más de 21 días y notas de seguimiento',
                  style: TextStyle(color: AppColors.textMuted, fontSize: 12),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right_rounded, color: AppColors.textMuted),
        ],
      ),
    );
  }

  Widget _tarjetaCredito(FilaCobranza fila, bool verCostos) {
    final proximo = fila.proximoPago != null
        ? _fmtFecha.format(DateTime.parse(fila.proximoPago!))
        : '—';
    final enMora = fila.estadoCuenta == 'En mora' || fila.estadoCuenta == 'Vencido';
    final etiquetaCuenta = enMora ? 'Vencido' : fila.estadoCuenta;
    final telefono = fila.clienteTelefono;

    return GlassContainer(
      margin: const EdgeInsets.only(bottom: 14),
      accentColor: enMora ? Colors.redAccent : AppColors.neonCyan,
      padding: const EdgeInsets.all(0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    CircleAvatar(
                      backgroundColor: AppColors.neonCyan.withValues(alpha: 0.15),
                      child: Text(
                        fila.clienteNombre.isNotEmpty ? fila.clienteNombre[0].toUpperCase() : '?',
                        style: const TextStyle(fontWeight: FontWeight.w800, color: AppColors.neonCyan),
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            fila.clienteNombre,
                            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
                          ),
                          if (telefono != null && telefono.isNotEmpty)
                            Text(telefono, style: Theme.of(context).textTheme.bodySmall),
                        ],
                      ),
                    ),
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text(
                          _fmt.format(fila.saldoPendienteUsd),
                          style: TextStyle(
                            fontWeight: FontWeight.w800,
                            color: enMora ? Colors.redAccent : AppColors.amber,
                            fontSize: 15,
                          ),
                        ),
                        Text(
                          etiquetaCuenta,
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: enMora ? Colors.redAccent : AppColors.emerald,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                const Text(
                  'Navegación al cliente',
                  style: TextStyle(fontWeight: FontWeight.w800, fontSize: 13),
                ),
                const SizedBox(height: 8),
                AsistenteRutaWidget(
                  latResidencia: fila.latitudResidencia,
                  lngResidencia: fila.longitudResidencia,
                  latTrabajo: fila.latitudTrabajo,
                  lngTrabajo: fila.longitudTrabajo,
                ),
                const SizedBox(height: 10),
                BotonesRutaCliente(
                  latResidencia: fila.latitudResidencia,
                  lngResidencia: fila.longitudResidencia,
                  latTrabajo: fila.latitudTrabajo,
                  lngTrabajo: fila.longitudTrabajo,
                  direccionResidencia: fila.clienteDireccion,
                  direccionTrabajo: fila.clienteDireccionLaboral,
                  clienteId: fila.clienteId,
                  destacados: true,
                ),
              ],
            ),
          ),
          Theme(
            data: Theme.of(context).copyWith(dividerColor: Colors.transparent),
            child: ExpansionTile(
              tilePadding: const EdgeInsets.fromLTRB(16, 8, 8, 4),
              childrenPadding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
              leading: const Icon(Icons.receipt_long_rounded, color: AppColors.neonCyan),
              title: const Text(
                'Detalle de crédito',
                style: TextStyle(fontWeight: FontWeight.w700, fontSize: 14),
              ),
              subtitle: Text(
                fila.productosResumen,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: Theme.of(context).textTheme.bodySmall,
              ),
              trailing: telefono != null && telefono.isNotEmpty
                  ? Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        IconButton(
                          icon: const Icon(Icons.call_rounded, color: AppColors.emerald, size: 20),
                          onPressed: () => _llamar(telefono),
                          tooltip: 'Llamar',
                        ),
                        IconButton(
                          icon: const Icon(Icons.chat_rounded, color: AppColors.emerald, size: 20),
                          onPressed: () => _whatsapp(telefono),
                          tooltip: 'WhatsApp',
                        ),
                      ],
                    )
                  : null,
              children: [
                Row(
                  children: [
                    _resumenChip('Deuda total', _fmt.format(fila.totalUsd), AppColors.textPrimary),
                    const SizedBox(width: 8),
                    _resumenChip('Abonado', _fmt.format(fila.cobradoUsd), AppColors.emerald),
                    const SizedBox(width: 8),
                    _resumenChip('Pendiente', _fmt.format(fila.saldoPendienteUsd), AppColors.amber),
                  ],
                ),
                if (verCostos && fila.costoTotalUsd != null) ...[
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      _resumenChip('Costo', _fmt.format(fila.costoTotalUsd!), AppColors.textMuted),
                      const SizedBox(width: 8),
                      _resumenChip(
                        'Margen',
                        _fmt.format(fila.margenUsd ?? (fila.totalUsd - fila.costoTotalUsd!)),
                        AppColors.violet,
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 12),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: (enMora ? Colors.red : AppColors.neonCyan).withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(
                      color: (enMora ? Colors.red : AppColors.neonCyan).withValues(alpha: 0.35),
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        Icons.event_rounded,
                        color: enMora ? Colors.red : AppColors.neonCyan,
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Próximo cobro',
                              style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                            ),
                            Text(
                              proximo,
                              style: TextStyle(
                                fontWeight: FontWeight.w800,
                                fontSize: 18,
                                color: enMora ? Colors.red : AppColors.neonCyan,
                              ),
                            ),
                            if (fila.montoProximaCuotaUsd > 0)
                              Text(
                                'Cuota: ${_fmt.format(fila.montoProximaCuotaUsd)} · '
                                '${fila.tipoCredito} · ${fila.cuotasPagadas}/${fila.cuotasTotales}',
                                style: Theme.of(context).textTheme.bodySmall,
                              ),
                          ],
                        ),
                      ),
                      FilledButton.icon(
                        onPressed: () => _abonoRapido(fila),
                        icon: const Icon(Icons.price_check_rounded, size: 18),
                        label: const Text('Abonar'),
                        style: FilledButton.styleFrom(
                          backgroundColor: AppColors.neonCyan,
                          foregroundColor: AppColors.bgDeep,
                        ),
                      ),
                    ],
                  ),
                ),
                if (fila.cuotas.isNotEmpty) ...[
                  const SizedBox(height: 16),
                  const Text(
                    'Tabla de amortización',
                    style: TextStyle(fontWeight: FontWeight.w800, fontSize: 14),
                  ),
                  const SizedBox(height: 8),
                  ...fila.cuotas.map((c) {
                    final fecha = _fmtFecha.format(DateTime.parse(c.fechaVencimiento));
                    final color = _colorEstadoCuota(c.estadoDisplay);
                    final montoCobrar = c.montoPendienteUsd > 0 ? c.montoPendienteUsd : c.montoUsd;
                    return Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                      decoration: BoxDecoration(
                        color: AppColors.bgElevated.withValues(alpha: 0.5),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(color: color.withValues(alpha: 0.25)),
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            flex: 2,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  c.etiquetaPeriodo,
                                  style: const TextStyle(fontWeight: FontWeight.w700),
                                ),
                                Text(fecha, style: Theme.of(context).textTheme.bodySmall),
                              ],
                            ),
                          ),
                          Expanded(
                            child: Text(
                              _fmt.format(montoCobrar),
                              style: const TextStyle(fontWeight: FontWeight.w700),
                              textAlign: TextAlign.center,
                            ),
                          ),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                            decoration: BoxDecoration(
                              color: color.withValues(alpha: 0.15),
                              borderRadius: BorderRadius.circular(20),
                            ),
                            child: Text(
                              c.estadoDisplay,
                              style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: color),
                            ),
                          ),
                          if (c.estadoDisplay != 'Pagado') ...[
                            const SizedBox(width: 6),
                            IconButton(
                              icon: const Icon(Icons.payments_outlined, color: AppColors.emerald, size: 22),
                              tooltip: 'Registrar abono',
                              onPressed: () => _abonoRapido(
                                fila,
                                montoSugeridoUsd: c.montoPendienteUsd > 0 ? c.montoPendienteUsd : c.montoUsd,
                              ),
                            ),
                          ],
                        ],
                      ),
                    );
                  }),
                ],
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 0, 12, 12),
            child: EnviarReciboButton(
              email: fila.clienteEmail,
              onEnviar: () => context.read<AppState>().ventas.enviarRecibo(fila.id),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    final verCostos = state.esDueno || state.esAdministrador;

    return FuturisticScaffold(
      title: 'Cobranza y Créditos',
      accentColor: AppColors.neonCyan,
      actions: [IconButton(icon: const Icon(Icons.refresh_rounded), onPressed: _cargar)],
      body: _cargando
          ? const Center(child: CircularProgressIndicator())
          : _error != null
              ? Center(child: Text(_error!, style: const TextStyle(color: Colors.red)))
              : _filas.isEmpty
                  ? ListView(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                      children: [
                        _carpetaMoraCritica(),
                        const SizedBox(height: 80),
                        const EmptyState(
                          icon: Icons.credit_score_outlined,
                          message: 'No hay cuentas pendientes de cobro',
                        ),
                      ],
                    )
                  : RefreshIndicator(
                      onRefresh: _cargar,
                      child: ListView(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                        children: [
                          _carpetaMoraCritica(),
                          Text(
                            '${_filas.length} crédito(s) activo(s)',
                            style: Theme.of(context).textTheme.bodySmall,
                          ),
                          const SizedBox(height: 8),
                          ..._filas.map((f) => _tarjetaCredito(f, verCostos)),
                        ],
                      ),
                    ),
    );
  }
}
