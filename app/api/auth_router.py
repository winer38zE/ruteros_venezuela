import enum
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pocketbase.errors import ClientResponseError
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import huella_contraseña_log, verify_password
from app.core.usuario_password_hash import (
    hash_desde_modelo_usuario,
    nombre_campo_hash_lectura_login,
    prefijo_bcrypt,
)
from app.core.config import POCKETBASE_URL
from app.core.db import autenticar_admin_pocketbase, get_db
from app.core.pb_ready import PocketBaseNoDisponible
from app.core.pb_retry import ejecutar_con_reintentos
from app.core.seguridad import (
    cuenta_bloqueada_login,
    exigir_cupo_login,
    limpiar_fallos_login,
    registrar_fallo_login,
)
from app.models.core import Empresa, Pais, Usuario
from app.schemas.core import LoginResponse, PaisPublicoResponse

logger = logging.getLogger(__name__)

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=4)
    pais_id: str = Field(min_length=1, description="ID del país seleccionado en la app")


def _rol_como_texto(rol) -> str:
    if isinstance(rol, enum.Enum):
        return str(rol.value)
    return str(rol)


def _float_sueldo(valor) -> float:
    if valor is None:
        return 0.0
    try:
        return float(valor)
    except (TypeError, ValueError):
        return 0.0


def _usuario_a_respuesta(usuario: Usuario, pais: PaisPublicoResponse) -> LoginResponse:
    return LoginResponse(
        id=usuario.id,
        empresa_id=usuario.empresa_id,
        nombre=usuario.nombre,
        username=usuario.username,
        rol=_rol_como_texto(usuario.rol),
        activo=bool(usuario.activo),
        telefono=usuario.telefono,
        sueldo_base_usd=_float_sueldo(getattr(usuario, "sueldo_base_usd", None)),
        pais_id=str(usuario.pais_id) if usuario.pais_id else None,
        pais=pais,
    )


def _pais_a_publico(pais: Pais) -> PaisPublicoResponse:
    return PaisPublicoResponse.model_validate(pais)


def _obtener_pais_activo(db: Session, pais_id: str) -> Pais:
    pid = (pais_id or "").strip()
    if not pid:
        raise HTTPException(status_code=400, detail="Debes seleccionar un país")
    pais = db.query(Pais).filter(Pais.id == pid, Pais.activo.is_(True)).first()
    if pais is None:
        raise HTTPException(status_code=400, detail="País no válido o inactivo")
    return pais


def _resolver_y_validar_pais_usuario(
    db: Session,
    usuario: Usuario,
    pais_seleccionado: Pais,
) -> PaisPublicoResponse:
    empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
    pais_efectivo = usuario.pais_id or (empresa.pais_id if empresa else None)
    seleccion = str(pais_seleccionado.id)

    if pais_efectivo and str(pais_efectivo) != seleccion:
        raise HTTPException(
            status_code=403,
            detail="Este usuario no pertenece al país seleccionado. Elige el país correcto.",
        )

    if not usuario.pais_id:
        usuario.pais_id = pais_seleccionado.id
    if empresa is not None and not empresa.pais_id:
        empresa.pais_id = pais_seleccionado.id

    try:
        db.commit()
    except (ClientResponseError, SQLAlchemyError) as exc:
        db.rollback()
        logger.exception("Login: no se pudo guardar pais_id del usuario")
        raise HTTPException(
            status_code=503,
            detail="No se pudo actualizar la región del usuario. Intenta de nuevo.",
        ) from exc

    return _pais_a_publico(pais_seleccionado)


def _normalizar_username(username: str) -> str:
    return (username or "").strip()


def _consultar_usuario_activo(db: Session, clave: str) -> Usuario | None:
    return (
        db.query(Usuario)
        .filter(func.lower(Usuario.username) == clave)
        .first()
    )


