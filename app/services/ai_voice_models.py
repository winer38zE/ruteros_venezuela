"""Modelos ORM usados solo por el asistente de voz (colección ordenes_voz)."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, JSON, String, Text, UniqueConstraint

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


class MemoriaVoz(Base):
    """Apodos y vocabulario persistente del asistente (por empresa y usuario)."""

    __tablename__ = "memoria_voz"
    __table_args__ = (
        UniqueConstraint("empresa_id", "usuario_id", name="uq_memoria_voz_empresa_usuario"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, index=True)
    usuario_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False, index=True)
    apodos_clientes = Column(JSON, nullable=True)
    apodos_productos = Column(JSON, nullable=True)
    vocabulario_whisper = Column(Text, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
