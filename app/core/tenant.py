from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.core import Empresa


def obtener_empresa_tenant(db: Session) -> Empresa:
    empresa = db.query(Empresa).first()
    if not empresa:
        raise HTTPException(status_code=400, detail="Debes crear una empresa primero")
    return empresa
