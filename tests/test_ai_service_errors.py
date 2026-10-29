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


# Parámetros que Groq documenta para whisper-large-v3-turbo.
_PARAMS_GROQ_WHISPER = {
    "file",
    "url",
    "model",
    "language",
    "prompt",
    "response_format",
    "temperature",
    "timestamp_granularities",
}


def test_whisper_groq_envia_language_es_y_vocabulario_en_prompt():
    vocabulario = "clientes: Juan Pérez. productos: sábana king"
    kwargs = _argumentos_transcripcion(
        model="whisper-large-v3-turbo",
        buffer=BytesIO(b"audio"),
        language="ES",
        prompt=f"  {vocabulario}  ",
    )
    assert kwargs["model"] == "whisper-large-v3-turbo"
    assert kwargs["language"] == "es"
    assert kwargs["prompt"] == vocabulario
    assert kwargs["response_format"] == "verbose_json"
    assert "languages" not in kwargs
    assert "extra_body" not in kwargs
    assert set(kwargs) <= _PARAMS_GROQ_WHISPER


def test_transcripcion_sin_pista_no_envia_prompt_ni_languages():
    kwargs = _argumentos_transcripcion(
        model="whisper-large-v3-turbo",
        buffer=BytesIO(b"audio"),
        language="es",
        prompt=None,
    )
    assert kwargs["language"] == "es"
    assert "prompt" not in kwargs
    assert "languages" not in kwargs
    assert "extra_body" not in kwargs
    assert set(kwargs) <= _PARAMS_GROQ_WHISPER


def test_transcribir_audio_lee_texto_y_dict(monkeypatch):
    import app.services.ai_service as ai_service

    monkeypatch.setattr(ai_service, "AI_WHISPER_API_KEY", "test-key")
    monkeypatch.setattr(ai_service, "AI_WHISPER_MODEL", "whisper-large-v3-turbo")
    cliente = MagicMock()
    cliente.audio.transcriptions.create.return_value = SimpleNamespace(text="venta de sabanas")
    monkeypatch.setattr(ai_service, "OpenAI", MagicMock(return_value=cliente))

    assert transcribir_audio(b"abc", prompt="  clientes: Ana. productos: toalla  ") == "venta de sabanas"
    enviado = cliente.audio.transcriptions.create.call_args.kwargs
    assert enviado["model"] == "whisper-large-v3-turbo"
    assert enviado["language"] == "es"
    assert enviado["prompt"] == "clientes: Ana. productos: toalla"
    assert enviado["response_format"] == "verbose_json"
    assert "languages" not in enviado
    assert "extra_body" not in enviado
    assert set(enviado) <= _PARAMS_GROQ_WHISPER

    cliente.audio.transcriptions.create.return_value = {"text": "cobro de juan"}
    assert transcribir_audio(b"abc") == "cobro de juan"
    sin_pista = cliente.audio.transcriptions.create.call_args.kwargs
    assert sin_pista["language"] == "es"
    assert "prompt" not in sin_pista
    assert "languages" not in sin_pista
    assert "extra_body" not in sin_pista
    assert set(sin_pista) <= _PARAMS_GROQ_WHISPER
