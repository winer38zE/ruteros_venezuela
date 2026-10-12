import 'package:flutter/material.dart';
import 'app.dart';
import 'local/isar_db.dart';
import 'services/notification_service.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await abrirBaseLocal();
  await NotificationService.instance.iniciar();
  runApp(const RuterosApp());
}
