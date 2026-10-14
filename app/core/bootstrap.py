import logging
import os

from pocketbase.errors import ClientResponseError

from app.api.auth import get_password_hash
from app.core.db import get_pocketbase_client
from app.core.pb_schema import preparar_esquema_pocketbase, verificar_colecciones_completas
from app.core.pb_orm.session import SessionLocal
from app.models.core import Almacen, Empresa, RolUsuario, Usuario

logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "dueno"
DEFAULT_PASSWORD = "123456"
DEFAULT_NOMBRE = "Administrador ED NET PRO"
DEFAULT_EMPRESA = "ED NET PRO"

DEMO_USUARIOS = [
    ("admin", "Jefe de Operaciones", RolUsuario.ADMINISTRADOR, "123456"),
    ("vendedor", "Vendedor Demo", RolUsuario.VENDEDOR, "123456"),
    ("cobrador", "Cobrador Demo", RolUsuario.COBRADOR, "123456"),
]


def _crear_usuario_si_no_existe(db, empresa_id, username, nombre, rol, password) -> None:
    if db.query(Usuario).filter(Usuario.username == username).first():
        return
    db.add(
        Usuario(
            nombre=nombre,
            username=username,
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
    dueno = db.query(Usuario).filter(Usuario.username == DEFAULT_USERNAME, Usuario.activo.is_(True)).first()
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
    """Inserta datos demo solo si el esquema PocketBase ya existe y responde."""
    if not os.getenv("ADMIN_EMAIL", "").strip() or not os.getenv("ADMIN_PASSWORD", ""):
        raise RuntimeError("ADMIN_EMAIL y ADMIN_PASSWORD requeridos para el bootstrap.")

    pb = get_pocketbase_client(os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/"))
    preparar_esquema_pocketbase(pb)
    verificar_colecciones_completas(pb)

    db = SessionLocal()
    try:
        existe_activo = db.query(Usuario).filter(Usuario.activo.is_(True)).first()
        if existe_activo:
            empresa = db.query(Empresa).first()
            if empresa:
                _asegurar_almacen_principal(db, empresa.id)
                for username, nombre, rol, pwd in DEMO_USUARIOS:
                    _crear_usuario_si_no_existe(db, empresa.id, username, nombre, rol, pwd)
                db.commit()
                _confirmar_demo_listo(db)
            return

        admin_existente = (
            db.query(Usuario)
            .filter(Usuario.username.in_(["dueno", "admin"]))
            .first()
        )
        if admin_existente:
            if not admin_existente.activo:
                admin_existente.activo = True
            empresa = db.query(Empresa).filter(Empresa.id == admin_existente.empresa_id).first()
            if empresa:
                _asegurar_almacen_principal(db, empresa.id)
                for username, nombre, rol, pwd in DEMO_USUARIOS:
                    _crear_usuario_si_no_existe(db, empresa.id, username, nombre, rol, pwd)
            db.commit()
            logger.info("Usuario '%s' reactivado.", admin_existente.username)
            _confirmar_demo_listo(db)
            return

        empresa = db.query(Empresa).first()
        if not empresa:
            empresa = Empresa(nombre=DEFAULT_EMPRESA)
            db.add(empresa)
            db.flush()

        dueno = Usuario(
            nombre=DEFAULT_NOMBRE,
            username=DEFAULT_USERNAME,
            password_hash=get_password_hash(DEFAULT_PASSWORD),
            rol=RolUsuario.DUENO,
            empresa_id=empresa.id,
            activo=True,
        )
        db.add(dueno)
        db.flush()
        _asegurar_almacen_principal(db, empresa.id)
        for username, nombre, rol, pwd in DEMO_USUARIOS:
            _crear_usuario_si_no_existe(db, empresa.id, username, nombre, rol, pwd)

        db.commit()
        logger.info(
            "Usuarios demo creados (dueno, vendedor, cobrador) — empresa '%s'.",
            empresa.nombre,
        )
        _confirmar_demo_listo(db)
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
