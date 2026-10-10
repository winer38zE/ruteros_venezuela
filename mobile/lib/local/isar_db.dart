import 'dart:io';

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
    isarInstance = await _abrir(dir.path);
  } catch (e, st) {
    debugPrint('Isar no pudo abrirse. La app sigue en línea. $e\n$st');
    if (!_esCambioDeEsquema(e)) {
      isarInstance = null;
      return;
    }
    try {
      final dir = await getApplicationDocumentsDirectory();
      await _borrarArchivosLocales(dir.path);
      isarInstance = await _abrir(dir.path);
    } catch (e2, st2) {
      debugPrint('Isar sigue sin abrirse. La app sigue en línea. $e2\n$st2');
      isarInstance = null;
    }
  }
}

Future<Isar> _abrir(String directory) {
  return Isar.open(
    [ClienteLocalSchema],
    directory: directory,
    name: 'ruteros_local',
  );
}

bool _esCambioDeEsquema(Object error) {
  final texto = error.toString().toLowerCase();
  return texto.contains('schema') || texto.contains('migration');
}

Future<void> _borrarArchivosLocales(String directory) async {
  final dir = Directory(directory);
  if (!await dir.exists()) return;
  await for (final entity in dir.list()) {
    final nombre = entity.path.replaceAll('\\', '/').split('/').last;
    if (nombre.startsWith('ruteros_local')) {
      try {
        await entity.delete();
      } catch (_) {}
    }
  }
}
