import 'package:flutter/material.dart';

import '../screens/first_use_tutorial_screen.dart';
import '../screens/help_screen.dart';
import '../screens/home_screen.dart';
import '../services/onboarding_prefs.dart';

/// Inicio autenticado: tutorial opcional al primer ingreso.
class HomeEntry extends StatefulWidget {
  const HomeEntry({super.key});

  @override
  State<HomeEntry> createState() => _HomeEntryState();
}

class _HomeEntryState extends State<HomeEntry> {
  bool _tutorialRevisado = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _maybeTutorial());
  }

  Future<void> _maybeTutorial() async {
    if (_tutorialRevisado) return;
    _tutorialRevisado = true;
    final hecho = await OnboardingPrefs.tutorialCompletado();
    if (!mounted || hecho) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        fullscreenDialog: true,
        builder: (_) => const FirstUseTutorialScreen(),
      ),
    );
  }

  void _abrirAyuda() {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => const HelpScreen()),
    );
  }

  @override
  Widget build(BuildContext context) {
    return HomeScreen(onAyuda: _abrirAyuda);
  }
}
