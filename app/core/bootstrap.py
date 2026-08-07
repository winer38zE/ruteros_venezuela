import logging
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.core import Usuario, Empresa, RolUsuario, Almacen
from app.api.auth import get_password_hash

logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "dueno"
DEFAULT_PASSWORD = "123456"
DEFAULT_NOMBRE = "Administrador ED NET PRO"
DEFAULT_EMPRESA = "ED NET PRO"

DEMO_USUARIOS = [
    ("vendedor", "Vendedor Demo", RolUsuario.VENDEDOR, "123456"),
    ("cobrador", "Cobrador Demo", RolUsuario.COBRADOR, "123456"),
]


def _crear_usuario_si_no_existe(
    db: Session,
    empresa_id,
    username: str,
    nombre: str,
    rol: RolUsuario,
    password: str,
) -> None:
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


def _asegurar_almacen_principal(db: Session, empresa_id) -> None:
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


def asegurar_usuario_admin() -> None:
    """Crea empresa y usuario dueño si la base de datos no tiene usuarios activos."""
    db: Session = SessionLocal()
    try:
        existe_activo = (
            db.query(Usuario)
            .filter(Usuario.activo.is_(True))
            .first()
        )
        if existe_activo:
            empresa = db.query(Empresa).first()
            if empresa:
                _asegurar_almacen_principal(db, empresa.id)
                for username, nombre, rol, pwd in DEMO_USUARIOS:
                    _crear_usuario_si_no_existe(db, empresa.id, username, nombre, rol, pwd)
                db.commit()
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
    except Exception:
        db.rollback()
        logger.exception("Error al crear usuario administrador por defecto.")
    finally:
        db.close()
