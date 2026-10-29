"""Modelos ORM usados solo por el asistente de voz (colección ordenes_voz)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String, Text

from app.models.core import Base, GUID, RolUsuario


class OrdenVoz(Base):
    __tablename__ = "ordenes_voz"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, index=True)
    usuario_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False, index=True)
    rol = Column(Enum(RolUsuario), nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    transcripcion = Column(Text, nullable=False, default="")
    herramienta = Column(String(64), nullable=False, default="ninguna")
    parametros = Column(JSON, nullable=True)
    resultado = Column(String(32), nullable=False)
