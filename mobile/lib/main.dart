import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'app.dart';
import 'local/isar_db.dart';
import 'services/notification_service.dart';

/// Bypass SSL temporal mientras el servidor no entrega la cadena completa del certificado.
/// Quitar cuando api.edwuarcardenas.online tenga fullchain en Coolify/nginx.
class MyHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return super.createHttpClient(context)
      ..badCertificateCallback =
          (X509Certificate cert, String host, int port) => true;
  }
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  if (!kIsWeb) {
    HttpOverrides.global = MyHttpOverrides();
  }
  await abrirBaseLocal();
  await NotificationService.instance.iniciar();
  runApp(const RuterosApp());
}
