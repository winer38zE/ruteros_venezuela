import 'package:flutter/material.dart';
import '../services/clientes_service.dart';
import '../theme/app_theme.dart';

class ScoreBadge extends StatelessWidget {
  const ScoreBadge({super.key, required this.score, required this.estado, this.compact = false});

  final int score;
  final String estado;
  final bool compact;

  static Color colorFor(String nivel, int score) {
    if (score <= 35 || nivel == 'malo') return const Color(0xFFEF4444);
    if (nivel == 'regular' || (score >= 35 && score < 60)) return AppColors.amber;
    if (nivel == 'excelente' || score >= 85) return AppColors.emerald;
    return AppColors.neonCyan;
  }

  @override
  Widget build(BuildContext context) {
    final color = colorFor('', score);
    return Container(
      padding: EdgeInsets.symmetric(horizontal: compact ? 8 : 12, vertical: compact ? 4 : 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(compact ? 12 : 16),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            'Score $score',
            style: TextStyle(fontWeight: FontWeight.w800, color: color, fontSize: compact ? 12 : 16),
          ),
          if (!compact)
            Text(estado, style: TextStyle(fontSize: 11, color: color.withValues(alpha: 0.9))),
        ],
      ),
    );
  }
}

Color scoreColor(ClienteDetalle c) => ScoreBadge.colorFor(c.nivelRiesgo, c.scoreCredito);
