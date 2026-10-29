"""Text-to-Speech: gpt-4o-mini-tts con estilo; si falla, tts-1 y luego gTTS."""
from __future__ import annotations

import base64
import io
import logging

from app.core.config import (
    AI_TTS_API_KEY,
    AI_TTS_BASE_URL,
    AI_TTS_INSTRUCTIONS,
    AI_TTS_MODEL,
    AI_TTS_PROVIDER,
    AI_TTS_VOICE,
)
from app.services.numeros_es import numeros_a_palabras

logger = logging.getLogger(__name__)

_MODELO_RESPALDO = "tts-1"


def _modelo_acepta_instrucciones(modelo: str) -> bool:
    nombre = (modelo or "").strip().lower()
    return nombre.startswith("gpt-4o") and "tts" in nombre


def _openai_speech(texto: str, *, model: str, instructions: str | None) -> str | None:
    from openai import OpenAI

    client = OpenAI(api_key=AI_TTS_API_KEY, base_url=AI_TTS_BASE_URL)
    kwargs: dict = {
        "model": model,
        "voice": AI_TTS_VOICE,
        "input": texto,
        "response_format": "mp3",
    }
    if instructions and _modelo_acepta_instrucciones(model):
        kwargs["instructions"] = instructions
    response = client.audio.speech.create(**kwargs)
    raw = response.content
    if not raw:
        return None
    return base64.b64encode(raw).decode("ascii")


def _tts_openai_base64(texto: str) -> str | None:
    if not AI_TTS_API_KEY:
        return None
    modelo = AI_TTS_MODEL or "gpt-4o-mini-tts"
    instrucciones = AI_TTS_INSTRUCTIONS or None
    try:
        audio = _openai_speech(texto, model=modelo, instructions=instrucciones)
        if audio:
            return audio
    except Exception:
        logger.exception("Error TTS OpenAI (model=%s)", modelo)
    if modelo == _MODELO_RESPALDO:
        return None
    try:
        return _openai_speech(texto, model=_MODELO_RESPALDO, instructions=None)
    except Exception:
        logger.exception("Error TTS de respaldo (model=%s)", _MODELO_RESPALDO)
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
    """Convierte texto a MP3 en base64. Nunca lanza: si el modelo nuevo falla, usa tts-1."""
    limpio = numeros_a_palabras((texto or "").strip())
    if not limpio:
        return None

    try:
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
    except Exception:
        logger.exception("Error inesperado en sintetizar_voz_base64")
        return None
