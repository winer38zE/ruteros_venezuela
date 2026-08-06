import 'package:flutter/material.dart';
import '../theme/app_theme.dart';

class FuturisticBackground extends StatelessWidget {
  const FuturisticBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(color: AppColors.bgDeep),
        Positioned(
          top: -80,
          right: -60,
          child: _orb(AppColors.neonCyan.withValues(alpha: 0.18), 220),
        ),
        Positioned(
          bottom: 120,
          left: -90,
          child: _orb(AppColors.neonBlue.withValues(alpha: 0.14), 260),
        ),
        Positioned(
          top: 200,
          left: 40,
          child: _orb(AppColors.emerald.withValues(alpha: 0.08), 140),
        ),
        child,
      ],
    );
  }

  Widget _orb(Color color, double size) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: RadialGradient(colors: [color, Colors.transparent]),
      ),
    );
  }
}
