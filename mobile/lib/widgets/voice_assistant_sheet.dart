import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:provider/provider.dart';
import 'package:record/record.dart';

import '../providers/app_state.dart';
import '../services/ai_voice_service.dart';
import '../services/api_service.dart';
import '../theme/app_theme.dart';
import 'glass_container.dart';

/// Modal de asistente de voz: grabar → enviar → mostrar resultado.
class VoiceAssistantSheet extends StatefulWidget {
  const VoiceAssistantSheet({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const VoiceAssistantSheet(),
    );
  }

  @override
  State<VoiceAssistantSheet> createState() => _VoiceAssistantSheetState();
}

class _VoiceAssistantSheetState extends State<VoiceAssistantSheet>
    with SingleTickerProviderStateMixin {
  final AudioRecorder _recorder = AudioRecorder();
  AiVoiceUiPhase _phase = AiVoiceUiPhase.idle;
  String _statusText = 'Mantén pulsado el micrófono y dicta tu orden';
  String? _transcripcion;
  String? _resultado;
  bool _holding = false;
  String? _path;
  late AnimationController _pulse;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 900),
      lowerBound: 0.92,
      upperBound: 1.08,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    _pulse.dispose();
    _recorder.dispose();
    super.dispose();
  }

  Future<bool> _ensureMicPermission() async {
    var status = await Permission.microphone.status;
    if (status.isGranted) return true;
    status = await Permission.microphone.request();
    if (status.isGranted) return true;
    if (status.isPermanentlyDenied && mounted) {
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'Activa el permiso de micrófono en Ajustes del teléfono.';
      });
    }
    return false;
  }

  Future<void> _startRecording() async {
    if (_phase == AiVoiceUiPhase.processing) return;
    if (!await _ensureMicPermission()) {
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'Permiso de micrófono denegado.';
      });
      return;
    }
    final dir = await getTemporaryDirectory();
    _path = p.join(dir.path, 'ruteros_voz_${DateTime.now().millisecondsSinceEpoch}.m4a');
    await _recorder.start(
      const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 128000, sampleRate: 44100),
      path: _path!,
    );
    setState(() {
      _holding = true;
      _phase = AiVoiceUiPhase.listening;
      _statusText = 'Escuchando… suelta para enviar';
      _transcripcion = null;
      _resultado = null;
    });
  }

  Future<void> _stopAndSend() async {
    if (!_holding) return;
    _holding = false;
    final path = await _recorder.stop();
    final filePath = path ?? _path;
    if (filePath == null || !File(filePath).existsSync()) {
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'No se pudo grabar audio. Intenta de nuevo.';
      });
      return;
    }

    setState(() {
      _phase = AiVoiceUiPhase.processing;
      _statusText = 'Procesando con IA…';
    });

    final api = context.read<AppState>().api;
    final service = AiVoiceService(api);
    try {
      final result = await service.enviarAudio(File(filePath));
      if (!mounted) return;
      setState(() {
        _transcripcion = result.transcripcion;
        _phase = result.exito ? AiVoiceUiPhase.success : AiVoiceUiPhase.error;
        _statusText = result.exito ? '¡Orden ejecutada!' : result.mensaje;
        _resultado = result.exito
            ? '${result.mensaje}${result.whatsappEnviado ? '\nWhatsApp enviado.' : ''}'
            : result.mensaje;
      });
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = e.message;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'Error de red: $e';
      });
    } finally {
      try {
        await File(filePath).delete();
      } catch (_) {}
    }
  }

  Color get _accent {
    switch (_phase) {
      case AiVoiceUiPhase.listening:
        return AppColors.neonCyan;
      case AiVoiceUiPhase.processing:
        return AppColors.neonBlue;
      case AiVoiceUiPhase.success:
        return Colors.greenAccent;
      case AiVoiceUiPhase.error:
        return Colors.redAccent;
      case AiVoiceUiPhase.idle:
        return AppColors.violet;
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.paddingOf(context).bottom;
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 0, 16, 16 + bottom),
      child: GlassContainer(
        accentColor: _accent,
        padding: const EdgeInsets.fromLTRB(20, 20, 20, 28),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Row(
              children: [
                Icon(Icons.auto_awesome_rounded, color: _accent),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Asistente Ruteros',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                ),
                IconButton(
                  onPressed: () => Navigator.pop(context),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              _statusText,
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textMuted, height: 1.35),
            ),
            if (_transcripcion != null && _transcripcion!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Align(
                alignment: Alignment.centerLeft,
                child: Text(
                  '“$_transcripcion”',
                  style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 13),
                ),
              ),
            ],
            if (_resultado != null) ...[
              const SizedBox(height: 8),
              Text(_resultado!, textAlign: TextAlign.center),
            ],
            const SizedBox(height: 24),
            if (_phase == AiVoiceUiPhase.processing)
              const Padding(
                padding: EdgeInsets.all(12),
                child: CircularProgressIndicator(strokeWidth: 3),
              )
            else
              GestureDetector(
                onLongPressStart: (_) => unawaited(_startRecording()),
                onLongPressEnd: (_) => unawaited(_stopAndSend()),
                onTap: () {
                  if (_phase == AiVoiceUiPhase.listening) {
                    unawaited(_stopAndSend());
                  } else if (_phase != AiVoiceUiPhase.processing) {
                    unawaited(_startRecording());
                  }
                },
                child: ScaleTransition(
                  scale: _phase == AiVoiceUiPhase.listening
                      ? _pulse
                      : const AlwaysStoppedAnimation(1.0),
                  child: Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: LinearGradient(
                        colors: [_accent, _accent.withValues(alpha: 0.55)],
                      ),
                      boxShadow: [
                        BoxShadow(
                          color: _accent.withValues(alpha: 0.45),
                          blurRadius: 24,
                          spreadRadius: 2,
                        ),
                      ],
                    ),
                    child: Icon(
                      _phase == AiVoiceUiPhase.listening ? Icons.mic_rounded : Icons.mic_none_rounded,
                      size: 40,
                      color: Colors.white,
                    ),
                  ),
                ),
              ),
            const SizedBox(height: 12),
            Text(
              _phase == AiVoiceUiPhase.listening
                  ? 'Suelta el botón para procesar'
                  : 'Mantén pulsado para hablar',
              style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}
