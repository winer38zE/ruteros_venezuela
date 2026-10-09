import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/app_state.dart';
import 'theme/app_theme.dart';
import 'widgets/futuristic_background.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';

class RuterosApp extends StatelessWidget {
  const RuterosApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AppState(),
      child: MaterialApp(
        title: 'ED NET PRO — Ruteros',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.dark,
        home: Consumer<AppState>(
          builder: (_, state, __) {
            if (!state.inicializado) {
              return Scaffold(
                body: FuturisticBackground(
                  child: Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            boxShadow: [
                              BoxShadow(
                                color: AppColors.neonCyan.withValues(alpha: 0.3),
                                blurRadius: 40,
                                spreadRadius: 4,
                              ),
                            ],
                          ),
                          child: const CircularProgressIndicator(strokeWidth: 3),
                        ),
                        const SizedBox(height: 24),
                        Text(
                          'Conectando con ED NET PRO',
                          style: Theme.of(context).textTheme.titleLarge,
                        ),
                        const SizedBox(height: 6),
                        const Text('Sincronizando red multimoneda...'),
                      ],
                    ),
                  ),
                ),
              );
            }
            if (state.usuario != null) return const HomeScreen();
            return const LoginScreen();
          },
        ),
      ),
    );
  }
}
