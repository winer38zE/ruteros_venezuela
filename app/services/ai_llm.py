"""Reexporta el asistente IA (implementación en ai_service.py)."""
from app.services.ai_service import AiLlmError, interpretar_texto_voz

__all__ = ["AiLlmError", "interpretar_texto_voz"]
