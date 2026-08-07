import logging
from sqlalchemy.orm import Session
from app.core.db import SessionLocal
from app.models.core import Usuario, Empresa, RolUsuario
from app.api.auth import get_password_hash

logger = logging.getLogger(__name__)

DEFAULT_USERNAME = "dueno"
DEFAULT_PASSWORD = "123456"
DEFAULT_NOMBRE = "Administrador ED NET PRO"
DEFAULT_EMPRESA = "ED NET PRO"


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
            return

        admin_existente = (
            db.query(Usuario)
            .filter(Usuario.username.in_(["dueno", "admin"]))
            .first()
        )
        if admin_existente:
            if not admin_existente.activo:
                admin_existente.activo = True
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
        db.commit()
        logger.info(
            "Usuario admin '%s' creado para empresa '%s'.",
            DEFAULT_USERNAME,
            empresa.nombre,
        )
    except Exception:
        db.rollback()
        logger.exception("Error al crear usuario administrador por defecto.")
    finally:
        db.close()
