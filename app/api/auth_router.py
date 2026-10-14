import enum
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pocketbase.errors import ClientResponseError
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import verify_password
from app.core.config import POCKETBASE_URL
from app.core.db import autenticar_admin_pocketbase, get_db
from app.core.seguridad import exigir_cupo_login, limpiar_fallos_login, registrar_fallo_login
from app.models.core import Usuario
from app.schemas.core import UsuarioResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=4)


def _rol_como_texto(rol) -> str:
    if isinstance(rol, enum.Enum):
        return str(rol.value)
    return str(rol)


def _usuario_a_respuesta(usuario: Usuario) -> UsuarioResponse:
    return UsuarioResponse(
        id=usuario.id,
        empresa_id=usuario.empresa_id,
        nombre=usuario.nombre,
        username=usuario.username,
        rol=_rol_como_texto(usuario.rol),
        activo=bool(usuario.activo),
        telefono=usuario.telefono,
    )


def _buscar_usuario_activo(db: Session, username: str) -> Usuario | None:
    username = username.strip()
    try:
        return (
            db.query(Usuario)
            .filter(Usuario.username == username, Usuario.activo.is_(True))
            .first()
        )
    except ClientResponseError as exc:
        if exc.status not in (401, 403):
            raise
        autenticar_admin_pocketbase(getattr(db, "pb", None))
        return (
            db.query(Usuario)
            .filter(Usuario.username == username, Usuario.activo.is_(True))
            .first()
        )


def _error_base_datos(exc: Exception) -> HTTPException:
    logger.exception("Login: fallo al consultar usuarios en PocketBase (%s)", POCKETBASE_URL)
    return HTTPException(
        status_code=503,
        detail=(
            "El servidor no puede acceder a la base de datos. "
            "Verifica POCKETBASE_URL, ADMIN_EMAIL y ADMIN_PASSWORD en el servidor."
        ),
    )


@router.post("/login", response_model=UsuarioResponse)
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    exigir_cupo_login(request, body.username)
    try:
        usuario = _buscar_usuario_activo(db, body.username)
    except HTTPException:
        raise
    except (ClientResponseError, httpx.HTTPError, OSError, SQLAlchemyError, RuntimeError) as exc:
        raise _error_base_datos(exc) from exc

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
    return _usuario_a_respuesta(usuario)
