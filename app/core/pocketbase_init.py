"""Arranque: autenticación admin, colecciones y datos demo en PocketBase."""
from __future__ import annotations

import logging

from pocketbase.errors import ClientResponseError

from app.core.bootstrap import asegurar_usuario_admin
from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
from app.core.pb_schema import asegurar_colecciones

logger = logging.getLogger(__name__)


def preparar_pocketbase_al_arranque() -> None:
    """
    Ejecutar en el lifespan de FastAPI antes de atender tráfico.

    1. Login superusuario (ADMIN_EMAIL / ADMIN_PASSWORD).
    2. Crear colecciones Ruteros si la instancia está vacía.
    3. Sembrar empresa + usuarios demo (dueno, vendedor, cobrador).
    """
    autenticar_admin_pocketbase()
    pb = get_pocketbase_client()
    asegurar_colecciones(pb)
    asegurar_usuario_admin()
    logger.info(
        "PocketBase inicializado: colecciones verificadas y usuarios demo listos "
        "(dueno / vendedor / cobrador — clave demo: 123456)."
    )


def preparar_pocketbase_al_arranque_seguro() -> None:
    """Igual que preparar_pocketbase_al_arranque pero no interrumpe el arranque de Uvicorn."""
    try:
        preparar_pocketbase_al_arranque()
    except ClientResponseError as exc:
        logger.exception(
            "PocketBase respondió con error HTTP %s durante la inicialización.",
            getattr(exc, "status", "?"),
        )
    except RuntimeError:
        logger.exception(
            "Inicialización PocketBase falló (credenciales admin o esquema). "
            "Revisa POCKETBASE_URL, ADMIN_EMAIL y ADMIN_PASSWORD."
        )
    except Exception:
        logger.exception("Error inesperado al preparar PocketBase al arrancar.")
