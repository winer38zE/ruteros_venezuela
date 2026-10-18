import logging

from fastapi import APIRouter, Depends, HTTPException
from pocketbase.errors import ClientResponseError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.core import Pais
from app.schemas.core import PaisPublicoResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("", response_model=list[PaisPublicoResponse])
def listar_paises_activos(db: Session = Depends(get_db)):
    """
    Catálogo público para el selector de país en login (sin token de usuario).

    La lectura en PocketBase se hace con sesión admin del servidor (get_db → init perezoso),
    así Flutter nunca necesita permisos de superusuario en colecciones privadas.
    """
    try:
        filas = (
            db.query(Pais)
            .filter(Pais.activo.is_(True))
            .order_by(Pais.nombre.asc())
            .all()
        )
        return filas
    except ClientResponseError as exc:
        if exc.status in (401, 403):
            from app.core.db import autenticar_admin_pocketbase

            try:
                autenticar_admin_pocketbase(getattr(db, "pb", None))
                filas = (
                    db.query(Pais)
                    .filter(Pais.activo.is_(True))
                    .order_by(Pais.nombre.asc())
                    .all()
                )
                return filas
            except Exception:
                logger.exception("Reintento admin al listar paises falló")
        logger.exception("No se pudo leer paises en PocketBase (status=%s)", exc.status)
        raise HTTPException(
            status_code=503,
            detail="Catálogo de países no disponible. Intenta de nuevo.",
        ) from exc
    except (SQLAlchemyError, RuntimeError) as exc:
        logger.exception("Error al listar paises")
        raise HTTPException(
            status_code=503,
            detail="Catálogo de países no disponible. Intenta de nuevo.",
        ) from exc
