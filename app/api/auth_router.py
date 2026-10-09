from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.auth import verify_password
from app.core.db import get_db
from app.models.core import Usuario
from app.schemas.core import UsuarioResponse

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=4)


@router.post("/login", response_model=UsuarioResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    usuario = (
        db.query(Usuario)
        .filter(Usuario.username == body.username.strip(), Usuario.activo.is_(True))
        .first()
    )
    valido = False
    if usuario is not None:
        try:
            valido = verify_password(body.password, usuario.password_hash)
        except Exception:
            valido = False
    if not valido or usuario is None:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    return usuario