def _consultar_con_reintentos(db: Session, clave: str) -> Usuario | None:
    reintentar_auth = True

    def operacion() -> Usuario | None:
        nonlocal reintentar_auth
        try:
            return _consultar_usuario_activo(db, clave)
        except ClientResponseError as exc:
            if reintentar_auth and exc.status in (401, 403):
                reintentar_auth = False
                autenticar_admin_pocketbase(getattr(db, "pb", None))
                return _consultar_usuario_activo(db, clave)
            raise

    return ejecutar_con_reintentos(
        operacion,
        max_intentos=5,
        etiqueta="Consulta usuarios PocketBase",
    )


def _buscar_usuario_por_username(db: Session, username: str) -> Usuario | None:
    clave = _normalizar_username(username).lower()
    if not clave:
        return None
    return _consultar_con_reintentos(db, clave)


def _log_login_401(
    username: str,
    password: str,
    *,
    hash_guardado: str | None = None,
) -> None:
    longitud_clave, sha_prefijo = huella_contraseña_log(password)
    hash_str = hash_guardado or ""
    logger.warning(
        "Login 401: username=%r clave_longitud=%d clave_sha256_prefijo=%s "
        "hash_campo=%r hash_longitud=%d hash_bcrypt_prefijo=%r",
        username,
        longitud_clave,
        sha_prefijo,
        nombre_campo_hash_lectura_login(),
        len(hash_str),
        prefijo_bcrypt(hash_str),
    )


def _error_base_datos(exc: Exception) -> HTTPException:
    logger.exception("Login: fallo al consultar usuarios en PocketBase (%s)", POCKETBASE_URL)
    return HTTPException(
        status_code=503,
        detail="Base de datos no disponible, intenta de nuevo",
    )


@router.post("/login", response_model=LoginResponse)
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
        pais_seleccionado = _obtener_pais_activo(db, body.pais_id)
    except HTTPException:
        raise
    except (ClientResponseError, SQLAlchemyError, RuntimeError) as exc:
        raise _error_base_datos(exc) from exc

    try:
        usuario = _buscar_usuario_por_username(db, username_entrada)
    except HTTPException:
        raise
    except PocketBaseNoDisponible as exc:
        raise _error_base_datos(exc) from exc
    except ClientResponseError as exc:
        if exc.status == 404:
            raise _error_base_datos(exc) from exc
        if exc.status in (401, 403):
            logger.warning(
                "Login fallido: PocketBase rechazó la consulta (%s) username=%r",
                exc.status,
                username_entrada,
            )
            _log_login_401(username_entrada, body.password)
            registrar_fallo_login(request, username_entrada)
            raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
        raise _error_base_datos(exc) from exc
    except (httpx.HTTPError, OSError, SQLAlchemyError, RuntimeError) as exc:
        raise _error_base_datos(exc) from exc

    if usuario is None:
        logger.warning("Login fallido: usuario no encontrado (username=%r)", username_entrada)
        _log_login_401(username_entrada, body.password)
        registrar_fallo_login(request, username_entrada)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not usuario.activo:
        logger.warning(
            "Login fallido: usuario inactivo (id=%s, username=%r)",
            usuario.id,
            usuario.username,
        )
        _log_login_401(username_entrada, body.password, hash_guardado=hash_desde_modelo_usuario(usuario))
        registrar_fallo_login(request, username_entrada)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    hash_guardado = hash_desde_modelo_usuario(usuario)
    valido = False
    try:
        valido = verify_password(body.password, hash_guardado)
    except Exception:
        logger.warning(
            "Login fallido: hash de contraseña inválido (id=%s, username=%r)",
            usuario.id,
            usuario.username,
        )
        valido = False

    if not valido:
        _log_login_401(
            username_entrada,
            body.password,
            hash_guardado=hash_guardado,
        )
        registrar_fallo_login(request, username_entrada)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    limpiar_fallos_login(request, username_entrada)
    pais_resp = _resolver_y_validar_pais_usuario(db, usuario, pais_seleccionado)
    logger.info(
        "Login OK (id=%s, username=%r, pais=%s)",
        usuario.id,
        usuario.username,
        pais_resp.codigo_iso,
    )
    return _usuario_a_respuesta(usuario, pais_resp)
