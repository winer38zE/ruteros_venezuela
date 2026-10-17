import logging
import os

from pocketbase.errors import ClientResponseError
from sqlalchemy import func

from app.api.auth import get_password_hash, log_huella_demo_password_configurada, obtener_demo_password
from app.core.db import get_pocketbase_client
from app.core.demo_hash_verificacion import verificar_hashes_usuarios_demo
from app.core.pb_orm import mapper
from app.core.pb_schema import preparar_esquema_pocketbase, verificar_colecciones_completas
from app.core.pb_orm.session import SessionLocal
from app.models.core import Almacen, Empresa, RolUsuario, Usuario

logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "dueno"
DEFAULT_NOMBRE = "Administrador ED NET PRO"
DEFAULT_EMPRESA = "ED NET PRO"

DEMO_USUARIOS = [
    (DEFAULT_USERNAME, DEFAULT_NOMBRE, RolUsuario.DUENO),
    ("admin", "Jefe de Operaciones", RolUsuario.ADMINISTRADOR),
    ("vendedor", "Vendedor Demo", RolUsuario.VENDEDOR),
    ("cobrador", "Cobrador Demo", RolUsuario.COBRADOR),
]


def _asegurar_usuario_demo(db, empresa_id, username: str, nombre: str, rol) -> None:
    """Crea o restablece un usuario demo (activo + hash bcrypt actualizado)."""
    username_norm = username.strip().lower()
    password = obtener_demo_password()
    existente = (
        db.query(Usuario)
        .filter(func.lower(Usuario.username) == username_norm)
        .first()
    )
    if existente:
        existente.password_hash = get_password_hash(password)
        existente.activo = True
        existente.nombre = nombre
        existente.rol = rol
        if existente.empresa_id != empresa_id:
            existente.empresa_id = empresa_id
        return
    db.add(
        Usuario(
            nombre=nombre,
            username=username_norm,
            password_hash=get_password_hash(password),
            rol=rol,
            empresa_id=empresa_id,
            activo=True,
        )
    )


def _asegurar_almacen_principal(db, empresa_id) -> None:
    existe = (
        db.query(Almacen)
        .filter(Almacen.empresa_id == empresa_id, Almacen.activo.is_(True))
        .first()
    )
    if existe:
        return
    db.add(
        Almacen(
            empresa_id=empresa_id,
            nombre="Almacén Principal",
            es_principal=True,
            activo=True,
        )
    )


def _confirmar_demo_listo(db) -> None:
    dueno = (
        db.query(Usuario)
        .filter(func.lower(Usuario.username) == DEFAULT_USERNAME, Usuario.activo.is_(True))
        .first()
    )
    empresa = db.query(Empresa).first()
    if not dueno or not empresa:
        raise RuntimeError(
            "Bootstrap incompleto: falta empresa o usuario 'dueno' tras el commit."
        )
    logger.info(
        "Bootstrap OK — empresa '%s' (id=%s), dueño '%s' (id=%s).",
        empresa.nombre,
        empresa.id,
        dueno.username,
        dueno.id,
    )


def asegurar_usuario_admin() -> None:
    """Sincroniza datos demo: esquema PocketBase + usuarios con clave DEMO_PASSWORD."""
    if not os.getenv("ADMIN_EMAIL", "").strip() or not os.getenv("ADMIN_PASSWORD", ""):
        raise RuntimeError("ADMIN_EMAIL y ADMIN_PASSWORD requeridos para el bootstrap.")

    from app.core.config import POCKETBASE_URL

    pb = get_pocketbase_client(POCKETBASE_URL)
    preparar_esquema_pocketbase(pb)
    verificar_colecciones_completas(pb)

    db = SessionLocal()
    try:
        empresa = db.query(Empresa).first()
        if not empresa:
            empresa = Empresa(nombre=DEFAULT_EMPRESA)
            db.add(empresa)
            db.flush()

        _asegurar_almacen_principal(db, empresa.id)
        for username, nombre, rol in DEMO_USUARIOS:
            _asegurar_usuario_demo(db, empresa.id, username, nombre, rol)

        db.commit()
        logger.info(
            "Usuarios demo sincronizados (dueno, admin, vendedor, cobrador) — empresa '%s'.",
            empresa.nombre,
        )
        log_huella_demo_password_configurada(logger, contexto="Bootstrap")
        _confirmar_demo_listo(db)

        demo_ids: list[tuple[str, str]] = []
        for username, _nombre, _rol in DEMO_USUARIOS:
            username_norm = username.strip().lower()
            u = (
                db.query(Usuario)
                .filter(func.lower(Usuario.username) == username_norm)
                .first()
            )
            if u is not None:
                demo_ids.append((username_norm, mapper.record_id(u)))
        if demo_ids:
            verificar_hashes_usuarios_demo(pb, demo_ids)
    except ClientResponseError as exc:
        db.rollback()
        if getattr(exc, "status", None) == 404:
            raise RuntimeError(
                "Bootstrap abortado: la colección no existe en PocketBase. "
                "El arranque debe crear el esquema antes de insertar registros."
            ) from exc
        raise
    except Exception:
        db.rollback()
        logger.exception("Error al crear usuario administrador por defecto.")
        raise
    finally:
        db.close()
