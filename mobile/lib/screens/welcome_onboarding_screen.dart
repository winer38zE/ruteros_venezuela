import 'package:flutter/material.dart';

import '../services/onboarding_prefs.dart';
import '../theme/app_theme.dart';
import '../widgets/futuristic_background.dart';
import '../widgets/glass_container.dart';
import 'login_screen.dart';

class _WelcomePage {
  const _WelcomePage({
    required this.icon,
    required this.title,
    required this.body,
    required this.color,
  });

  final IconData icon;
  final String title;
  final String body;
  final Color color;
}

class WelcomeOnboardingScreen extends StatefulWidget {
  const WelcomeOnboardingScreen({super.key});

  @override
  State<WelcomeOnboardingScreen> createState() => _WelcomeOnboardingScreenState();
}

class _WelcomeOnboardingScreenState extends State<WelcomeOnboardingScreen> {
  final _controller = PageController();
  int _page = 0;

  static const _pages = [
    _WelcomePage(
      icon: Icons.credit_score_rounded,
      title: 'Ventas a crédito',
      body: 'Registra fiados o ventas a plazo y lleva el saldo de cada cliente.',
      color: AppColors.emerald,
    ),
    _WelcomePage(
      icon: Icons.route_rounded,
      title: 'Cobros por ruta',
      body: 'Organiza tu recorrido y registra abonos donde estés, en segundos.',
      color: AppColors.neonCyan,
    ),
    _WelcomePage(
      icon: Icons.cloud_off_rounded,
      title: 'Funciona sin internet',
      body: 'Captura clientes y operaciones offline; se sincronizan al volver la red.',
      color: AppColors.amber,
    ),
    _WelcomePage(
      icon: Icons.currency_exchange_rounded,
      title: 'Caja por moneda',
      body: 'Opera en la moneda de tu país con tasas y totales claros.',
      color: AppColors.violet,
    ),
  ];

  Future<void> _finalizar() async {
    await OnboardingPrefs.marcarWelcomeCompletado();
    if (!mounted) return;
    Navigator.of(context).pushReplacement(
      MaterialPageRoute(builder: (_) => const LoginScreen()),
    );
  }

  void _siguiente() {
    if (_page >= _pages.length - 1) {
      _finalizar();
      return;
    }
    _controller.nextPage(
      duration: const Duration(milliseconds: 320),
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: FuturisticBackground(
        child: SafeArea(
          child: Column(
            children: [
              Align(
                alignment: Alignment.centerRight,
                child: TextButton(
                  onPressed: _finalizar,
                  child: const Text('Saltar'),
                ),
              ),
              Expanded(
                child: PageView.builder(
                  controller: _controller,
                  itemCount: _pages.length,
                  onPageChanged: (i) => setState(() => _page = i),
                  itemBuilder: (context, index) {
                    final p = _pages[index];
                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 28),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Container(
                            padding: const EdgeInsets.all(28),
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: p.color.withValues(alpha: 0.12),
                              border: Border.all(color: p.color.withValues(alpha: 0.45)),
                              boxShadow: [
                                BoxShadow(
                                  color: p.color.withValues(alpha: 0.25),
                                  blurRadius: 36,
                                  spreadRadius: -4,
                                ),
                              ],
                            ),
                            child: Icon(p.icon, size: 72, color: p.color),
                          ),
                          const SizedBox(height: 36),
                          Text(
                            p.title,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                                  fontWeight: FontWeight.w800,
                                ),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            p.body,
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
                                  color: AppColors.textMuted,
                                  height: 1.35,
                                ),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
              Padding(
                padding: const EdgeInsets.fromLTRB(24, 8, 24, 24),
                child: GlassContainer(
                  accentColor: _pages[_page].color,
                  padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: List.generate(
                          _pages.length,
                          (i) => AnimatedContainer(
                            duration: const Duration(milliseconds: 240),
                            margin: const EdgeInsets.symmetric(horizontal: 4),
                            width: i == _page ? 22 : 8,
                            height: 8,
                            decoration: BoxDecoration(
                              borderRadius: BorderRadius.circular(8),
                              color: i == _page
                                  ? _pages[_page].color
                                  : AppColors.textMuted.withValues(alpha: 0.35),
                            ),
                          ),
                        ),
                      ),
                      const SizedBox(height: 16),
                      SizedBox(
                        width: double.infinity,
                        child: FilledButton(
                          onPressed: _siguiente,
                          style: FilledButton.styleFrom(
                            backgroundColor: _pages[_page].color,
                            foregroundColor: AppColors.bgDeep,
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                          child: Text(
                            _page == _pages.length - 1 ? 'Comenzar' : 'Siguiente',
                            style: const TextStyle(fontWeight: FontWeight.w800),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
