"""Asistente de voz por IA."""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

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
from app.services.ai_llm_tools import (
    HERRAMIENTAS_VOZ_TODAS,
    MENSAJE_CONFUSION_VOZ,
    mensaje_permiso_denegado,
)
import app.services.ai_voice_models  # noqa: F401 — registra ordenes_voz en ORM

from app.services.ai_voice_audit import registrar_orden_voz
from app.services.ai_voice_confirmacion import (
    construir_resumen_confirmacion,
    evaluar_respuesta_confirmacion,
    guardar_pendiente_confirmacion,
    limpiar_confirmacion,
    obtener_pendiente_confirmacion,
    parece_nueva_intencion_negocio,
    requiere_confirmacion,
)
from app.services.ai_voice_executor import VoiceUserError, ejecutar_herramienta_voz
from app.services.ai_voice_session import (
    historial_mensajes_para_llm,
    intent_memoria_pendiente,
    limpiar as limpiar_sesion_voz,
    obtener as obtener_sesion_voz,
    parcial_memoria,
    preparar_ejecucion,
    registrar_intercambio,
    texto_contexto_para_llm,
    transcripcion_debe_rechazarse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_MENSAJE_AUDIO_NO_ENTENDIDO = (
    "No entendí el audio. Mantén pulsado el micrófono y di tu pedido, cobro o «registrar cliente …»."
)

_HERRAMIENTAS_VALIDAS = HERRAMIENTAS_VOZ_TODAS | frozenset({"ninguna"})

_WHISPER_PALABRAS_CLAVE = (
    "Ventas, inventario, productos, sábanas, cobros, gastos, proveedores, facturas, reportes."
)


def _normalizar_herramienta(nombre: str | None) -> str:
    if not nombre:
        return "ninguna"
    limpio = str(nombre).strip()
    return limpio if limpio in _HERRAMIENTAS_VALIDAS else "ninguna"


def _sanitizar_json(valor: Any) -> Any:
    if valor is None or isinstance(valor, (str, int, float, bool)):
        return valor
    if isinstance(valor, uuid.UUID):
        return str(valor)
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {str(k): _sanitizar_json(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_sanitizar_json(v) for v in valor]
    return str(valor)


def _respuesta_voz(**kwargs) -> AiAudioComandoResponse:
    """Arma la respuesta JSON; TTS opcional (fallos no rompen el endpoint)."""
    kwargs["herramienta"] = _normalizar_herramienta(kwargs.get("herramienta"))
    detalle = kwargs.get("detalle")
    if detalle:
        kwargs["detalle"] = _sanitizar_json(detalle)

    mensaje = (kwargs.get("mensaje") or "").strip()
    if mensaje and kwargs.get("audio_base64") is None:
        try:
            kwargs["audio_base64"] = sintetizar_voz_base64(mensaje)
        except Exception:
            logger.exception("TTS falló al armar respuesta de voz")
            kwargs["audio_base64"] = None

    try:
        return AiAudioComandoResponse(**kwargs)
    except Exception:
        logger.exception("Validación de AiAudioComandoResponse falló")
        return AiAudioComandoResponse(
            transcripcion=str(kwargs.get("transcripcion") or ""),
            herramienta="ninguna",
            exito=bool(kwargs.get("exito")),
            mensaje=mensaje or "Respuesta procesada.",
            detalle={"codigo": "respuesta_normalizada"},
            audio_base64=kwargs.get("audio_base64"),
        )


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


@router.post("/reiniciar-sesion")
async def reiniciar_sesion_voz(
    usuario: Usuario = Depends(require_ruta_o_superior),
):
    """Olvida turnos pendientes (cerrar modal o «Nueva conversación» en la app)."""
    uid = str(usuario.id)
    limpiar_sesion_voz(uid)
    limpiar_confirmacion(uid)
    return {"ok": True}


@router.post("/audio-comando", response_model=AiAudioComandoResponse)
async def audio_comando(
    audio: UploadFile = File(..., description="Grabación de voz del usuario"),
    usuario: Usuario = Depends(require_ruta_o_superior),
    db=Depends(get_db),
):
    try:
        return await _procesar_audio_comando(audio, usuario, db)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error no controlado en audio-comando")
        return _respuesta_voz(
            transcripcion="",
            herramienta="ninguna",
            exito=False,
            mensaje="No pude procesar el audio. Intenta de nuevo.",
            detalle={"codigo": "error_interno", "detalle_tecnico": str(exc)[:240]},
        )


async def _procesar_audio_comando(
    audio: UploadFile,
    usuario: Usuario,
    db,
) -> AiAudioComandoResponse:
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

    whisper_extra = inventario.prompt_whisper()
    whisper_prompt = _WHISPER_PALABRAS_CLAVE
    if whisper_extra:
        whisper_prompt = f"{_WHISPER_PALABRAS_CLAVE} {whisper_extra}"
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

    resp_confirm = _procesar_confirmacion_pendiente(
        db,
        usuario,
        uid,
        transcripcion,
    )
    if resp_confirm is not None:
        return resp_confirm

    if transcripcion_debe_rechazarse(transcripcion):
        ses_prev = obtener_sesion_voz(uid)
        en_flujo_activo = bool(
            ses_prev
            and ses_prev.intent in ("registrar_cliente", "crear_pedido", "registrar_cobro")
        )
        en_registro_con_nombre = bool(
            ses_prev
            and ses_prev.intent == "registrar_cliente"
            and str((ses_prev.partial or {}).get("nombre") or "").strip()
        )
        if not en_flujo_activo and not en_registro_con_nombre:
            limpiar_sesion_voz(uid)
            return _respuesta_voz(
                transcripcion=transcripcion,
                herramienta="ninguna",
                exito=False,
                mensaje=_MENSAJE_AUDIO_NO_ENTENDIDO,
                detalle={"codigo": "audio_no_entendido"},
            )

    partes_contexto = []
    if inventario.consulta_ok:
        bloque_inv = inventario.bloque_inventario_llm()
        if bloque_inv:
            partes_contexto.append(bloque_inv)
    ctx_sesion = texto_contexto_para_llm(uid)
    if ctx_sesion:
        partes_contexto.append(ctx_sesion)
    contexto = "\n\n".join(partes_contexto)

    historial = historial_mensajes_para_llm(uid)
    try:
        herramienta, args, mensaje_libre = interpretar_texto_voz(
            transcripcion,
            contexto_sistema_extra=contexto or None,
            historial=historial,
            rol_usuario=usuario.rol,
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
        intent_guard = intent_memoria_pendiente(herramienta, transcripcion)
        herramienta_resp = _normalizar_herramienta(herramienta)
        if intent_guard == "registrar_cliente":
            parcial = parcial_memoria(intent_guard, args)
            registrar_intercambio(
                uid,
                intent=intent_guard,
                partial=parcial,
                transcripcion_usuario=transcripcion,
                respuesta_asistente=msg_usuario,
            )
        elif intent_guard in ("crear_pedido", "registrar_cobro"):
            parcial = parcial_memoria(intent_guard, args)
            registrar_intercambio(
                uid,
                intent=intent_guard,
                partial=parcial,
                transcripcion_usuario=transcripcion,
                respuesta_asistente=msg_usuario,
            )
        else:
            limpiar_sesion_voz(uid)
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta=herramienta_resp,
            exito=False,
            mensaje=msg_usuario,
            detalle={
                "codigo": "flujo_pendiente",
                "parcial": _sanitizar_json(parcial_memoria(intent_guard, args)),
                "intent": intent_guard,
            },
        )

    if not herramienta:
        msg = mensaje_libre or MENSAJE_CONFUSION_VOZ
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
            detalle={"codigo": "intencion_ambigua"},
        )

    if herramienta not in HERRAMIENTAS_VOZ_TODAS:
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=MENSAJE_CONFUSION_VOZ,
            detalle={"args": _sanitizar_json(args), "codigo": "herramienta_desconocida"},
        )

    denegado = mensaje_permiso_denegado(usuario.rol, herramienta)
    if denegado:
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=herramienta,
            parametros=args,
            resultado="permiso_denegado",
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=denegado,
            detalle={"codigo": "permiso_denegado", "herramienta": herramienta},
        )

    if requiere_confirmacion(herramienta):
        resumen, err_conf = construir_resumen_confirmacion(db, usuario, herramienta, args)
        if err_conf:
            registrar_orden_voz(
                db,
                usuario,
                transcripcion=transcripcion,
                herramienta=herramienta,
                parametros=args,
                resultado="error",
            )
            return _respuesta_voz(
                transcripcion=transcripcion,
                herramienta=herramienta,
                exito=False,
                mensaje=err_conf,
                detalle={"codigo": "confirmacion_invalida"},
            )
        guardar_pendiente_confirmacion(
            uid,
            herramienta=herramienta,
            args=args,
            resumen=resumen or "",
            transcripcion_origen=transcripcion,
        )
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=herramienta,
            parametros=args,
            resultado="pendiente_confirmacion",
        )
        registrar_intercambio(
            uid,
            intent=herramienta,
            partial={},
            transcripcion_usuario=transcripcion,
            respuesta_asistente=resumen,
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta=herramienta,
            exito=False,
            mensaje=resumen or "¿Confirmas?",
            detalle={"codigo": "confirmacion_pendiente"},
        )

    return _ejecutar_y_responder(
        db,
        usuario,
        uid,
        transcripcion,
        herramienta,
        args,
    )


