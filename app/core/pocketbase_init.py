"""Arranque: autenticación admin, colecciones y datos demo en PocketBase."""
from __future__ import annotations

import logging
import os

from pocketbase.errors import ClientResponseError

from app.core.bootstrap import asegurar_usuario_admin
from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
from app.core.pb_schema import asegurar_colecciones, verificar_colecciones_completas

logger = logging.getLogger(__name__)


def _credenciales_desde_entorno() -> tuple[str, str, str]:
    url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/")
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password:
        raise RuntimeError(
            "ADMIN_EMAIL y ADMIN_PASSWORD deben definirse con os.getenv en el entorno del servidor."
        )
    return url, email, password


def preparar_pocketbase_al_arranque() -> None:
    """
    Orden estricto antes de atender peticiones:

    1. Autenticación superusuario (POCKETBASE_URL, ADMIN_EMAIL, ADMIN_PASSWORD).
    2. Verificar / crear todas las colecciones Ruteros vía API admin.
    3. Confirmar que no falta ninguna colección.
    4. Bootstrap (empresa demo + dueno / vendedor / cobrador).
    """
    url, email, password = _credenciales_desde_entorno()
    pb = get_pocketbase_client(url)

    logger.info("PocketBase init paso 1/4: autenticación admin (%s).", url)
    autenticar_admin_pocketbase(pb, email=email, password=password)

    logger.info("PocketBase init paso 2/4: verificar y crear colecciones.")
    asegurar_colecciones(pb)

    logger.info("PocketBase init paso 3/4: confirmar esquema completo.")
    verificar_colecciones_completas(pb)

    logger.info("PocketBase init paso 4/4: bootstrap de empresa y usuarios demo.")
    asegurar_usuario_admin()

    logger.info(
        "PocketBase listo — usuarios demo: dueno / vendedor / cobrador (clave: 123456)."
    )


def preparar_pocketbase_al_arranque_seguro() -> None:
    """No detiene Uvicorn, pero no ejecuta bootstrap si falla auth o esquema."""
    try:
        preparar_pocketbase_al_arranque()
    except ClientResponseError as exc:
        logger.exception(
            "PocketBase respondió HTTP %s durante la inicialización; bootstrap omitido.",
            getattr(exc, "status", "?"),
        )
    except RuntimeError:
        logger.exception(
            "Inicialización PocketBase incompleta (auth, colecciones o bootstrap). "
            "Revisa POCKETBASE_URL, ADMIN_EMAIL y ADMIN_PASSWORD."
        )
    except Exception:
        logger.exception("Error inesperado al preparar PocketBase; bootstrap omitido.")
