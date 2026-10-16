import enum
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pocketbase.errors import ClientResponseError
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import verify_password
from app.core.config import POCKETBASE_URL
from app.core.db import autenticar_admin_pocketbase, get_db
from app.core.seguridad import (
    cuenta_bloqueada_login,
    exigir_cupo_login,
    limpiar_fallos_login,
    registrar_fallo_login,
)
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


def _normalizar_username(username: str) -> str:
    return (username or "").strip()


def _buscar_usuario_por_username(db: Session, username: str) -> Usuario | None:
    clave = _normalizar_username(username).lower()
    if not clave:
        return None
    try:
        return (
            db.query(Usuario)
            .filter(func.lower(Usuario.username) == clave)
            .first()
        )
    except ClientResponseError as exc:
        if exc.status not in (401, 403):
            raise
        autenticar_admin_pocketbase(getattr(db, "pb", None))
        return (
            db.query(Usuario)
            .filter(func.lower(Usuario.username) == clave)
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
    username_entrada = _normalizar_username(body.username)
    if cuenta_bloqueada_login(request, username_entrada):
        logger.warning(
            "Login fallido: cuenta bloqueada por intentos (username=%r, ip=%s)",
            username_entrada,
            request.client.host if request.client else "sin-ip",
        )
        raise HTTPException(
            status_code=429,
            detail="Demasiados intentos de ingreso. Espera unos minutos e inténtalo de nuevo.",
        )
    exigir_cupo_login(request, username_entrada)
    try:
        usuario = _buscar_usuario_por_username(db, username_entrada)
    except HTTPException:
        raise
    except ClientResponseError as exc:
        if exc.status == 404:
            raise _error_base_datos(exc) from exc
        if exc.status in (401, 403):
            logger.warning(
                "Login fallido: PocketBase rechazó la consulta (%s) username=%r",
                exc.status,
                username_entrada,
            )
            registrar_fallo_login(request, username_entrada)
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        raise _error_base_datos(exc) from exc
    except (httpx.HTTPError, OSError, SQLAlchemyError, RuntimeError) as exc:
        raise _error_base_datos(exc) from exc

    if usuario is None:
        logger.warning("Login fallido: usuario no encontrado (username=%r)", username_entrada)
        registrar_fallo_login(request, username_entrada)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not usuario.activo:
        logger.warning(
            "Login fallido: usuario inactivo (id=%s, username=%r)",
            usuario.id,
            usuario.username,
        )
        registrar_fallo_login(request, username_entrada)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    valido = False
    try:
        valido = verify_password(body.password, usuario.password_hash)
    except Exception:
        logger.warning(
            "Login fallido: hash de contraseña inválido (id=%s, username=%r)",
            usuario.id,
            usuario.username,
        )
        valido = False

    if not valido:
        logger.warning(
            "Login fallido: contraseña incorrecta (id=%s, username=%r)",
            usuario.id,
            usuario.username,
        )
        registrar_fallo_login(request, username_entrada)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    limpiar_fallos_login(request, username_entrada)
    logger.info("Login OK (id=%s, username=%r)", usuario.id, usuario.username)
    return _usuario_a_respuesta(usuario)
