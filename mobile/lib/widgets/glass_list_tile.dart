import 'package:flutter/material.dart';
import '../theme/app_theme.dart';
import 'glass_container.dart';

class GlassListTile extends StatelessWidget {
  const GlassListTile({
    super.key,
    required this.title,
    this.subtitle,
    this.trailing,
    this.leading,
    this.accentColor,
    this.selected = false,
    this.onTap,
    this.children,
  });

  final Widget title;
  final Widget? subtitle;
  final Widget? trailing;
  final Widget? leading;
  final Color? accentColor;
  final bool selected;
  final VoidCallback? onTap;
  final List<Widget>? children;

  @override
  Widget build(BuildContext context) {
    final accent = accentColor ?? (selected ? AppColors.neonCyan : AppColors.neonBlue);

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassContainer(
        accentColor: accent,
        padding: EdgeInsets.zero,
        onTap: onTap,
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (leading != null) ...[
                    leading!,
                    const SizedBox(width: 12),
                  ],
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        DefaultTextStyle(
                          style: const TextStyle(
                            fontWeight: FontWeight.w700,
                            fontSize: 16,
                            color: AppColors.textPrimary,
                          ),
                          child: title,
                        ),
                        if (subtitle != null) ...[
                          const SizedBox(height: 4),
                          DefaultTextStyle(
                            style: const TextStyle(fontSize: 13, color: AppColors.textMuted),
                            child: subtitle!,
                          ),
                        ],
                      ],
                    ),
                  ),
                  if (trailing != null) trailing!,
                ],
              ),
            ),
            if (children != null && children!.isNotEmpty) ...[
              Divider(height: 1, color: accent.withValues(alpha: 0.2)),
              ...children!,
            ],
          ],
        ),
      ),
    );
  }
}
