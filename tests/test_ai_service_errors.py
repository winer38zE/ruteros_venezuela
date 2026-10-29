"""Errores amigables del asistente IA (Groq model_not_found)."""
from __future__ import annotations

from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.ai_service import (
    _argumentos_transcripcion,
    _mensaje_error_llm,
    _mensaje_error_whisper,
    transcribir_audio,
)


def test_mensaje_llm_modelo_404_groq():
    exc = SimpleNamespace(status_code=404)
    msg = _mensaje_error_llm(exc)  # type: ignore[arg-type]
    assert "modelo de ia no está disponible" in msg.lower()
    assert "administrador" in msg.lower()


def test_mensaje_whisper_modelo_404():
    exc = Exception("Error code: 404 - model_not_found")
    msg = _mensaje_error_whisper(exc)
    assert "modelo de ia no está disponible" in msg.lower()


def test_gpt_transcribe_envia_languages_sin_language():
    kwargs = _argumentos_transcripcion(
        model="gpt-transcribe",
        buffer=BytesIO(b"audio"),
        language="ES",
        prompt="  productos  ",
    )
    assert kwargs["model"] == "gpt-transcribe"
    assert kwargs["extra_body"] == {"languages": ["es"]}
    assert kwargs["response_format"] == "json"
    assert kwargs["prompt"] == "productos"
    assert "language" not in kwargs
    assert "languages" not in kwargs


def test_transcripcion_nunca_envia_language():
    kwargs = _argumentos_transcripcion(
        model="gpt-transcribe",
        buffer=BytesIO(b"audio"),
        language="es",
        prompt=None,
    )
    assert kwargs["extra_body"] == {"languages": ["es"]}
    assert "language" not in kwargs
    assert "languages" not in kwargs


def test_transcribir_audio_lee_texto_y_dict(monkeypatch):
    import app.services.ai_service as ai_service

    monkeypatch.setattr(ai_service, "AI_WHISPER_API_KEY", "test-key")
    monkeypatch.setattr(ai_service, "AI_WHISPER_MODEL", "gpt-transcribe")
    cliente = MagicMock()
    cliente.audio.transcriptions.create.return_value = SimpleNamespace(text="venta de sabanas")
    monkeypatch.setattr(ai_service, "OpenAI", MagicMock(return_value=cliente))

    assert transcribir_audio(b"abc") == "venta de sabanas"
    enviado = cliente.audio.transcriptions.create.call_args.kwargs
    assert enviado["model"] == "gpt-transcribe"
    assert enviado["extra_body"]["languages"] == ["es"]
    assert "language" not in enviado

    cliente.audio.transcriptions.create.return_value = {"text": "cobro de juan"}
    assert transcribir_audio(b"abc") == "cobro de juan"
