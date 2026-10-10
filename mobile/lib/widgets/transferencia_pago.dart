import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../providers/app_state.dart';
import '../screens/datos_bancarios_screen.dart';
import '../services/empresa_service.dart';
import '../theme/app_theme.dart';

class SelectorCuentaBancaria extends StatefulWidget {
  const SelectorCuentaBancaria({
    super.key,
    required this.onChanged,
    this.canal = 'transferencia',
  });

  final ValueChanged<CuentaBancaria?> onChanged;
  final String canal;

  @override
  State<SelectorCuentaBancaria> createState() => _SelectorCuentaBancariaState();
}

class _SelectorCuentaBancariaState extends State<SelectorCuentaBancaria> {
  List<CuentaBancaria> _cuentas = [];
  CuentaBancaria? _seleccionada;
  bool _cargando = true;
  String? _error;

  List<CuentaBancaria> get _visibles =>
      _cuentas.where((c) => c.canal == widget.canal).toList();

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
      final cuentas = await context.read<AppState>().empresas.cuentasBancarias();
      if (!mounted) return;
      setState(() => _cuentas = cuentas);
      _publicarSeleccion();
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = '$e');
      widget.onChanged(null);
    } finally {
      if (mounted) setState(() => _cargando = false);
    }
  }

  void _publicarSeleccion() {
    final visibles = _visibles;
    final previa = _seleccionada?.id;
    CuentaBancaria? elegida;
    for (final cuenta in visibles) {
      if (cuenta.id == previa) elegida = cuenta;
    }
    elegida ??= visibles.isEmpty ? null : visibles.first;
    setState(() => _seleccionada = elegida);
    widget.onChanged(elegida);
  }

  Future<void> _copiarDato() async {
    final cuenta = _seleccionada;
    if (cuenta == null) return;
    await copiarAlPortapapeles(context, cuenta.datoCopiable);
  }

  Future<void> _abrirConfiguracion() async {
    await Navigator.push<bool>(
      context,
      MaterialPageRoute(builder: (_) => const DatosBancariosScreen()),
    );
    if (mounted) _cargar();
  }

  void _elegir(String? id) {
    CuentaBancaria? cuenta;
    for (final item in _visibles) {
      if (item.id == id) cuenta = item;
    }
    setState(() => _seleccionada = cuenta);
    widget.onChanged(cuenta);
  }

  @override
  Widget build(BuildContext context) {
    final puedeEditar = context.watch<AppState>().puedeOperaciones;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (_cargando)
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: LinearProgressIndicator(),
          )
        else if (_error != null)
          Text(_error!, style: const TextStyle(color: Color(0xFFEF4444)))
        else if (_visibles.isEmpty)
          Text(
            puedeEditar
                ? (widget.canal == 'pago_movil'
                    ? 'No hay Pago Móvil. Agrega banco, teléfono, titular y cédula.'
                    : 'No hay transferencia bancaria. Agrega banco, tipo, número, titular y cédula o RIF.')
                : 'La empresa aún no configuró este medio de pago.',
            style: const TextStyle(fontWeight: FontWeight.w600),
          )
        else ...[
          DropdownButtonFormField<String>(
            value: _seleccionada?.id,
            decoration: InputDecoration(
              labelText: widget.canal == 'pago_movil' ? 'Pago Móvil de destino' : 'Cuenta de destino',
              prefixIcon: const Icon(Icons.account_balance_rounded),
            ),
            items: _visibles
                .map(
                  (c) => DropdownMenuItem(
                    value: c.id,
                    child: Text(c.etiqueta, overflow: TextOverflow.ellipsis),
                  ),
                )
                .toList(),
            onChanged: _elegir,
          ),
          if (_seleccionada != null) ...[
            const SizedBox(height: 12),
            _TarjetaCuenta(cuenta: _seleccionada!, onCopiar: _copiarDato),
          ],
        ],
        if (puedeEditar)
          Align(
            alignment: Alignment.centerLeft,
            child: TextButton.icon(
              onPressed: _abrirConfiguracion,
              icon: const Icon(Icons.account_balance_rounded),
              label: Text(_visibles.isEmpty ? 'Agregar cuenta' : 'Administrar cuentas'),
            ),
          ),
      ],
    );
  }
}

class _TarjetaCuenta extends StatelessWidget {
  const _TarjetaCuenta({required this.cuenta, required this.onCopiar});

