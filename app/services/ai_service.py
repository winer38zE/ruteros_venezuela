"""Asistente de voz: Whisper + LLM con function calling (SDK OpenAI → Groq u OpenAI)."""
from __future__ import annotations

import io
import json
import logging
from typing import Any

from openai import OpenAI

from app.core.config import (
    AI_LLM_API_KEY,
    AI_LLM_BASE_URL,
    AI_LLM_MODEL,
    AI_WHISPER_API_KEY,
    AI_WHISPER_BASE_URL,
    AI_WHISPER_MODEL,
)
from app.services.ai_llm_tools import HERRAMIENTAS_OPENAI, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AiServiceError(RuntimeError):
    """Error de transcripción o interpretación IA."""


class AiTranscriptionError(AiServiceError):
    pass


class AiLlmError(AiServiceError):
    pass


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
) -> str:
    """Whisper vía SDK OpenAI (compatible Groq: whisper-large-v3)."""
    if not contenido:
        raise AiTranscriptionError("El archivo de audio está vacío.")

    _ = content_type  # reservado; el SDK infiere formato por extensión del nombre
    client = _whisper_client()
    buffer = io.BytesIO(contenido)
    buffer.name = filename

    try:
        result = client.audio.transcriptions.create(
            model=AI_WHISPER_MODEL,
            file=buffer,
            language=language,
            response_format="json",
        )
    except Exception as exc:
        logger.exception("Error transcribiendo con Whisper")
        raise AiTranscriptionError(f"No se pudo transcribir el audio: {exc}") from exc

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
    return out


def interpretar_texto_voz(texto: str) -> tuple[str | None, dict[str, Any], str | None]:
    """
    Function calling con el SDK oficial.
    Devuelve (herramienta, argumentos, mensaje_sin_tool).
    """
    client = _llm_client()
    try:
        completion = client.chat.completions.create(
            model=AI_LLM_MODEL,
            temperature=0.1,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": texto},
            ],
            tools=HERRAMIENTAS_OPENAI,
            tool_choice="auto",
        )
    except Exception as exc:
        logger.exception("Error LLM function calling")
        raise AiLlmError(f"No se pudo contactar al modelo de IA: {exc}") from exc

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
    return None, {}, contenido or "No entendí el comando. Intenta de nuevo."
