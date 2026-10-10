import 'package:flutter/foundation.dart';
import 'package:isar/isar.dart';
import 'package:path_provider/path_provider.dart';

import 'cliente_local.dart';

/// Base local. Queda en null si el dispositivo no puede abrir Isar.
Isar? isarInstance;

Future<void> abrirBaseLocal() async {
  if (isarInstance != null && isarInstance!.isOpen) return;
  try {
    final dir = await getApplicationDocumentsDirectory();
    isarInstance = await Isar.open(
      [ClienteLocalSchema],
      directory: dir.path,
      name: 'ruteros_local',
    );
  } catch (e, st) {
    debugPrint('Isar no pudo abrirse. La app sigue en línea. $e\n$st');
    isarInstance = null;
  }
}
