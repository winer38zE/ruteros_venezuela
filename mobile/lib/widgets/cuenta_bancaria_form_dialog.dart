import 'package:flutter/material.dart';
import '../models/configuracion_bancaria_pais.dart';
import '../theme/app_theme.dart';

/// Formulario reutilizable: banco y documento según país.
class CuentaBancariaFormDialog extends StatefulWidget {
  const CuentaBancariaFormDialog({
    super.key,
    required this.config,
    required this.titulo,
    required this.onGuardar,
  });

  final ConfiguracionBancariaPais config;
  final String titulo;
  final Future<void> Function(CuentaBancariaFormData data) onGuardar;

  @override
  State<CuentaBancariaFormDialog> createState() => _CuentaBancariaFormDialogState();
}

class CuentaBancariaFormData {
  final String banco;
  final String tipoCuenta;
  final String titular;
  final String documentoIdentidad;
  final String canal;
  final String? numeroCuenta;
  final String? telefonoPagoMovil;

  CuentaBancariaFormData({
    required this.banco,
    required this.tipoCuenta,
    required this.titular,
    required this.documentoIdentidad,
    required this.canal,
    this.numeroCuenta,
    this.telefonoPagoMovil,
  });
}

class _CuentaBancariaFormDialogState extends State<CuentaBancariaFormDialog> {
  final _numeroCtrl = TextEditingController();
  final _telefonoCtrl = TextEditingController();
  final _titularCtrl = TextEditingController();
  final _documentoCtrl = TextEditingController();

  late String _canal;
  late String _banco;
  late String _tipoCuenta;
  late String _tipoDocumento;
  bool _guardando = false;

  @override
  void initState() {
    super.initState();
    final cfg = widget.config;
    _banco = cfg.bancos.first;
    _tipoDocumento = cfg.documentosLegales.first;
    _tipoCuenta = cfg.tiposCuenta.first.label;
    _canal = cfg.canalesPago.isNotEmpty ? cfg.canalesPago.first.id : 'transferencia';
    if (cfg.esCanalPagoMovil(_banco, _canal)) {
      _canal = 'pago_movil';
    }
  }

  @override
  void dispose() {
    _numeroCtrl.dispose();
    _telefonoCtrl.dispose();
    _titularCtrl.dispose();
    _documentoCtrl.dispose();
    super.dispose();
  }

  bool get _pagoMovil =>
      widget.config.esCanalPagoMovil(_banco, _canal) || _canal == 'pago_movil';

  String get _documentoFinal {
    final num = _documentoCtrl.text.trim();
    if (_tipoDocumento.isEmpty) return num;
    if (num.isEmpty) return _tipoDocumento;
    if (num.startsWith('$_tipoDocumento-') || num.startsWith('$_tipoDocumento ')) {
      return num;
    }
    return '$_tipoDocumento-$num';
  }

  Future<void> _guardar() async {
    if (_banco.isEmpty ||
        _titularCtrl.text.trim().isEmpty ||
        _documentoCtrl.text.trim().isEmpty ||
        (_pagoMovil ? _telefonoCtrl.text.trim().isEmpty : _numeroCtrl.text.trim().isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(
            _pagoMovil
                ? 'Completa banco, teléfono, titular y documento'
                : 'Completa banco, número de cuenta, titular y documento',
          ),
        ),
      );
      return;
    }
    setState(() => _guardando = true);
    try {
      await widget.onGuardar(
        CuentaBancariaFormData(
          banco: _banco,
          tipoCuenta: _tipoCuenta,
          titular: _titularCtrl.text.trim(),
          documentoIdentidad: _documentoFinal,
          canal: _pagoMovil ? 'pago_movil' : 'transferencia',
          numeroCuenta: _pagoMovil ? null : _numeroCtrl.text.trim(),
          telefonoPagoMovil: _pagoMovil ? _telefonoCtrl.text.trim() : null,
        ),
      );
      if (mounted) Navigator.pop(context, true);
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
    final cfg = widget.config;
    final canales = cfg.canalesPago;
    return AlertDialog(
      backgroundColor: AppColors.bgCard,
      title: Text(widget.titulo),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (canales.length > 1)
              DropdownButtonFormField<String>(
                value: _canal,
                decoration: const InputDecoration(labelText: 'Medio de pago'),
                items: canales
                    .map(
                      (c) => DropdownMenuItem(value: c.id, child: Text(c.label)),
                    )
                    .toList(),
                onChanged: (v) => setState(() => _canal = v ?? _canal),
              ),
            if (canales.length > 1) const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _banco,
              decoration: const InputDecoration(labelText: 'Banco'),
              items: cfg.bancos
                  .map((b) => DropdownMenuItem(value: b, child: Text(b)))
                  .toList(),
              onChanged: (v) {
                setState(() {
                  _banco = v ?? _banco;
                  if (cfg.esCanalPagoMovil(_banco, _canal)) {
                    _canal = 'pago_movil';
                  }
                });
              },
            ),
            const SizedBox(height: 8),
            if (!_pagoMovil)
              DropdownButtonFormField<String>(
                value: _tipoCuenta,
                decoration: const InputDecoration(labelText: 'Tipo de cuenta'),
                items: cfg.tiposCuenta
                    .map((t) => DropdownMenuItem(value: t.label, child: Text(t.label)))
                    .toList(),
                onChanged: (v) => setState(() => _tipoCuenta = v ?? _tipoCuenta),
              ),
            if (!_pagoMovil) const SizedBox(height: 8),
            DropdownButtonFormField<String>(
              value: _tipoDocumento,
              decoration: const InputDecoration(labelText: 'Tipo de documento'),
              items: cfg.documentosLegales
                  .map((d) => DropdownMenuItem(value: d, child: Text(d)))
                  .toList(),
              onChanged: (v) => setState(() => _tipoDocumento = v ?? _tipoDocumento),
            ),
            const SizedBox(height: 8),
            if (_pagoMovil)
              TextField(
                controller: _telefonoCtrl,
                keyboardType: TextInputType.phone,
                decoration: const InputDecoration(labelText: 'Teléfono / alias'),
              )
            else
              TextField(
                controller: _numeroCtrl,
                decoration: const InputDecoration(labelText: 'Número de cuenta'),
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
                labelText: 'Número de documento',
                hintText: _tipoDocumento,
              ),
            ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _guardando ? null : () => Navigator.pop(context, false),
          child: const Text('Cancelar'),
        ),
        FilledButton(
          onPressed: _guardando ? null : _guardar,
          child: Text(_guardando ? 'Guardando...' : 'Guardar'),
        ),
      ],
    );
  }
}
