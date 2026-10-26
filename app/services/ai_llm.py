"""Cliente LLM con function calling (Groq / OpenAI / DeepSeek)."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import AI_LLM_API_KEY, AI_LLM_BASE_URL, AI_LLM_MODEL
from app.services.ai_llm_tools import HERRAMIENTAS_OPENAI, SYSTEM_PROMPT, parse_tool_call

logger = logging.getLogger(__name__)


class AiLlmError(RuntimeError):
    pass


def interpretar_texto_voz(texto: str) -> tuple[str | None, dict[str, Any], str | None]:
    """
    Devuelve (herramienta, argumentos, mensaje_asistente_sin_tool).
    Si hay herramienta, mensaje_asistente puede ser None.
    """
    if not AI_LLM_API_KEY:
        raise AiLlmError("LLM no configurado. Defina AI_LLM_API_KEY o GROQ_API_KEY.")

    url = f"{AI_LLM_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {AI_LLM_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": AI_LLM_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": texto},
        ],
        "tools": HERRAMIENTAS_OPENAI,
        "tool_choice": "auto",
    }

    try:
        with httpx.Client(timeout=90.0) as client:
            resp = client.post(url, headers=headers, json=body)
    except httpx.HTTPError as exc:
        logger.exception("Error de red con LLM")
        raise AiLlmError(f"No se pudo contactar al modelo de IA: {exc}") from exc

    if resp.status_code >= 400:
        logger.warning("LLM respondió %s: %s", resp.status_code, resp.text[:500])
        raise AiLlmError(f"El modelo de IA rechazó la solicitud ({resp.status_code}).")

    data = resp.json()
    choices = data.get("choices") or []
    if not choices:
        raise AiLlmError("Respuesta vacía del modelo de IA.")

    message = choices[0].get("message") or {}
    tool, args = parse_tool_call(message)
    if tool:
        return tool, args, None
    contenido = (message.get("content") or "").strip()
    return None, {}, contenido or "No entendí el comando. Intenta de nuevo."
