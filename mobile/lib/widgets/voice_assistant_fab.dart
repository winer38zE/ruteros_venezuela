import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import 'voice_assistant_sheet.dart';

/// Espacio sobre [FloatingNavBar] (padding inferior 24 + altura ~72).
const double kVoiceFabOffsetAboveBottomNav = 96;

/// FAB flotante que abre el modal del asistente de voz.
class VoiceAssistantFab extends StatelessWidget {
  const VoiceAssistantFab({super.key, this.liftAboveBottomNav = false});

  /// Si hay barra inferior en el home, evita solapamiento.
  final bool liftAboveBottomNav;

  @override
  Widget build(BuildContext context) {
    final fab = FloatingActionButton.extended(
      onPressed: () => VoiceAssistantSheet.show(context),
      backgroundColor: AppColors.violet,
      foregroundColor: Colors.white,
      elevation: 8,
      icon: const Icon(Icons.record_voice_over_rounded),
      label: const Text('IA Voz', style: TextStyle(fontWeight: FontWeight.w700)),
    );
    if (!liftAboveBottomNav) return fab;
    return Padding(
      padding: const EdgeInsets.only(bottom: kVoiceFabOffsetAboveBottomNav),
      child: fab,
    );
  }
}
