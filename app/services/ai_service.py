"""Asistente de voz: Whisper + LLM con function calling (SDK OpenAI → Groq u OpenAI)."""
from __future__ import annotations

import io
import json
import logging
from typing import Any

from openai import APIStatusError, OpenAI

from app.core.config import (
    AI_LLM_API_KEY,
    AI_LLM_BASE_URL,
    AI_LLM_MAX_TOKENS,
    AI_LLM_MODEL,
    AI_LLM_TEMPERATURE,
    AI_WHISPER_API_KEY,
    AI_WHISPER_BASE_URL,
    AI_WHISPER_MODEL,
)
from app.services.ai_llm_tools import (
    MENSAJE_CONFUSION_VOZ,
    SYSTEM_PROMPT,
    herramientas_openai_para_rol,
)
from app.services.ai_product_context import (
    ContextoProductos,
    MENSAJE_INVENTARIO_VACIO,
    obtener_contexto_productos,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AiLlmError",
    "AiTranscriptionError",
    "ContextoProductos",
    "MENSAJE_INVENTARIO_VACIO",
    "interpretar_texto_voz",
    "obtener_contexto_productos",
    "transcribir_audio",
]


class AiServiceError(RuntimeError):
    """Error de transcripción o interpretación IA."""


class AiTranscriptionError(AiServiceError):
    pass


class AiLlmError(AiServiceError):
    pass


_MENSAJE_MODELO_IA_NO_DISPONIBLE = (
    "El modelo de IA no está disponible. Contacta al administrador."
)