  final CuentaBancaria cuenta;
  final VoidCallback onCopiar;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: AppColors.bgElevated.withValues(alpha: 0.55),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.neonBlue.withValues(alpha: 0.35)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            cuenta.esPagoMovil ? 'Datos para Pago Móvil' : 'Datos para transferencia',
            style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16),
          ),
          const SizedBox(height: 4),
          Text(cuenta.banco, style: const TextStyle(color: AppColors.textMuted)),
          const SizedBox(height: 10),
          if (cuenta.esPagoMovil) ...[
            _dato(context, 'Teléfono', cuenta.datoCopiable),
            _dato(context, 'Titular', cuenta.titular),
            _dato(context, 'Cédula', cuenta.documento),
          ] else ...[
            _dato(context, 'Número', cuenta.numeroCuenta),
            _dato(context, 'Tipo', cuenta.tipoCuenta),
            _dato(context, 'Titular', cuenta.titular),
            _dato(context, 'Cédula/RIF', cuenta.documento),
          ],
          const SizedBox(height: 8),
          FilledButton.icon(
            onPressed: cuenta.datoCopiable.trim().isEmpty ? null : onCopiar,
            icon: const Icon(Icons.copy_rounded),
            label: Text(cuenta.esPagoMovil ? 'Copiar teléfono' : 'Copiar número de cuenta'),
          ),
        ],
      ),
    );
  }

  Widget _dato(BuildContext context, String etiqueta, String valor) {
    final texto = valor.trim().isEmpty ? '—' : valor.trim();
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Row(
        children: [
          SizedBox(
            width: 92,
            child: Text(etiqueta, style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ),
          Expanded(
            child: Text(texto, style: const TextStyle(fontWeight: FontWeight.w700)),
          ),
          IconButton(
            tooltip: 'Copiar $etiqueta',
            onPressed: texto == '—' ? null : () => copiarAlPortapapeles(context, texto),
            icon: const Icon(Icons.copy, size: 18),
          ),
        ],
      ),
    );
  }
}

Future<void> copiarAlPortapapeles(BuildContext context, String texto) async {
  final valor = texto.trim();
  if (valor.isEmpty) return;
  await Clipboard.setData(ClipboardData(text: valor));
  if (!context.mounted) return;
  ScaffoldMessenger.of(context).showSnackBar(
    const SnackBar(content: Text('Datos copiados al portapapeles')),
  );
}

class FaseTransferencia extends StatelessWidget {
  const FaseTransferencia({
    super.key,
    required this.esCredito,
    required this.referenciaCtrl,
    required this.onComprobante,
    required this.onCuentaChanged,
    this.detalleCredito,
    this.canal = 'transferencia',
  });

  final bool esCredito;
  final String canal;
  final String? detalleCredito;
  final TextEditingController referenciaCtrl;
  final void Function(String? base64, String? nombre) onComprobante;
  final ValueChanged<CuentaBancaria?> onCuentaChanged;

  @override
  Widget build(BuildContext context) {
    final metodo = esCredito ? 'Venta a crédito' : 'Venta de contado';
    final detalle = esCredito
        ? 'La venta queda a crédito${detalleCredito == null || detalleCredito!.isEmpty ? '' : ' ($detalleCredito)'}. '
            'El cliente usa estos datos para pagar las cuotas. El cobro se confirma al registrar el abono.'
        : 'La venta de contado se cobra ahora. Vendedor o cobrador: Pagada (Por Verificar). Dueño o administrador: Pagada.';
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.neonBlue.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.neonBlue.withValues(alpha: 0.45)),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                canal == 'pago_movil' ? 'Fase 2 · Pago Móvil' : 'Fase 2 · Transferencia bancaria',
                style: const TextStyle(fontSize: 12, color: AppColors.textMuted, fontWeight: FontWeight.w700),
              ),
              const SizedBox(height: 4),
              Text(metodo, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
              const SizedBox(height: 4),
              Text(detalle, style: const TextStyle(fontSize: 13)),
            ],
          ),
        ),
        const SizedBox(height: 12),
        SelectorCuentaBancaria(
          key: ValueKey(canal),
          canal: canal,
          onChanged: onCuentaChanged,
        ),
        const SizedBox(height: 12),
        CamposComprobanteTransferencia(
          referenciaCtrl: referenciaCtrl,
          onComprobante: onComprobante,
        ),
      ],
    );
  }
}

class CamposComprobanteTransferencia extends StatefulWidget {
  const CamposComprobanteTransferencia({
    super.key,
    required this.referenciaCtrl,
    required this.onComprobante,
  });

  final TextEditingController referenciaCtrl;
  final void Function(String? base64, String? nombre) onComprobante;

  @override
  State<CamposComprobanteTransferencia> createState() => _CamposComprobanteTransferenciaState();
}

class _CamposComprobanteTransferenciaState extends State<CamposComprobanteTransferencia> {
  final ImagePicker _picker = ImagePicker();
  Uint8List? _bytes;
  String? _nombre;

