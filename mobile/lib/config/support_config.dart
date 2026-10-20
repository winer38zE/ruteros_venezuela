/// Contacto de soporte (WhatsApp). Override: `--dart-define=SUPPORT_WHATSAPP=58412XXXXXXX`
class SupportConfig {
  SupportConfig._();

  static const String _envWhatsapp = String.fromEnvironment('SUPPORT_WHATSAPP');

  static const String _defaultWhatsapp = '584121234567';

  static String get whatsappE164 {
    final raw = _envWhatsapp.isNotEmpty ? _envWhatsapp : _defaultWhatsapp;
    return raw.replaceAll(RegExp(r'\D'), '');
  }

  static String mensajeSoporte({String? pais}) {
    final p = (pais ?? '').trim();
    if (p.isEmpty) {
      return 'Hola, necesito ayuda con ED NET PRO Ruteros.';
    }
    return 'Hola, necesito ayuda con ED NET PRO Ruteros (país: $p).';
  }
}
