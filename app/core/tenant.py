from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.core import Empresa, Usuario


def _empresa_habilitada(empresa: Empresa) -> bool:
    """None = legacy sin campo en PocketBase; se considera activa."""
    if empresa.activa is None:
        return True
    return bool(empresa.activa)


def obtener_empresa_tenant(db: Session, usuario: Usuario) -> Empresa:
    """Empresa del usuario autenticado (aislamiento multi-tenant)."""
    empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
    if not empresa:
        raise HTTPException(status_code=400, detail="Empresa no encontrada para este usuario")
    if not _empresa_habilitada(empresa):
        raise HTTPException(status_code=403, detail="La empresa está inactiva")
    return empresa
