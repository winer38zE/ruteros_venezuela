"""Asistente de voz por IA."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import AI_ENABLED
from app.core.db import get_db
from app.core.deps import require_ruta_o_superior
from app.models.core import Usuario
from app.schemas.ai import AiAudioComandoResponse
from app.services.ai_llm import AiLlmError, interpretar_texto_voz
from app.services.ai_transcription import AiTranscriptionError, transcribir_audio
from app.services.ai_voice_executor import VoiceUserError, ejecutar_herramienta_voz

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_AUDIO_BYTES = 12 * 1024 * 1024
_MIME_PERMITIDOS = {
    "audio/m4a",
    "audio/mp4",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
    "audio/webm",
    "audio/ogg",
    "application/octet-stream",
}


@router.post("/audio-comando", response_model=AiAudioComandoResponse)
async def audio_comando(
    audio: UploadFile = File(..., description="Grabación de voz del usuario"),
    usuario: Usuario = Depends(require_ruta_o_superior),
    db=Depends(get_db),
):
    if not AI_ENABLED:
        raise HTTPException(
            status_code=503,
            detail=(
                "Asistente de voz no configurado. Defina AI_LLM_API_KEY y "
                "AI_WHISPER_API_KEY (o GROQ_API_KEY) en el servidor."
            ),
        )

    contenido = await audio.read()
    if len(contenido) > _MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="Audio demasiado grande (máx. 12 MB).")
    if len(contenido) < 256:
        raise HTTPException(status_code=400, detail="Grabación demasiado corta.")

    ctype = (audio.content_type or "application/octet-stream").split(";")[0].strip().lower()
    if ctype not in _MIME_PERMITIDOS:
        logger.info("Content-Type audio recibido: %s", ctype)

    filename = audio.filename or "comando.m4a"
    try:
        transcripcion = transcribir_audio(
            contenido,
            filename=filename,
            content_type=ctype if ctype != "application/octet-stream" else "audio/mp4",
        )
    except AiTranscriptionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    try:
        herramienta, args, mensaje_libre = interpretar_texto_voz(transcripcion)
    except AiLlmError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if not herramienta:
        return AiAudioComandoResponse(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=mensaje_libre or "No pude identificar una acción.",
            detalle={},
        )

    if herramienta not in ("crear_pedido", "registrar_cliente", "registrar_cobro"):
        return AiAudioComandoResponse(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=f"Herramienta no soportada: {herramienta}",
            detalle={"args": args},
        )

    try:
        exito, mensaje, detalle, (wa_ok, wa_det) = ejecutar_herramienta_voz(
            db, usuario, herramienta, args
        )
    except VoiceUserError as exc:
        return AiAudioComandoResponse(
            transcripcion=transcripcion,
            herramienta=herramienta,
            exito=False,
            mensaje=exc.message,
            detalle=exc.detalle,
        )
    except HTTPException as exc:
        if exc.status_code in (400, 404, 422):
            detalle_err = exc.detail if isinstance(exc.detail, dict) else {}
            mensaje_err = (
                exc.detail
                if isinstance(exc.detail, str)
                else str(exc.detail)
            )
            return AiAudioComandoResponse(
                transcripcion=transcripcion,
                herramienta=herramienta,
                exito=False,
                mensaje=mensaje_err,
                detalle=detalle_err,
            )
        raise
    except Exception as exc:
        logger.exception("Error ejecutando herramienta de voz %s", herramienta)
        return AiAudioComandoResponse(
            transcripcion=transcripcion,
            herramienta=herramienta,
            exito=False,
            mensaje="No pude completar la orden. Intenta de nuevo o repite con más detalle.",
            detalle={"codigo": "error_interno", "detalle_tecnico": str(exc)},
        )

    mensaje_final = mensaje
    if exito and wa_ok and "whatsapp" not in mensaje.lower():
        mensaje_final = f"{mensaje} WhatsApp enviado."

    return AiAudioComandoResponse(
        transcripcion=transcripcion,
        herramienta=herramienta,
        exito=exito,
        mensaje=mensaje_final,
        detalle=detalle,
        whatsapp_enviado=wa_ok,
        whatsapp_detalle=wa_det,
    )
