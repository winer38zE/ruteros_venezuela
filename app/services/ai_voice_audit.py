"""Registro persistente de órdenes del asistente de voz (ordenes_voz)."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.pb_orm.ids import nuevo_id_pocketbase
from app.models.core import RolUsuario, Usuario
from app.services.ai_voice_models import OrdenVoz

logger = logging.getLogger(__name__)

RESULTADOS_VALIDOS = frozenset(
    {"ok", "rechazada", "cancelada", "error", "pendiente_confirmacion", "permiso_denegado"}
)


def registrar_orden_voz(
    db: Session,
    usuario: Usuario,
    *,
    transcripcion: str,
    herramienta: str,
    parametros: dict[str, Any] | None,
    resultado: str,
) -> None:
    if resultado not in RESULTADOS_VALIDOS:
        resultado = "error"
    try:
        fila = OrdenVoz(
            id=nuevo_id_pocketbase(),
            empresa_id=usuario.empresa_id,
            usuario_id=usuario.id,
            rol=usuario.rol,
            transcripcion=(transcripcion or "")[:4000],
            herramienta=(herramienta or "ninguna")[:64],
            parametros=_sanitizar_parametros(parametros),
            resultado=resultado,
        )
        db.add(fila)
        db.commit()
    except Exception:
        logger.exception("No se pudo guardar ordenes_voz")
        try:
            db.rollback()
        except Exception:
            pass


def _sanitizar_parametros(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if not params:
        return None
    out: dict[str, Any] = {}
    for k, v in params.items():
        if k.lower() in ("password", "token", "api_key", "secret"):
            continue
        if isinstance(v, (str, int, float, bool)) or v is None:
            out[k] = v
        elif isinstance(v, list):
            out[k] = v[:50]
        elif isinstance(v, dict):
            out[k] = _sanitizar_parametros(v) or {}
        else:
            out[k] = str(v)[:500]
    return out