def _procesar_confirmacion_pendiente(
    db,
    usuario: Usuario,
    uid: str,
    transcripcion: str,
) -> AiAudioComandoResponse | None:
    pend = obtener_pendiente_confirmacion(uid)
    if pend is None:
        return None

    accion = evaluar_respuesta_confirmacion(transcripcion)
    if accion == "ambiguo" and parece_nueva_intencion_negocio(transcripcion):
        limpiar_confirmacion(uid)
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=pend.herramienta,
            parametros=pend.args,
            resultado="cancelada",
        )
        return None

    if accion == "ambiguo":
        msg = f"{pend.resumen} Di sí para confirmar o no para cancelar."
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta=pend.herramienta,
            exito=False,
            mensaje=msg,
            detalle={"codigo": "confirmacion_pendiente"},
        )

    limpiar_confirmacion(uid)
    if accion == "rechazar":
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=pend.herramienta,
            parametros=pend.args,
            resultado="cancelada",
        )
        limpiar_sesion_voz(uid)
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta=pend.herramienta,
            exito=False,
            mensaje="Acción cancelada.",
            detalle={"codigo": "confirmacion_rechazada"},
        )

    denegado = mensaje_permiso_denegado(usuario.rol, pend.herramienta)
    if denegado:
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=pend.herramienta,
            parametros=pend.args,
            resultado="permiso_denegado",
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=denegado,
            detalle={"codigo": "permiso_denegado", "herramienta": pend.herramienta},
        )

    return _ejecutar_y_responder(
        db,
        usuario,
        uid,
        transcripcion,
        pend.herramienta,
        pend.args,
    )


