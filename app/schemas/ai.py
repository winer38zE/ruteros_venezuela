"""Esquemas del asistente de voz por IA."""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AiAudioComandoResponse(BaseModel):
    transcripcion: str
    herramienta: Optional[
        Literal["crear_pedido", "registrar_cliente", "registrar_cobro", "ninguna"]
    ] = None
    exito: bool
    mensaje: str
    detalle: dict[str, Any] = Field(default_factory=dict)
    whatsapp_enviado: bool = False
    whatsapp_detalle: Optional[str] = None
    audio_base64: Optional[str] = Field(
        default=None,
        description="Respuesta hablada (MP3 en base64) para reproducir en la app.",
    )
