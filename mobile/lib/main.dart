import 'package:flutter/material.dart';
import 'app.dart';
import 'local/isar_db.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await abrirBaseLocal();
  runApp(const RuterosApp());
}