def _ejecutar_y_responder(
    db,
    usuario: Usuario,
    uid: str,
    transcripcion: str,
    herramienta: str,
    args: dict[str, Any],
) -> AiAudioComandoResponse:
    denegado = mensaje_permiso_denegado(usuario.rol, herramienta)
    if denegado:
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=herramienta,
            parametros=args,
            resultado="permiso_denegado",
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta="ninguna",
            exito=False,
            mensaje=denegado,
            detalle={"codigo": "permiso_denegado", "herramienta": herramienta},
        )

    try:
        exito, mensaje, detalle, (wa_ok, wa_det) = ejecutar_herramienta_voz(
            db, usuario, herramienta, args
        )
    except VoiceUserError as exc:
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=herramienta,
            parametros=args,
            resultado="error",
        )
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
            registrar_orden_voz(
                db,
                usuario,
                transcripcion=transcripcion,
                herramienta=herramienta,
                parametros=args,
                resultado="error",
            )
            return _respuesta_voz(
                transcripcion=transcripcion,
                herramienta=herramienta,
                exito=False,
                mensaje=mensaje_err,
                detalle=detalle_err if isinstance(detalle_err, dict) else {},
            )
        raise
    except Exception as exc:
        logger.exception("Error ejecutando herramienta de voz %s", herramienta)
        registrar_orden_voz(
            db,
            usuario,
            transcripcion=transcripcion,
            herramienta=herramienta,
            parametros=args,
            resultado="error",
        )
        return _respuesta_voz(
            transcripcion=transcripcion,
            herramienta=herramienta,
            exito=False,
            mensaje="No pude completar la orden. Intenta de nuevo o repite con más detalle.",
            detalle={"codigo": "error_interno", "detalle_tecnico": str(exc)[:240]},
        )

    registrar_orden_voz(
        db,
        usuario,
        transcripcion=transcripcion,
        herramienta=herramienta,
        parametros=args,
        resultado="ok" if exito else "error",
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
