"""Errores amigables del asistente IA (Groq model_not_found)."""
from __future__ import annotations

from types import SimpleNamespace

from app.services.ai_service import _mensaje_error_llm, _mensaje_error_whisper


def test_mensaje_llm_modelo_404_groq():
    exc = SimpleNamespace(status_code=404)
    msg = _mensaje_error_llm(exc)  # type: ignore[arg-type]
    assert "modelo de ia no está disponible" in msg.lower()
    assert "administrador" in msg.lower()


def test_mensaje_whisper_modelo_404():
    exc = Exception("Error code: 404 - model_not_found")
    msg = _mensaje_error_whisper(exc)
    assert "modelo de ia no está disponible" in msg.lower()
