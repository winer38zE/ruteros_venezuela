from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.core import Usuario
from app.schemas.core import UsuarioResponse

router = APIRouter()


class LoginRequest(BaseModel):
    username: str


@router.post("/login", response_model=UsuarioResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    usuario = (
        db.query(Usuario)
        .filter(Usuario.username == body.username, Usuario.activo.is_(True))
        .first()
    )
    if not usuario:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o inactivo")
    return usuario
