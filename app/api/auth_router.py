import enum
import logging
from datetime import timedelta
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from pocketbase.errors import ClientResponseError
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token,
    huella_contraseña_log,
    verify_password,
)
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
from app.models.core import Empresa, Pais, RolUsuario, Usuario
from app.schemas.core import LoginResponse, PaisPublicoResponse
from app.core.pb_orm import mapper
from app.services.paises_seed import pais_por_defecto

logger = logging.getLogger(__name__)

# Cuentas demo: una fila por username; el país de sesión lo elige la app en cada login.
_DEMO_USERNAMES = frozenset({"dueno", "admin", "vendedor", "cobrador"})

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str = Field(min_length=4)
    pais_id: Optional[str] = Field(
        default=None,
        description="ID del país seleccionado en la app (obligatorio salvo fallback dueño)",
    )

    @field_validator("pais_id", mode="before")
    @classmethod
    def _normalizar_pais_id(cls, v):
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None


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


def _emitir_token_jwt(usuario: Usuario, pais: Pais) -> str:
    """JWT con pais_id efectivo de la sesión (dueño multiregión usa el del request)."""
    return create_access_token(
        {
            "sub": str(usuario.id),
            "username": usuario.username,
            "empresa_id": str(usuario.empresa_id),
            "rol": _rol_como_texto(usuario.rol),
            "pais_id": str(pais.id),
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def _usuario_a_respuesta(
    usuario: Usuario,
    pais: PaisPublicoResponse,
    *,
    access_token: str,
) -> LoginResponse:
    return LoginResponse(
        id=usuario.id,
        empresa_id=usuario.empresa_id,
        nombre=usuario.nombre,
        username=usuario.username,
        rol=_rol_como_texto(usuario.rol),
        activo=bool(usuario.activo),
        telefono=usuario.telefono,
        sueldo_base_usd=_float_sueldo(getattr(usuario, "sueldo_base_usd", None)),
        pais_id=str(pais.id),
        pais=pais,
        access_token=access_token,
        token_type="bearer",
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


def _es_dueno_cuenta(usuario: Usuario) -> bool:
    if (usuario.username or "").strip().lower() == "dueno":
        return True
    rol = _rol_como_texto(usuario.rol).upper()
    return rol in ("DUEÑO", "DUENO", "OWNER") or usuario.rol == RolUsuario.DUENO


def _acceso_multiregion(usuario: Usuario) -> bool:
    """Dueño, admin y cuentas demo: país de sesión = request (no users.pais_id)."""
    uname = (usuario.username or "").strip().lower()
    if uname in _DEMO_USERNAMES:
        return True
    if _es_dueno_cuenta(usuario):
        return True
    return usuario.rol == RolUsuario.ADMINISTRADOR


def _pais_para_login(db: Session, body: LoginRequest, *, multiregion: bool) -> Pais:
    """País efectivo de sesión: el pais_id del JSON (independiente del guardado en users)."""
    pid = body.pais_id
    if not pid:
        print(
            f"[LOGIN] pais_id vacío username={body.username!r} multiregion={multiregion}"
        )
        if not multiregion:
            raise HTTPException(status_code=400, detail="Debes seleccionar un país")
        defecto = pais_por_defecto(db)
        if defecto is None or not bool(defecto.activo):
            raise HTTPException(status_code=400, detail="Debes seleccionar un país")
        logger.warning(
            "Login multiregión: pais_id vacío; usando país por defecto %s",
            defecto.codigo_iso,
        )
        return defecto
    return _obtener_pais_activo(db, pid)


def _resolver_y_validar_pais_usuario(
    db: Session,
    usuario: Usuario,
    pais_seleccionado: Pais,
) -> PaisPublicoResponse:
    empresa = db.query(Empresa).filter(Empresa.id == usuario.empresa_id).first()
    multiregion = _acceso_multiregion(usuario)
    pais_efectivo = usuario.pais_id or (empresa.pais_id if empresa else None)
    seleccion = str(pais_seleccionado.id)

    if multiregion:
        if pais_efectivo and str(pais_efectivo) != seleccion:
            logger.info(
                "Login multiregión: región solicitada %s (registro previo %s, rol=%s)",
                seleccion,
                pais_efectivo,
                _rol_como_texto(usuario.rol),
            )
        # Dueño/admin: país de sesión = request; no se exige coincidir con users.pais_id.
        return _pais_a_publico(pais_seleccionado)
    else:
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


def _filtro_pocketbase_username(clave: str) -> str:
    esc = clave.replace("\\", "\\\\").replace("'", "\\'")
    return f"username:lower = '{esc}'"


def _listar_usuarios_por_username(db: Session, clave: str) -> list[Usuario]:
    """Lista usuarios en PocketBase solo por username (nunca filtra por pais_id)."""
    filtro = _filtro_pocketbase_username(clave)
    logger.info("Login PocketBase filter=%r", filtro)
    print(f"[LOGIN] PocketBase filter={filtro!r} (sin pais_id)")

    pb = getattr(db, "pb", None)
    if pb is not None:
        coll = mapper.collection_name(Usuario)
        usuarios: list[Usuario] = []
        page = 1
        per_page = 200
        while True:
            batch = pb.collection(coll).get_list(
                page,
                per_page,
                query_params={"filter": filtro},
            )
            for rec in batch.items:
                data = mapper.record_payload(rec)
                obj = mapper.record_to_model(Usuario, data)
                if hasattr(db, "_register_loaded"):
                    db._register_loaded(obj)
                usuarios.append(obj)
            if len(batch.items) < per_page:
                break
            page += 1
        return usuarios

    return (
        db.query(Usuario)
        .filter(func.lower(Usuario.username) == clave)
        .all()
    )


def _listar_usuarios_con_reintentos(db: Session, clave: str) -> list[Usuario]:
    reintentar_auth = True

    def operacion() -> list[Usuario]:
        nonlocal reintentar_auth
        try:
            return _listar_usuarios_por_username(db, clave)
        except ClientResponseError as exc:
            if reintentar_auth and exc.status in (401, 403):
                reintentar_auth = False
                autenticar_admin_pocketbase(getattr(db, "pb", None))
                return _listar_usuarios_por_username(db, clave)
            raise

    return ejecutar_con_reintentos(
        operacion,
        max_intentos=5,
        etiqueta="Consulta usuarios PocketBase",
    )


def _elegir_usuario_tras_password(
    candidatos: list[Usuario],
    password: str,
) -> Usuario | None:
    """Si hay duplicados por país en PB, elige el que valida bcrypt (prioriza dueño/admin)."""
    validos: list[Usuario] = []
    for candidato in candidatos:
        if not candidato.activo:
            continue
        hash_guardado = hash_desde_modelo_usuario(candidato)
        try:
            if verify_password(password, hash_guardado):
                validos.append(candidato)
        except Exception:
            continue
    if not validos:
        return None
    if len(validos) == 1:
        return validos[0]
    for candidato in validos:
        if _acceso_multiregion(candidato):
            return candidato
    return validos[0]


def _autenticar_usuario_login(
    db: Session,
    username: str,
    password: str,
) -> Usuario | None:
    clave = _normalizar_username(username).lower()
    if not clave:
        return None
    candidatos = _listar_usuarios_con_reintentos(db, clave)
    logger.debug(
        "Login PocketBase username=%r candidatos=%d (sin pais_id en filtro)",
        clave,
        len(candidatos),
    )
    return _elegir_usuario_tras_password(candidatos, password)


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
        detail="Servidor no disponible, reintenta",
    )


def _http_error_desde_pocketbase(exc: ClientResponseError) -> HTTPException:
    status = int(getattr(exc, "status", 0) or 0)
    if status in (502, 503, 504):
        return _error_base_datos(exc)
    if status in (401, 403):
        logger.warning("Login: PocketBase admin/superuser rechazó consulta (status=%s)", status)
        return HTTPException(
            status_code=503,
            detail="Servidor no disponible, reintenta",
        )
    if status == 404:
        return _error_base_datos(exc)
    return _error_base_datos(exc)


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

    logger.debug(
        "Login intento username=%r pais_id=%r",
        username_entrada,
        body.pais_id,
    )

    try:
        usuario = _autenticar_usuario_login(db, username_entrada, body.password)
    except HTTPException:
        raise
    except PocketBaseNoDisponible as exc:
        raise _error_base_datos(exc) from exc
    except ClientResponseError as exc:
        raise _http_error_desde_pocketbase(exc) from exc
    except (httpx.HTTPError, OSError, SQLAlchemyError, RuntimeError) as exc:
        raise _error_base_datos(exc) from exc

    if usuario is None:
        logger.warning(
            "Login fallido: usuario no encontrado o contraseña inválida (username=%r)",
            username_entrada,
        )
        _log_login_401(username_entrada, body.password)
        registrar_fallo_login(request, username_entrada)
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    limpiar_fallos_login(request, username_entrada)

    multiregion = _acceso_multiregion(usuario)
    try:
        pais_seleccionado = _pais_para_login(db, body, multiregion=multiregion)
    except HTTPException:
        raise
    except (ClientResponseError, SQLAlchemyError, RuntimeError) as exc:
        raise _error_base_datos(exc) from exc

    pais_resp = _resolver_y_validar_pais_usuario(db, usuario, pais_seleccionado)
    access_token = _emitir_token_jwt(usuario, pais_seleccionado)
    pais_id_seleccionado = str(pais_seleccionado.id)
    logger.info(
        "Login exitoso para %s en el país %s",
        usuario.username,
        pais_id_seleccionado,
    )
    logger.info(
        "Login OK (id=%s, username=%r, pais=%s)",
        usuario.id,
        usuario.username,
        pais_resp.codigo_iso,
    )
    return _usuario_a_respuesta(usuario, pais_resp, access_token=access_token)
