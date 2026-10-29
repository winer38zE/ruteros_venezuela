import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:audioplayers/audioplayers.dart';
import 'package:flutter/foundation.dart';
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

/// Modal inferior del asistente de voz (grabar → IA → resultado).
class AiVoiceModal extends StatefulWidget {
  const AiVoiceModal({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => const AiVoiceModal(),
    );
  }

  @override
  State<AiVoiceModal> createState() => _AiVoiceModalState();
}

class _AiVoiceModalState extends State<AiVoiceModal> with SingleTickerProviderStateMixin {
  static const _listeningRed = Color(0xFFEF4444);

  final AudioRecorder _recorder = AudioRecorder();
  final AudioPlayer _responsePlayer = AudioPlayer();
  AiVoiceUiPhase _phase = AiVoiceUiPhase.idle;
  String _statusText = 'Mantén pulsado el micrófono y dicta tu orden';
  String? _transcripcion;
  String? _resultado;
  String? _ultimoAudioBase64;
  String? _codigoDetalle;
  bool _holding = false;
  bool _bloqueoMicPorTts = false;
  String? _path;
  late AnimationController _pulse;
  StreamSubscription<PlayerState>? _playerSub;

  @override
  void initState() {
    super.initState();
    _pulse = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 850),
      lowerBound: 0.9,
      upperBound: 1.1,
    )..repeat(reverse: true);
    _playerSub = _responsePlayer.onPlayerComplete.listen((_) {
      _liberarMicrofonoTrasVoz();
    });
  }

  Future<void> _reiniciarSesionServidor() async {
    if (!mounted) return;
    final api = context.read<AppState>().api;
    await AiVoiceService(api).reiniciarSesion();
    if (!mounted) return;
    setState(() {
      _transcripcion = null;
      _resultado = null;
      _codigoDetalle = null;
      _ultimoAudioBase64 = null;
      _phase = AiVoiceUiPhase.idle;
      _statusText = 'Conversación nueva. Dicta tu orden.';
    });
  }

  Future<void> _cerrarModal() async {
    await _reiniciarSesionServidor();
    if (mounted) Navigator.pop(context);
  }

  @override
  void dispose() {
    unawaited(_playerSub?.cancel());
    _pulse.dispose();
    _recorder.dispose();
    unawaited(_responsePlayer.dispose());
    super.dispose();
  }

  void _liberarMicrofonoTrasVoz() {
    if (!mounted || !_bloqueoMicPorTts) return;
    setState(() {
      _bloqueoMicPorTts = false;
      if (_phase == AiVoiceUiPhase.idle ||
          _phase == AiVoiceUiPhase.success ||
          _phase == AiVoiceUiPhase.error) {
        _statusText = 'Mantén pulsado el micrófono y dicta tu orden';
      }
    });
  }

  Future<void> _reproducirRespuestaVoz(String? audioBase64) async {
    final payload = audioBase64?.trim();
    if (payload == null || payload.isEmpty) return;
    if (mounted) {
      setState(() {
        _bloqueoMicPorTts = true;
        _statusText = 'Escuchando respuesta… no hables hasta que termine.';
      });
    }
    try {
      final bytes = base64Decode(payload);
      final dir = await getTemporaryDirectory();
      final path = p.join(
        dir.path,
        'ai_voz_resp_${DateTime.now().millisecondsSinceEpoch}.mp3',
      );
      final file = File(path);
      await file.writeAsBytes(bytes, flush: true);
      await _responsePlayer.stop();
      await _responsePlayer.play(DeviceFileSource(path));
    } catch (e) {
      _liberarMicrofonoTrasVoz();
      if (kDebugMode) {
        debugPrint('No se pudo reproducir audio TTS: $e');
      }
    }
  }

  Future<bool> _ensureMicPermission() async {
    if (await _recorder.hasPermission()) return true;
    var status = await Permission.microphone.status;
    if (status.isGranted) return true;
    status = await Permission.microphone.request();
    if (status.isGranted || await _recorder.hasPermission()) return true;
    if (status.isPermanentlyDenied && mounted) {
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'Activa el permiso de micrófono en Ajustes del teléfono.';
      });
    }
    return false;
  }

  Future<void> _startRecording() async {
    if (_phase == AiVoiceUiPhase.processing || _holding || _bloqueoMicPorTts) return;
    if (!await _ensureMicPermission()) {
      if (!mounted) return;
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'Permiso de micrófono denegado.';
      });
      return;
    }
    try {
      await _responsePlayer.stop();
      if (await _recorder.isRecording()) {
        await _recorder.stop();
      }
      final dir = await getTemporaryDirectory();
      _path = p.join(dir.path, 'ruteros_voz_${DateTime.now().millisecondsSinceEpoch}.m4a');
      await _recorder.start(
        const RecordConfig(encoder: AudioEncoder.aacLc, bitRate: 128000, sampleRate: 44100),
        path: _path!,
      );
      if (!mounted) return;
      setState(() {
        _holding = true;
        _phase = AiVoiceUiPhase.listening;
        _statusText = 'Escuchando…';
        _transcripcion = null;
        _resultado = null;
        _ultimoAudioBase64 = null;
      });
    } catch (e) {
      _holding = false;
      if (!mounted) return;
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'No se pudo grabar: $e';
      });
    }
  }

  Future<void> _stopAndSend() async {
    if (!_holding && _phase != AiVoiceUiPhase.listening) return;
    _holding = false;
    final api = mounted ? context.read<AppState>().api : null;
    String? path;
    try {
      path = await _recorder.stop();
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'Error al detener la grabación: $e';
      });
      return;
    }
    final filePath = path ?? _path;
    if (filePath == null || !File(filePath).existsSync()) {
      setState(() {
        _phase = AiVoiceUiPhase.error;
        _statusText = 'No se pudo grabar audio. Intenta de nuevo.';
      });
      return;
    }

    if (api == null) return;

    setState(() {
      _phase = AiVoiceUiPhase.processing;
      _statusText = 'Procesando con IA…';
    });

    final service = AiVoiceService(api);
    try {
      final result = await service.enviarAudio(File(filePath));
      if (!mounted) return;
      _mostrarResultado(result);
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

  void _mostrarResultado(AiVoiceCommandResult result) {
    final wa = result.whatsappEnviado ? ' WhatsApp enviado.' : '';
    final codigo = result.detalle['codigo']?.toString();
    setState(() {
      _transcripcion = result.transcripcion;
      _phase = result.exito ? AiVoiceUiPhase.success : AiVoiceUiPhase.error;
      _statusText = result.exito ? '¡Listo!' : result.mensaje;
      _resultado = result.exito ? '${result.mensaje}$wa' : result.mensaje;
      _ultimoAudioBase64 = result.audioBase64;
      _codigoDetalle = codigo?.isNotEmpty == true ? codigo : null;
    });
    unawaited(_reproducirRespuestaVoz(result.audioBase64));
  }

  Future<void> _resolverConfirmacion(String accion) async {
    if (!mounted || _phase == AiVoiceUiPhase.processing) return;
    final api = context.read<AppState>().api;
    setState(() {
      _phase = AiVoiceUiPhase.processing;
      _statusText = accion == 'confirmar' ? 'Confirmando…' : 'Cancelando…';
    });
    try {
      final result = await AiVoiceService(api).resolverConfirmacion(accion);
      if (!mounted) return;
      _mostrarResultado(result);
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
    }
  }

  Color get _accent {
    switch (_phase) {
      case AiVoiceUiPhase.listening:
        return _listeningRed;
      case AiVoiceUiPhase.processing:
        return AppColors.neonBlue;
      case AiVoiceUiPhase.success:
        return AppColors.emerald;
      case AiVoiceUiPhase.error:
        return _listeningRed;
      case AiVoiceUiPhase.idle:
        return AppColors.violet;
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottom = MediaQuery.paddingOf(context).bottom;
    final listening = _phase == AiVoiceUiPhase.listening;

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
                Icon(Icons.mic_rounded, color: _accent),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Asistente Ruteros',
                    style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                ),
                IconButton(
                  tooltip: 'Cerrar y olvidar conversación',
                  onPressed: () => unawaited(_cerrarModal()),
                  icon: const Icon(Icons.close_rounded),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              _statusText,
              textAlign: TextAlign.center,
              style: TextStyle(
                color: listening ? _listeningRed : AppColors.textMuted,
                height: 1.35,
                fontWeight: listening ? FontWeight.w700 : FontWeight.normal,
              ),
            ),
            if (_transcripcion != null && _transcripcion!.isNotEmpty) ...[
              const SizedBox(height: 12),
              Align(
                alignment: Alignment.centerLeft,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Entendí:',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                        color: AppColors.textMuted,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '“$_transcripcion”',
                      style: const TextStyle(fontStyle: FontStyle.italic, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ],
            if (_resultado != null) ...[
              const SizedBox(height: 10),
              Text(
                _resultado!,
                textAlign: TextAlign.center,
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            ],
            if (_codigoDetalle != null) ...[
              const SizedBox(height: 6),
              Text(
                'Código: $_codigoDetalle',
                style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
              ),
            ],
            const SizedBox(height: 8),
            TextButton.icon(
              onPressed: () => unawaited(_reiniciarSesionServidor()),
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: const Text('Nueva conversación'),
            ),
            if (_ultimoAudioBase64 != null && _ultimoAudioBase64!.isNotEmpty) ...[
              const SizedBox(height: 8),
              TextButton.icon(
                onPressed: () => unawaited(_reproducirRespuestaVoz(_ultimoAudioBase64)),
                icon: const Icon(Icons.volume_up_rounded, size: 20),
                label: const Text('Repetir voz'),
              ),
            ],
            if (_codigoDetalle == 'confirmacion_pendiente') ...[
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: FilledButton(
                      onPressed: _phase == AiVoiceUiPhase.processing
                          ? null
                          : () => unawaited(_resolverConfirmacion('confirmar')),
                      child: const Text('Confirmar'),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _phase == AiVoiceUiPhase.processing
                          ? null
                          : () => unawaited(_resolverConfirmacion('cancelar')),
                      child: const Text('Cancelar'),
                    ),
                  ),
                ],
              ),
            ],
            const SizedBox(height: 24),
            if (_phase == AiVoiceUiPhase.processing)
              const Padding(
                padding: EdgeInsets.all(12),
                child: CircularProgressIndicator(strokeWidth: 3),
              )
            else
              GestureDetector(
                behavior: HitTestBehavior.opaque,
                onLongPressStart: _bloqueoMicPorTts ? null : (_) => unawaited(_startRecording()),
                onLongPressEnd: _bloqueoMicPorTts ? null : (_) => unawaited(_stopAndSend()),
                onLongPressCancel: _bloqueoMicPorTts
                    ? null
                    : () {
                        if (_holding) unawaited(_stopAndSend());
                      },
                child: Opacity(
                  opacity: _bloqueoMicPorTts ? 0.35 : 1,
                  child: ScaleTransition(
                  scale: listening ? _pulse : const AlwaysStoppedAnimation(1.0),
                  child: Container(
                    width: 96,
                    height: 96,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: listening ? _listeningRed : AppColors.violet,
                      boxShadow: [
                        BoxShadow(
                          color: (listening ? _listeningRed : AppColors.violet)
                              .withValues(alpha: 0.5),
                          blurRadius: 28,
                          spreadRadius: listening ? 4 : 1,
                        ),
                      ],
                    ),
                    child: Icon(
                      listening ? Icons.mic_rounded : Icons.mic_none_rounded,
                      size: 44,
                      color: Colors.white,
                    ),
                  ),
                ),
                ),
              ),
            const SizedBox(height: 12),
            Text(
              _bloqueoMicPorTts
                  ? 'El micrófono está bloqueado mientras habla el asistente'
                  : listening
                      ? 'Suelta para enviar a la IA'
                      : 'Mantén presionado el micrófono',
              style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}
