"""Descarta audios demasiado cortos, en silencio o sin voz antes de usarlos."""
from __future__ import annotations

import struct
import wave
from io import BytesIO

DURACION_MINIMA_SEG = 0.45
RMS_MINIMO = 180
NO_SPEECH_PROB_MAX = 0.6


class AudioSinVoz(ValueError):
    """El archivo no tiene voz utilizable."""


def duracion_segundos(contenido: bytes, filename: str = "") -> float | None:
    nombre = (filename or "").lower()
    if nombre.endswith(".wav") or contenido[:4] == b"RIFF":
        return _duracion_wav(contenido)
    if nombre.endswith((".m4a", ".mp4", ".mp3")) or b"mvhd" in contenido[:4096] or b"mvhd" in contenido:
        return _duracion_mp4(contenido)
    return None


def volumen_rms(contenido: bytes, filename: str = "") -> float | None:
    nombre = (filename or "").lower()
    if nombre.endswith(".wav") or contenido[:4] == b"RIFF":
        return _rms_wav(contenido)
    return None


def validar_audio_grabado(contenido: bytes, filename: str = "") -> None:
    """Lanza AudioSinVoz si el clip es corto o queda por debajo del volumen mínimo."""
    if not contenido:
        raise AudioSinVoz("El archivo de audio está vacío.")
    duracion = duracion_segundos(contenido, filename)
    if duracion is not None and duracion < DURACION_MINIMA_SEG:
        raise AudioSinVoz("La grabación es demasiado corta.")
    rms = volumen_rms(contenido, filename)
    if rms is not None and rms < RMS_MINIMO:
        raise AudioSinVoz("No se detectó voz en el audio.")


def texto_desde_verbose(result) -> str:
    """Une segmentos de verbose_json y omite los que tienen no_speech_prob alto."""
    segmentos = getattr(result, "segments", None)
    if segmentos is None and isinstance(result, dict):
        segmentos = result.get("segments")
    if segmentos:
        partes: list[str] = []
        for seg in segmentos:
            prob = getattr(seg, "no_speech_prob", None)
            texto = getattr(seg, "text", None)
            if isinstance(seg, dict):
                prob = seg.get("no_speech_prob", prob)
                texto = seg.get("text", texto)
            if prob is not None and float(prob) >= NO_SPEECH_PROB_MAX:
                continue
            limpio = (texto or "").strip()
            if limpio:
                partes.append(limpio)
        return " ".join(partes).strip()
    texto = (getattr(result, "text", None) or "").strip()
    if not texto and isinstance(result, dict):
        texto = (result.get("text") or "").strip()
    return texto


def _duracion_wav(contenido: bytes) -> float | None:
    try:
        with wave.open(BytesIO(contenido), "rb") as wav:
            rate = wav.getframerate() or 0
            if rate <= 0:
                return None
            return wav.getnframes() / float(rate)
    except wave.Error:
        return None


def _rms_wav(contenido: bytes) -> float | None:
    try:
        with wave.open(BytesIO(contenido), "rb") as wav:
            frames = wav.readframes(wav.getnframes())
            ancho = wav.getsampwidth()
    except wave.Error:
        return None
    if not frames or ancho not in (1, 2):
        return 0.0
    if ancho == 1:
        muestras = [b - 128 for b in frames]
    else:
        cuenta = len(frames) // 2
        muestras = list(struct.unpack("<" + "h" * cuenta, frames[: cuenta * 2]))
    if not muestras:
        return 0.0
    return (sum(m * m for m in muestras) / len(muestras)) ** 0.5


def _duracion_mp4(contenido: bytes) -> float | None:
    indice = contenido.find(b"mvhd")
    if indice < 0 or indice + 32 > len(contenido):
        return None
    version = contenido[indice + 4]
    base = indice + 8
    try:
        if version == 0:
            timescale, duration = struct.unpack(">II", contenido[base + 8 : base + 16])
        else:
            timescale, duration = struct.unpack(">IQ", contenido[base + 16 : base + 28])
    except struct.error:
        return None
    if timescale <= 0:
        return None
    return duration / float(timescale)
