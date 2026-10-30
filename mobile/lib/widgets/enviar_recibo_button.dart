import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Botón reutilizable para enviar comprobante por correo.
class EnviarReciboButton extends StatefulWidget {
  const EnviarReciboButton({
    super.key,
    required this.onEnviar,
    this.email,
    this.telefono,
    this.onWhatsapp,
    this.compacto = false,
  });

  final Future<String> Function() onEnviar;
  final String? email;
  final String? telefono;
  final Future<String> Function()? onWhatsapp;
  final bool compacto;

  @override
  State<EnviarReciboButton> createState() => _EnviarReciboButtonState();
}

class _EnviarReciboButtonState extends State<EnviarReciboButton> {
  bool _enviando = false;

  bool get _tieneCorreo => widget.email != null && widget.email!.contains('@');

  bool get _usarWhatsapp => !_tieneCorreo && widget.onWhatsapp != null;

  Future<void> _enviar() async {
    setState(() => _enviando = true);
    try {
      final mensaje = _usarWhatsapp ? await widget.onWhatsapp!() : await widget.onEnviar();
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(mensaje), backgroundColor: AppColors.emerald),
      );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(e.toString()), backgroundColor: Colors.red),
      );
    } finally {
      if (mounted) setState(() => _enviando = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final icono = _enviando
        ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
        : Icon(_usarWhatsapp ? Icons.chat_rounded : Icons.receipt_long_rounded, size: 18);
    final texto = _usarWhatsapp
        ? 'Enviar recibo por WhatsApp'
        : (_tieneCorreo ? 'Enviar recibo al correo' : 'Enviar recibo');

    if (widget.compacto) {
      return TextButton.icon(
        onPressed: _enviando ? null : _enviar,
        icon: icono,
        label: Text(texto),
      );
    }

    return OutlinedButton.icon(
      onPressed: _enviando ? null : _enviar,
      icon: icono,
      label: Text(texto, textAlign: TextAlign.center),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.violet,
        side: BorderSide(color: AppColors.violet.withValues(alpha: 0.5)),
        minimumSize: const Size(double.infinity, 44),
        padding: const EdgeInsets.symmetric(vertical: 12),
      ),
    );
  }
}
