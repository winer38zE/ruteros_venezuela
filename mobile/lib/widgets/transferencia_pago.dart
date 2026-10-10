import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
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
    final valor = cuenta.datoCopiable.trim();
    if (valor.isEmpty) return;
    await Clipboard.setData(ClipboardData(text: valor));
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          cuenta.esPagoMovil ? 'Teléfono de Pago Móvil copiado' : 'Número de cuenta copiado',
        ),
      ),
    );
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
          Text(cuenta.banco, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
          const SizedBox(height: 10),
          if (cuenta.esPagoMovil) ...[
            _dato('Teléfono', cuenta.datoCopiable),
            _dato('Titular', cuenta.titular),
            _dato('Cédula', cuenta.documento),
          ] else ...[
            _dato('Número', cuenta.numeroCuenta),
            _dato('Tipo', cuenta.tipoCuenta),
            _dato('Titular', cuenta.titular),
            _dato('Cédula/RIF', cuenta.documento),
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

  Widget _dato(String etiqueta, String valor) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 92,
            child: Text(etiqueta, style: const TextStyle(color: AppColors.textMuted, fontSize: 13)),
          ),
          Expanded(
            child: Text(
              valor.trim().isEmpty ? '—' : valor,
              style: const TextStyle(fontWeight: FontWeight.w700),
            ),
          ),
        ],
      ),
    );
  }
}

class FaseTransferencia extends StatelessWidget {
  const FaseTransferencia({
    super.key,
    required this.esCredito,
    required this.referenciaCtrl,
    required this.comprobanteNombre,
    required this.onElegirFoto,
    required this.onCuentaChanged,
    this.onQuitarFoto,
    this.detalleCredito,
    this.canal = 'transferencia',
  });

  final bool esCredito;
  final String canal;
  final String? detalleCredito;
  final TextEditingController referenciaCtrl;
  final String? comprobanteNombre;
  final VoidCallback onElegirFoto;
  final VoidCallback? onQuitarFoto;
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
          comprobanteNombre: comprobanteNombre,
          onElegirFoto: onElegirFoto,
          onQuitarFoto: onQuitarFoto,
        ),
      ],
    );
  }
}

class CamposComprobanteTransferencia extends StatelessWidget {
  const CamposComprobanteTransferencia({
    super.key,
    required this.referenciaCtrl,
    required this.comprobanteNombre,
    required this.onElegirFoto,
    this.onQuitarFoto,
  });

  final TextEditingController referenciaCtrl;
  final String? comprobanteNombre;
  final VoidCallback onElegirFoto;
  final VoidCallback? onQuitarFoto;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: referenciaCtrl,
          decoration: const InputDecoration(
            labelText: 'Referencia / número de comprobante',
            prefixIcon: Icon(Icons.tag_rounded),
          ),
        ),
        const SizedBox(height: 12),
        OutlinedButton.icon(
          onPressed: onElegirFoto,
          icon: const Icon(Icons.photo_camera_outlined),
          label: Text(
            comprobanteNombre == null ? 'Adjuntar foto del comprobante' : 'Cambiar foto',
          ),
        ),
        if (comprobanteNombre != null) ...[
          const SizedBox(height: 8),
          Row(
            children: [
              const Icon(Icons.image_outlined, size: 18, color: AppColors.emerald),
              const SizedBox(width: 8),
              Expanded(child: Text(comprobanteNombre!)),
              if (onQuitarFoto != null)
                IconButton(
                  tooltip: 'Quitar foto',
                  onPressed: onQuitarFoto,
                  icon: const Icon(Icons.close_rounded),
                ),
            ],
          ),
        ],
      ],
    );
  }
}
