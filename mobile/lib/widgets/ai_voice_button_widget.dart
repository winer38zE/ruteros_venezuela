import 'package:flutter/material.dart';

import '../theme/app_theme.dart';
import 'ai_voice_modal.dart';

/// Espacio sobre barra de navegación inferior del home.
const double kAiVoiceFabOffsetAboveBottomNav = 96;

/// FAB que abre [AiVoiceModal].
class AIVoiceButtonWidget extends StatelessWidget {
  const AIVoiceButtonWidget({super.key, this.liftAboveBottomNav = false});

  final bool liftAboveBottomNav;

  @override
  Widget build(BuildContext context) {
    final fab = FloatingActionButton(
      heroTag: 'ruteros_ai_voice_fab',
      onPressed: () => AiVoiceModal.show(context),
      backgroundColor: AppColors.violet,
      foregroundColor: Colors.white,
      elevation: 8,
      tooltip: 'Asistente de voz',
      child: const Icon(Icons.mic_rounded, size: 28),
    );
    final bottomInset = MediaQuery.viewPaddingOf(context).bottom;
    final lift = liftAboveBottomNav ? kAiVoiceFabOffsetAboveBottomNav : 16.0;
    return Padding(
      padding: EdgeInsets.only(bottom: lift + bottomInset),
      child: fab,
    );
  }
}
