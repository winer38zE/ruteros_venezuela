import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

/// Botón reutilizable para enviar comprobante por correo.
class EnviarReciboButton extends StatefulWidget {
  const EnviarReciboButton({
    super.key,
    required this.onEnviar,
    this.email,
    this.compacto = false,
  });

  final Future<String> Function() onEnviar;
  final String? email;
  final bool compacto;

  @override
  State<EnviarReciboButton> createState() => _EnviarReciboButtonState();
}

class _EnviarReciboButtonState extends State<EnviarReciboButton> {
  bool _enviando = false;

  Future<void> _enviar() async {
    setState(() => _enviando = true);
    try {
      final mensaje = await widget.onEnviar();
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
    final tieneEmail = widget.email != null && widget.email!.contains('@');

    if (widget.compacto) {
      return TextButton.icon(
        onPressed: _enviando ? null : _enviar,
        icon: _enviando
            ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2))
            : const Text('📩', style: TextStyle(fontSize: 16)),
        label: Text(tieneEmail ? 'Enviar recibo' : 'Enviar recibo (sin correo)'),
      );
    }

    return OutlinedButton.icon(
      onPressed: _enviando ? null : _enviar,
      icon: _enviando
          ? const SizedBox(width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
          : const Text('📩', style: TextStyle(fontSize: 18)),
      label: Text(
        tieneEmail ? '📩 Enviar Recibo al Correo' : '📩 Enviar Recibo (cliente sin correo)',
        textAlign: TextAlign.center,
      ),
      style: OutlinedButton.styleFrom(
        foregroundColor: AppColors.violet,
        side: BorderSide(color: AppColors.violet.withValues(alpha: 0.5)),
        minimumSize: const Size(double.infinity, 44),
        padding: const EdgeInsets.symmetric(vertical: 12),
      ),
    );
  }
}
