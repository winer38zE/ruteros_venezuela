"""Arranque: autenticación admin, colecciones y datos demo en PocketBase."""
from __future__ import annotations

import logging
import os
import time

from pocketbase.errors import ClientResponseError

from app.core.bootstrap import asegurar_usuario_admin
from app.core.db import get_pocketbase_client
from app.core.pb_schema import preparar_esquema_pocketbase, verificar_colecciones_completas

logger = logging.getLogger(__name__)

_INIT_LOCK_PATH = os.getenv("POCKETBASE_INIT_LOCK", "/tmp/ruteros_pocketbase_init.lock")
_INIT_LOCK_TIMEOUT = float(os.getenv("POCKETBASE_INIT_LOCK_TIMEOUT", "180"))


def _credenciales_desde_entorno() -> tuple[str, str, str]:
    url = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/")
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not email or not password:
        raise RuntimeError(
            "ADMIN_EMAIL y ADMIN_PASSWORD deben definirse con os.getenv en el entorno del servidor."
        )
    return url, email, password


class _InitLock:
    """Evita carreras cuando Uvicorn levanta varios workers (Coolify)."""

    def __init__(self) -> None:
        self._fh = None

    def __enter__(self) -> _InitLock:
        if os.name == "nt":
            return self
        import fcntl

        deadline = time.monotonic() + _INIT_LOCK_TIMEOUT
        self._fh = open(_INIT_LOCK_PATH, "a+", encoding="utf-8")
        while True:
            try:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"No se obtuvo lock de init PocketBase en {_INIT_LOCK_PATH} "
                        f"tras {_INIT_LOCK_TIMEOUT}s."
                    )
                time.sleep(0.5)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._fh is None:
            return
        if os.name != "nt":
            import fcntl

            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        self._fh.close()


def preparar_pocketbase_al_arranque() -> None:
    """
    Orden estricto:

    1. POCKETBASE_URL + credenciales admin (os.getenv).
    2. Crear/verificar colecciones vía API admin (+ probe /records).
    3. Bootstrap (empresa + usuarios demo).
    """
    url, _email, _password = _credenciales_desde_entorno()
    pb = get_pocketbase_client(url)

    with _InitLock():
        logger.info("PocketBase init paso 1/3: esquema (auth + colecciones) en %s.", url)
        preparar_esquema_pocketbase(pb)

        logger.info("PocketBase init paso 2/3: confirmación final del esquema.")
        verificar_colecciones_completas(pb)

        logger.info("PocketBase init paso 3/3: bootstrap (empresa y usuarios demo).")
        asegurar_usuario_admin()

    logger.info(
        "PocketBase listo — usuarios demo: dueno / vendedor / cobrador (clave: 123456)."
    )


def preparar_pocketbase_al_arranque_seguro() -> None:
    try:
        preparar_pocketbase_al_arranque()
    except ClientResponseError as exc:
        logger.exception(
            "PocketBase respondió HTTP %s durante la inicialización; bootstrap omitido.",
            getattr(exc, "status", "?"),
        )
    except (RuntimeError, TimeoutError):
        logger.exception(
            "Inicialización PocketBase incompleta (auth, colecciones o bootstrap). "
            "Revisa POCKETBASE_URL, ADMIN_EMAIL y ADMIN_PASSWORD."
        )
    except Exception:
        logger.exception("Error inesperado al preparar PocketBase; bootstrap omitido.")
