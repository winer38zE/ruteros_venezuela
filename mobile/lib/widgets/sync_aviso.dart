import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../providers/app_state.dart';

/// Clave del mensajero raíz, para avisar aunque la pantalla activa no tenga Scaffold.
final GlobalKey<ScaffoldMessengerState> syncMessengerKey = GlobalKey<ScaffoldMessengerState>();

/// Muestra el aviso cuando la red vuelve y arranca la sincronización.
class SyncAvisoHost extends StatefulWidget {
  const SyncAvisoHost({super.key, required this.child});

  final Widget child;

  @override
  State<SyncAvisoHost> createState() => _SyncAvisoHostState();
}

class _SyncAvisoHostState extends State<SyncAvisoHost> {
  StreamSubscription<String>? _avisos;

  @override
  void initState() {
    super.initState();
    _avisos = context.read<AppState>().sync.avisos.listen(_mostrar);
  }

  void _mostrar(String mensaje) {
    final messenger = syncMessengerKey.currentState;
    if (messenger == null) return;
    messenger.hideCurrentSnackBar();
    messenger.showSnackBar(
      SnackBar(
        content: Text(mensaje),
        duration: const Duration(seconds: 2),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  void dispose() {
    _avisos?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}
