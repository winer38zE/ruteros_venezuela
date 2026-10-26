"""Reexporta transcripción Whisper (implementación en ai_service.py)."""
from app.services.ai_service import AiTranscriptionError, transcribir_audio

__all__ = ["AiTranscriptionError", "transcribir_audio"]