  Future<void> _adjuntarComprobante() async {
    final imagen = await _picker.pickImage(
      source: ImageSource.gallery,
      maxWidth: 1600,
      imageQuality: 75,
    );
    if (imagen == null) return;
    final bytes = await imagen.readAsBytes();
    if (!mounted) return;
    setState(() {
      _bytes = bytes;
      _nombre = imagen.name;
    });
    widget.onComprobante(base64Encode(bytes), imagen.name);
  }

  void _quitar() {
    setState(() {
      _bytes = null;
      _nombre = null;
    });
    widget.onComprobante(null, null);
  }

  @override
  Widget build(BuildContext context) {
    final adjunto = _bytes != null;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: widget.referenciaCtrl,
          decoration: const InputDecoration(
            labelText: 'Referencia / número de comprobante',
            prefixIcon: Icon(Icons.tag_rounded),
          ),
        ),
        const SizedBox(height: 12),
        FilledButton.icon(
          onPressed: _adjuntarComprobante,
          icon: Icon(adjunto ? Icons.check_circle : Icons.camera_alt),
          label: Text(adjunto ? 'Comprobante adjuntado' : 'Adjuntar comprobante'),
          style: FilledButton.styleFrom(
            backgroundColor: AppColors.amber,
            foregroundColor: AppColors.bgDeep,
          ),
        ),
        if (adjunto) ...[
          const SizedBox(height: 8),
          const Text(
            'Imagen lista para enviar',
            style: TextStyle(color: AppColors.emerald, fontWeight: FontWeight.w700),
          ),
          if (_nombre != null) Text(_nombre!, style: const TextStyle(color: AppColors.textMuted, fontSize: 12)),
          const SizedBox(height: 8),
          ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.memory(_bytes!, height: 140, width: double.infinity, fit: BoxFit.cover),
          ),
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              onPressed: _quitar,
              icon: const Icon(Icons.close_rounded),
              label: const Text('Quitar foto'),
            ),
          ),
        ],
      ],
    );
  }
}

/// Diálogo posterior al registro: envía la foto ya guardada al administrador.
Future<void> mostrarEnvioComprobanteWhatsapp({
  required BuildContext context,
  required String resumen,
  required bool tieneFoto,
  required Future<String> Function() onEnviar,
}) async {
  var enviando = false;
  var enviado = false;
  await showDialog<void>(
    context: context,
    barrierDismissible: false,
    builder: (ctx) {
      return StatefulBuilder(
        builder: (ctx, setLocal) {
          return AlertDialog(
            backgroundColor: AppColors.bgCard,
            title: const Text('Pago registrado'),
            content: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(resumen),
                const SizedBox(height: 12),
                Text(
                  tieneFoto
                      ? 'La foto quedó guardada. Puedes enviarla al administrador.'
                      : 'No hay foto del comprobante, así que no se puede enviar por WhatsApp.',
                  style: const TextStyle(color: AppColors.textMuted, fontSize: 13),
                ),
                const SizedBox(height: 16),
                SizedBox(
                  width: double.maxFinite,
                  child: FilledButton.icon(
                    onPressed: !tieneFoto || enviando || enviado
                        ? null
                        : () async {
                            setLocal(() => enviando = true);
                            try {
                              final mensaje = await onEnviar();
                              enviado = true;
                              if (ctx.mounted) {
                                ScaffoldMessenger.of(ctx).showSnackBar(
                                  SnackBar(content: Text(mensaje), backgroundColor: AppColors.emerald),
                                );
                              }
                            } catch (e) {
                              if (ctx.mounted) {
                                ScaffoldMessenger.of(ctx).showSnackBar(
                                  SnackBar(
                                    content: Text('$e'),
                                    backgroundColor: const Color(0xFFEF4444),
                                  ),
                                );
                              }
                            } finally {
                              if (ctx.mounted) setLocal(() => enviando = false);
                            }
                          },
                    icon: enviando
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                          )
                        : const Icon(Icons.chat_rounded),
                    label: Text(
                      enviado
                          ? 'Comprobante enviado'
                          : 'Enviar comprobante por WhatsApp al administrador',
                      textAlign: TextAlign.center,
                    ),
                    style: FilledButton.styleFrom(
                      backgroundColor: const Color(0xFF25D366),
                      foregroundColor: Colors.white,
                      disabledBackgroundColor: AppColors.bgElevated,
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                    ),
                  ),
                ),
              ],
            ),
            actions: [
              TextButton(
                onPressed: enviando ? null : () => Navigator.pop(ctx),
                child: Text(enviado ? 'Listo' : 'Cerrar'),
              ),
            ],
          );
        },
      );
    },
  );
}
