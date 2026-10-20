import 'package:url_launcher/url_launcher.dart';

import '../config/support_config.dart';

Future<bool> abrirWhatsappSoporte({String? mensaje, String? paisNombre}) async {
  final text = mensaje ?? SupportConfig.mensajeSoporte(pais: paisNombre);
  final uri = Uri.parse(
    'https://wa.me/${SupportConfig.whatsappE164}?text=${Uri.encodeComponent(text)}',
  );
  if (await canLaunchUrl(uri)) {
    return launchUrl(uri, mode: LaunchMode.externalApplication);
  }
  return false;
}
