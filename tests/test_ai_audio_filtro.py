"""Audios cortos, en silencio o sin voz no llegan a la transcripción."""
from __future__ import annotations

import struct
import wave
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.services.ai_audio_filtro import (
    NO_SPEECH_PROB_MAX,
    texto_desde_verbose,
    validar_audio_grabado,
    AudioSinVoz,
)
from app.services.ai_service import AiTranscriptionError, transcribir_audio


def _wav(segundos: float, amplitud: int, rate: int = 8000) -> bytes:
    n = max(1, int(segundos * rate))
    buf = BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(struct.pack("<" + "h" * n, *([amplitud] * n)))
    return buf.getvalue()


def test_audio_corto_no_se_transcribe(monkeypatch):
    import app.services.ai_service as ai_service

    cliente = MagicMock()
    monkeypatch.setattr(ai_service, "OpenAI", MagicMock(return_value=cliente))
    monkeypatch.setattr(ai_service, "AI_WHISPER_API_KEY", "test-key")
    with pytest.raises(AiTranscriptionError, match="demasiado corta"):
        transcribir_audio(_wav(0.2, 8000), filename="comando.wav")
    cliente.audio.transcriptions.create.assert_not_called()


def test_audio_en_silencio_no_se_transcribe(monkeypatch):
    import app.services.ai_service as ai_service

    cliente = MagicMock()
    monkeypatch.setattr(ai_service, "OpenAI", MagicMock(return_value=cliente))
    monkeypatch.setattr(ai_service, "AI_WHISPER_API_KEY", "test-key")
    with pytest.raises(AiTranscriptionError, match="No se detectó voz"):
        transcribir_audio(_wav(1.0, 0), filename="comando.wav")
    cliente.audio.transcriptions.create.assert_not_called()


def test_segmento_con_no_speech_prob_alto_se_descarta(monkeypatch):
    import app.services.ai_service as ai_service

    monkeypatch.setattr(ai_service, "AI_WHISPER_API_KEY", "test-key")
    cliente = MagicMock()
    cliente.audio.transcriptions.create.return_value = SimpleNamespace(
        text="Puedo ver el video.",
        segments=[
            {"text": "Puedo ver el video.", "no_speech_prob": NO_SPEECH_PROB_MAX},
        ],
    )
    monkeypatch.setattr(ai_service, "OpenAI", MagicMock(return_value=cliente))
    with pytest.raises(AiTranscriptionError, match="No se detectó voz"):
        transcribir_audio(_wav(1.0, 4000), filename="comando.wav")


def test_segmento_con_voz_se_conserva():
    texto = texto_desde_verbose(
        {
            "text": "sí",
            "segments": [
                {"text": " ruido ", "no_speech_prob": 0.9},
                {"text": " sí ", "no_speech_prob": 0.1},
            ],
        }
    )
    assert texto == "sí"


def test_wav_con_volumen_pasa_el_filtro():
    validar_audio_grabado(_wav(1.0, 4000), "comando.wav")


def test_vacio_es_sin_voz():
    with pytest.raises(AudioSinVoz):
        validar_audio_grabado(b"", "comando.wav")
