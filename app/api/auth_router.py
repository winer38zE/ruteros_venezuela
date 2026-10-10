from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.api.auth import verify_password
from app.core.db import get_db
from app.core.seguridad import exigir_cupo_login, limpiar_fallos_login, registrar_fallo_login
from app.models.core import Usuario
from app.schemas.core import UsuarioResponse

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=4)


@router.post("/login", response_model=UsuarioResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    exigir_cupo_login(request, body.username)
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
        registrar_fallo_login(request, body.username)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    limpiar_fallos_login(request, body.username)
    return usuario
