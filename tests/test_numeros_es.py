"""Números y montos dichos en español antes del TTS."""
from __future__ import annotations

from app.services.numeros_es import entero_a_palabras, numeros_a_palabras


def test_enteros_basicos():
    assert entero_a_palabras(0) == "cero"
    assert entero_a_palabras(15) == "quince"
    assert entero_a_palabras(21) == "veintiuno"
    assert entero_a_palabras(100) == "cien"
    assert entero_a_palabras(1000) == "mil"


def test_montos_y_cantidades_a_palabras():
    assert numeros_a_palabras("3 camisas") == "tres camisas"
    assert (
        numeros_a_palabras("Voy a cobrar 12.50 dólares")
        == "Voy a cobrar doce dolares con cincuenta centavos"
    )
    assert numeros_a_palabras("son 20 USD") == "son veinte dolares"


def test_telefono_se_deletrea():
    dicho = numeros_a_palabras("teléfono 04141234567")
    assert dicho.startswith("teléfono cero cuatro uno cuatro")
    assert "cuatrocientos" not in dicho


def test_tts_nuevo_modelo_cae_a_tts1(monkeypatch):
    import app.services.ai_tts as tts

    monkeypatch.setattr(tts, "AI_TTS_API_KEY", "test-key")
    monkeypatch.setattr(tts, "AI_TTS_MODEL", "gpt-4o-mini-tts")
    monkeypatch.setattr(tts, "AI_TTS_VOICE", "nova")
    monkeypatch.setattr(tts, "AI_TTS_INSTRUCTIONS", "Habla en español.")
    llamadas: list[dict] = []

    def _speech(texto, *, model, instructions):
        llamadas.append({"model": model, "instructions": instructions, "input": texto})
        if model == "gpt-4o-mini-tts":
            raise RuntimeError("modelo no disponible")
        return "b64"

    monkeypatch.setattr(tts, "_openai_speech", _speech)
    monkeypatch.setattr(tts, "AI_TTS_PROVIDER", "openai")
    assert tts.sintetizar_voz_base64("son 2 dólares") == "b64"
    assert llamadas[0]["model"] == "gpt-4o-mini-tts"
    assert llamadas[0]["instructions"] == "Habla en español."
    assert "dos dolares" in llamadas[0]["input"]
    assert llamadas[1]["model"] == "tts-1"
    assert llamadas[1]["instructions"] is None
