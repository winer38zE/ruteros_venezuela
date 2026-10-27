"""Text-to-Speech: OpenAI (tts-1) si hay clave, si no gTTS → MP3 en base64."""
from __future__ import annotations

import base64
import io
import logging

from app.core.config import (
    AI_TTS_API_KEY,
    AI_TTS_BASE_URL,
    AI_TTS_MODEL,
    AI_TTS_PROVIDER,
    AI_TTS_VOICE,
)

logger = logging.getLogger(__name__)


def _tts_openai_base64(texto: str) -> str | None:
    if not AI_TTS_API_KEY:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=AI_TTS_API_KEY, base_url=AI_TTS_BASE_URL)
        response = client.audio.speech.create(
            model=AI_TTS_MODEL,
            voice=AI_TTS_VOICE,
            input=texto,
            response_format="mp3",
        )
        raw = response.content
        if not raw:
            return None
        return base64.b64encode(raw).decode("ascii")
    except Exception:
        logger.exception("Error TTS OpenAI (model=%s)", AI_TTS_MODEL)
        return None


def _tts_gtts_base64(texto: str, *, lang: str = "es") -> str | None:
    try:
        from gtts import gTTS
    except ImportError:
        logger.warning("gTTS no instalado; respuesta sin audio.")
        return None

    try:
        buffer = io.BytesIO()
        gTTS(text=texto, lang=lang, slow=False).write_to_fp(buffer)
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode("ascii")
    except Exception:
        logger.exception("Error generando audio gTTS")
        return None


def sintetizar_voz_base64(texto: str, *, lang: str = "es") -> str | None:
    """Convierte texto a MP3 codificado en base64. Devuelve None si falla."""
    limpio = (texto or "").strip()
    if not limpio:
        return None

    provider = AI_TTS_PROVIDER or "auto"
    if provider == "gtts":
        return _tts_gtts_base64(limpio, lang=lang)

    if provider in ("openai", "auto") and AI_TTS_API_KEY:
        audio = _tts_openai_base64(limpio)
        if audio:
            return audio
        if provider == "openai":
            return None

    return _tts_gtts_base64(limpio, lang=lang)
