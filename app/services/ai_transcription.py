"""Transcripción de audio con API compatible OpenAI (Whisper)."""
from __future__ import annotations

import logging
import httpx

from app.core.config import AI_WHISPER_API_KEY, AI_WHISPER_BASE_URL, AI_WHISPER_MODEL

logger = logging.getLogger(__name__)


class AiTranscriptionError(RuntimeError):
    pass


def transcribir_audio(
    contenido: bytes,
    *,
    filename: str = "comando.m4a",
    content_type: str = "audio/mp4",
    language: str = "es",
) -> str:
    if not AI_WHISPER_API_KEY:
        raise AiTranscriptionError(
            "Transcripción no configurada. Defina AI_WHISPER_API_KEY o GROQ_API_KEY."
        )
    if not contenido:
        raise AiTranscriptionError("El archivo de audio está vacío.")

    url = f"{AI_WHISPER_BASE_URL}/audio/transcriptions"
    headers = {"Authorization": f"Bearer {AI_WHISPER_API_KEY}"}

    files = {"file": (filename, contenido, content_type)}
    data = {"model": AI_WHISPER_MODEL, "language": language, "response_format": "json"}

    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(url, headers=headers, data=data, files=files)
    except httpx.HTTPError as exc:
        logger.exception("Error de red transcribiendo audio")
        raise AiTranscriptionError(f"No se pudo transcribir el audio: {exc}") from exc

    if resp.status_code >= 400:
        logger.warning("Whisper respondió %s: %s", resp.status_code, resp.text[:400])
        raise AiTranscriptionError(
            f"Servicio de transcripción rechazó el audio ({resp.status_code})."
        )

    payload = resp.json()
    texto = (payload.get("text") or "").strip()
    if not texto:
        raise AiTranscriptionError("No se detectó voz en el audio.")
    return texto