def _es_modelo_ia_no_disponible(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status == 404:
        return True
    if isinstance(exc, APIStatusError) and exc.status_code == 404:
        return True
    texto = str(exc).lower()
    return any(
        frag in texto
        for frag in (
            "model_not_found",
            "does not exist",
            "decommissioned",
            "no longer supported",
            "model is decommissioned",
        )
    )


def _mensaje_error_llm(exc: Exception) -> str:
    if _es_modelo_ia_no_disponible(exc):
        logger.error(
            "Groq/OpenAI modelo no disponible (model=%s): %s",
            AI_LLM_MODEL,
            exc,
        )
        return _MENSAJE_MODELO_IA_NO_DISPONIBLE
    return f"No se pudo contactar al modelo de IA: {exc}"


def _mensaje_error_whisper(exc: Exception) -> str:
    if _es_modelo_ia_no_disponible(exc):
        logger.error(
            "Whisper modelo no disponible (model=%s): %s",
            AI_WHISPER_MODEL,
            exc,
        )
        return _MENSAJE_MODELO_IA_NO_DISPONIBLE
    return f"No se pudo transcribir el audio: {exc}"


def _llm_client() -> OpenAI:
    if not AI_LLM_API_KEY:
        raise AiLlmError("LLM no configurado. Defina AI_LLM_API_KEY o GROQ_API_KEY.")
    return OpenAI(api_key=AI_LLM_API_KEY, base_url=AI_LLM_BASE_URL)


def _whisper_client() -> OpenAI:
    if not AI_WHISPER_API_KEY:
        raise AiTranscriptionError(
            "Transcripción no configurada. Defina AI_WHISPER_API_KEY o GROQ_API_KEY."
        )
    return OpenAI(api_key=AI_WHISPER_API_KEY, base_url=AI_WHISPER_BASE_URL)


def transcribir_audio(
    contenido: bytes,
    *,
    filename: str = "comando.m4a",
    content_type: str = "audio/mp4",
    language: str = "es",
    prompt: str | None = None,
) -> str:
    """Whisper vía SDK OpenAI (compatible Groq: whisper-large-v3)."""
    if not contenido:
        raise AiTranscriptionError("El archivo de audio está vacío.")

    _ = content_type  # reservado; el SDK infiere formato por extensión del nombre
    client = _whisper_client()
    buffer = io.BytesIO(contenido)
    buffer.name = filename

    try:
        kwargs: dict[str, Any] = {
            "model": AI_WHISPER_MODEL,
            "file": buffer,
            "language": language,
            "response_format": "json",
        }
        if prompt and prompt.strip():
            kwargs["prompt"] = prompt.strip()
        result = client.audio.transcriptions.create(**kwargs)
    except Exception as exc:
        logger.exception("Error transcribiendo con Whisper")
        raise AiTranscriptionError(_mensaje_error_whisper(exc)) from exc

    texto = (getattr(result, "text", None) or "").strip()
    if not texto and isinstance(result, dict):
        texto = (result.get("text") or "").strip()
    if not texto:
        raise AiTranscriptionError("No se detectó voz en el audio.")
    return texto


def _normalizar_argumentos_herramienta(nombre: str, args: dict[str, Any]) -> dict[str, Any]:
    """Alias que el modelo a veces usa (nombre_cliente, monto, etc.)."""
    out = dict(args)
    if nombre == "crear_pedido":
        if not out.get("cliente_nombre") and out.get("nombre_cliente"):
            out["cliente_nombre"] = out.pop("nombre_cliente")
    if nombre == "registrar_cobro":
        if out.get("monto_usd") is None and out.get("monto") is not None:
            out["monto_usd"] = out.pop("monto")
        if not out.get("cliente_nombre") and out.get("nombre_cliente"):
            out["cliente_nombre"] = out.pop("nombre_cliente")
    if nombre == "registrar_producto_inventario":
        if out.get("precio_venta") is None and out.get("precio") is not None:
            out["precio_venta"] = out.pop("precio")
        if out.get("stock_inicial") is None and out.get("stock") is not None:
            out["stock_inicial"] = out.pop("stock")
    if nombre == "registrar_gasto":
        if out.get("monto") is None and out.get("monto_usd") is not None:
            out["monto"] = out.pop("monto_usd")
    if nombre == "crear_factura_proveedor":
        if out.get("proveedor_nombre") is None and out.get("nombre_proveedor"):
            out["proveedor_nombre"] = out.pop("nombre_proveedor")
    return out


def interpretar_texto_voz(
    texto: str,
    *,
    contexto_sistema_extra: str | None = None,
    historial: list[dict[str, str]] | None = None,
    rol_usuario: Any = None,
) -> tuple[str | None, dict[str, Any], str | None]:
    """
    Function calling con el SDK oficial.
    Devuelve (herramienta, argumentos, mensaje_sin_tool).
    """
    system = SYSTEM_PROMPT
    if contexto_sistema_extra and contexto_sistema_extra.strip():
        system = f"{SYSTEM_PROMPT}\n\n{contexto_sistema_extra.strip()}"

    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    if historial:
        for item in historial[-8:]:
            role = (item.get("role") or "").strip()
            content = (item.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": texto})

    tools = herramientas_openai_para_rol(rol_usuario)

    client = _llm_client()
    try:
        completion = client.chat.completions.create(
            model=AI_LLM_MODEL,
            temperature=AI_LLM_TEMPERATURE,
            max_tokens=AI_LLM_MAX_TOKENS,
            messages=messages,
            tools=tools,
            tool_choice="auto",
        )
    except Exception as exc:
        logger.exception("Error LLM function calling (model=%s)", AI_LLM_MODEL)
        raise AiLlmError(_mensaje_error_llm(exc)) from exc

    if not completion.choices:
        raise AiLlmError("Respuesta vacía del modelo de IA.")

    message = completion.choices[0].message
    tool_calls = message.tool_calls or []
    if tool_calls:
        call = tool_calls[0]
        fn = call.function
        name = fn.name
        raw = fn.arguments or "{}"
        try:
            args = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except json.JSONDecodeError:
            args = {}
        return name, _normalizar_argumentos_herramienta(name, args), None

    contenido = (message.content or "").strip()
    if not contenido:
        return None, {}, MENSAJE_CONFUSION_VOZ
    if len(contenido) < 120 and any(
        frag in contenido.lower()
        for frag in ("no entend", "aclara", "no estoy seguro", "¿qué deseas")
    ):
        return None, {}, MENSAJE_CONFUSION_VOZ
    return None, {}, contenido or MENSAJE_CONFUSION_VOZ
