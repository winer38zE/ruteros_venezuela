from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.core import Empresa, Usuario


def obtener_empresa_tenant(db: Session, usuario: Usuario) -> Empresa:
    """Empresa del usuario autenticado (aislamiento multi-tenant)."""
    empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=400, detail="Empresa no encontrada para este usuario")
    if empresa.activa is False:
        raise HTTPException(status_code=403, detail="La empresa está inactiva")
    return empresa
