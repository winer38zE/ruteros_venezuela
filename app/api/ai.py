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
from app.services.ai_product_context import MENSAJE_INVENTARIO_VACIO, obtener_contexto_productos
from app.services.ai_transcription import AiTranscriptionError, transcribir_audio
from app.services.ai_tts import sintetizar_voz_base64
from app.services.ai_voice_executor import VoiceUserError, ejecutar_herramienta_voz
from app.services.ai_voice_session import (
    historial_mensajes_para_llm,
    limpiar as limpiar_sesion_voz,
    preparar_ejecucion,
    registrar_intercambio,
    texto_contexto_para_llm,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _respuesta_voz(**kwargs) -> AiAudioComandoResponse:
    """Arma la respuesta JSON e incluye TTS del mensaje al usuario."""
    mensaje = (kwargs.get("mensaje") or "").strip()
    if mensaje and kwargs.get("audio_base64") is None:
        kwargs["audio_base64"] = sintetizar_voz_base64(mensaje)
    return AiAudioComandoResponse(**kwargs)


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

    inventario = obtener_contexto_productos(db, usuario.empresa_id)
    if inventario.vacio:
        return _respuesta_voz(
            transcripcion="",
            herramienta="ninguna",
            exito=False,
            mensaje=MENSAJE_INVENTARIO_VACIO,
            detalle={"codigo": "inventario_vacio"},
        )

    whisper_prompt = inventario.prompt_whisper()
    try:
        transcripcion = transcribir_audio(
            contenido,
            filename=filename,
            content_type=ctype if ctype != "application/octet-stream" else "audio/mp4",
            prompt=whisper_prompt,
        )
    except AiTranscriptionError as exc:
        return _respuesta_voz(
            transcripcion="",
            herramienta="ninguna",
            exito=False,
            mensaje=str(exc),
            detalle={"codigo": "transcripcion_fallida"},
        )

    uid = str(usuario.id)
    partes_contexto = [
        inventario.bloque_inventario_llm(),
        texto_contexto_para_llm(uid),
    ]
    contexto = "\n\n".join(p for p in partes_contexto if p and p.strip())
    historial = historial_mensajes_para_llm(uid)
    try:
        herramienta, args, mensaje_libre = interpretar_texto_voz(
            transcripcion,
            contexto_sistema_extra=contexto,
            historial=historial,
        )
    except AiLlmError as exc:
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=str(exc),
            detalle={"codigo": "llm_fallido"},
        )

    herramienta, args, mensaje_pendiente, listo = preparar_ejecucion(
        uid,
        herramienta,
        args,
        transcripcion,
        mensaje_libre,
    )

    if not listo:
        msg_usuario = (
            mensaje_pendiente or mensaje_libre or "Necesito un dato más para continuar."
        )
        intent_guard = herramienta or "registrar_cliente"
        registrar_intercambio(
            uid,
            intent=intent_guard,
            partial=args or {},
            transcripcion_usuario=transcripcion,
            respuesta_asistente=msg_usuario,
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta=herramienta or "ninguna",
            exito=False,
            mensaje=msg_usuario,
            detalle={
                "codigo": "flujo_pendiente",
                "parcial": args,
                "intent": herramienta,
            },
        )

    if not herramienta:
        msg = mensaje_libre or "No pude identificar una acción."
        registrar_intercambio(
            uid,
            intent="general",
            partial={},
            transcripcion_usuario=transcripcion,
            respuesta_asistente=msg,
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=msg,
            detalle={},
        )

    if herramienta == "registrar_producto":
        msg = (
            mensaje_libre
            or "Para guardar el producto, completa precio y stock en la app móvil por ahora."
        )
        registrar_intercambio(
            uid,
            intent="general",
            partial={},
            transcripcion_usuario=transcripcion,
            respuesta_asistente=msg,
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=msg,
            detalle={"codigo": "registrar_producto_manual"},
        )

    if herramienta not in ("crear_pedido", "registrar_cliente", "registrar_cobro"):
        return _respuesta_voz(
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
        return _respuesta_voz(
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
            return _respuesta_voz(
                transcripcion=transcripcion,
                herramienta=herramienta,
                exito=False,
                mensaje=mensaje_err,
                detalle=detalle_err,
            )
        raise
    except Exception as exc:
        logger.exception("Error ejecutando herramienta de voz %s", herramienta)
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta=herramienta,
            exito=False,
            mensaje="No pude completar la orden. Intenta de nuevo o repite con más detalle.",
            detalle={"codigo": "error_interno", "detalle_tecnico": str(exc)},
        )

    if exito:
        registrar_intercambio(
            uid,
            intent=herramienta,
            partial={},
            transcripcion_usuario=transcripcion,
            respuesta_asistente=mensaje,
        )
        limpiar_sesion_voz(uid)

    mensaje_final = mensaje
    if exito and wa_ok and "whatsapp" not in mensaje.lower():
        mensaje_final = f"{mensaje} WhatsApp enviado."

    return _respuesta_voz(
        transcripcion=transcripcion,
        herramienta=herramienta,
        exito=exito,
        mensaje=mensaje_final,
        detalle=detalle,
        whatsapp_enviado=wa_ok,
        whatsapp_detalle=wa_det,
    )
