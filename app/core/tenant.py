import logging

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.core import Empresa, Usuario

logger = logging.getLogger(__name__)


def _reactivar_empresa_si_hace_falta(db: Session, empresa: Empresa) -> None:
    """Registros viejos en PocketBase suelen tener activa=false al añadir el campo."""
    if empresa.activa is True:
        return
    prev = empresa.activa
    empresa.activa = True
    db.flush()
    logger.warning(
        "Empresa '%s' (%s) reactivada (activa era %r).",
        empresa.nombre,
        empresa.id,
        prev,
    )


def obtener_empresa_tenant(db: Session, usuario: Usuario) -> Empresa:
    """Empresa del usuario autenticado (aislamiento multi-tenant)."""
    empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=400, detail="Empresa no encontrada para este usuario")
    _reactivar_empresa_si_hace_falta(db, empresa)
    return empresa


def empresas_destino_tasas(db: Session, empresa_id=None) -> list[Empresa]:
    """Empresas donde el scheduler o la sync manual deben persistir tasas."""
    query = db.query(Empresa)
    if empresa_id is not None:
        query = query.filter(Empresa.id == empresa_id)
    candidatas = query.all()
    if not candidatas:
        if empresa_id is not None:
            raise ValueError(f"No existe empresa {empresa_id} para registrar tasas")
        raise ValueError("No hay empresas registradas para registrar tasas")

    activas = [e for e in candidatas if e.activa is True]
    if activas:
        return activas

    logger.warning(
        "Tasas automáticas: ninguna empresa con activa=true (%d candidata(s)); "
        "reactivando registros legacy PocketBase.",
        len(candidatas),
    )
    for empresa in candidatas:
        _reactivar_empresa_si_hace_falta(db, empresa)
    db.flush()
    return candidatas
