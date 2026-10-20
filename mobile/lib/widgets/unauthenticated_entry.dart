import 'package:flutter/material.dart';

import '../screens/login_screen.dart';
import '../screens/welcome_onboarding_screen.dart';
import '../services/onboarding_prefs.dart';
import 'futuristic_background.dart';

/// Muestra bienvenida la primera vez; luego login (sin alterar lógica de sesión).
class UnauthenticatedEntry extends StatefulWidget {
  const UnauthenticatedEntry({super.key});

  @override
  State<UnauthenticatedEntry> createState() => _UnauthenticatedEntryState();
}

class _UnauthenticatedEntryState extends State<UnauthenticatedEntry> {
  bool? _welcomeHecho;

  @override
  void initState() {
    super.initState();
    _cargar();
  }

  Future<void> _cargar() async {
    final hecho = await OnboardingPrefs.welcomeCompletado();
    if (mounted) setState(() => _welcomeHecho = hecho);
  }

  @override
  Widget build(BuildContext context) {
    if (_welcomeHecho == null) {
      return Scaffold(
        body: FuturisticBackground(
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const CircularProgressIndicator(strokeWidth: 3),
                const SizedBox(height: 16),
                Text('Preparando acceso…', style: Theme.of(context).textTheme.titleMedium),
              ],
            ),
          ),
        ),
      );
    }
    if (_welcomeHecho!) return const LoginScreen();
    return const WelcomeOnboardingScreen();
  }
}
