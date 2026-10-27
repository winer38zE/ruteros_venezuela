import 'dart:io';

import 'package:flutter/foundation.dart';

import '../config/api_config.dart';
import 'api_service.dart';

enum AiVoiceUiPhase {
  idle,
  listening,
  processing,
  success,
  error,
}

class AiVoiceCommandResult {
  const AiVoiceCommandResult({
    required this.transcripcion,
    required this.exito,
    required this.mensaje,
    this.herramienta,
    this.detalle = const {},
    this.whatsappEnviado = false,
    this.whatsappDetalle,
    this.audioBase64,
  });

  factory AiVoiceCommandResult.fromJson(Map<String, dynamic> json) {
    return AiVoiceCommandResult(
      transcripcion: json['transcripcion']?.toString() ?? '',
      herramienta: json['herramienta']?.toString(),
      exito: json['exito'] == true,
      mensaje: json['mensaje']?.toString() ?? '',
      detalle: json['detalle'] is Map
          ? Map<String, dynamic>.from(json['detalle'] as Map)
          : const {},
      whatsappEnviado: json['whatsapp_enviado'] == true,
      whatsappDetalle: json['whatsapp_detalle']?.toString(),
      audioBase64: json['audio_base64']?.toString(),
    );
  }

  final String transcripcion;
  final String? herramienta;
  final bool exito;
  final String mensaje;
  final Map<String, dynamic> detalle;
  final bool whatsappEnviado;
  final String? whatsappDetalle;
  final String? audioBase64;
}

class AiVoiceService {
  AiVoiceService(this._api);

  final ApiService _api;

  Future<AiVoiceCommandResult> enviarAudio(File file) async {
    final bytes = await file.readAsBytes();
    final name = file.path.split(Platform.pathSeparator).last;
    // Ruta fuera de /api/v1 (montada en FastAPI como /api/ai/...).
    final data = await _api.postMultipartAbsolute(
      '${ApiConfig.serverOrigin}/api/ai/audio-comando',
      const {},
      fileField: 'audio',
      bytes: bytes,
      filename: name.isNotEmpty ? name : 'comando.m4a',
      timeout: const Duration(seconds: 120),
    );
    if (data is! Map<String, dynamic>) {
      throw ApiException(0, 'Respuesta inválida del asistente de voz.');
    }
    if (kDebugMode) {
      debugPrint('AI voz: ${data['herramienta']} exito=${data['exito']}');
    }
    return AiVoiceCommandResult.fromJson(data);
  }
}
