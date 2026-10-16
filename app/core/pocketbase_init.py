"""Arranque: autenticación admin, colecciones y bootstrap con reintentos y segundo plano."""
from __future__ import annotations

import logging
import os
import threading
import time
from typing import TYPE_CHECKING

import httpx
from pocketbase.errors import ClientResponseError

from app.core.bootstrap import asegurar_usuario_admin
from app.core.db import get_pocketbase_client
from app.core.pb_retry import ejecutar_con_reintentos, es_error_transitorio
from app.core.pb_schema import preparar_esquema_pocketbase, verificar_colecciones_completas

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

_INIT_LOCK_PATH = os.getenv("POCKETBASE_INIT_LOCK", "/tmp/ruteros_pocketbase_init.lock")
_INIT_LOCK_TIMEOUT = float(os.getenv("POCKETBASE_INIT_LOCK_TIMEOUT", "180"))
_REINTENTO_SEGUNDO_PLANO = float(os.getenv("POCKETBASE_INIT_RETRY_SECONDS", "30"))

_estado_lock = threading.Lock()
_pb_listo = False
_worker_started = False
_stop_event: threading.Event | None = None


def pocketbase_esta_listo() -> bool:
    with _estado_lock:
        return _pb_listo


def _marcar_listo(valor: bool) -> None:
    global _pb_listo
    with _estado_lock:
        _pb_listo = valor


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
        "PocketBase listo — usuarios demo sincronizados (dueno, vendedor, cobrador). "
        "Clave demo: variable DEMO_PASSWORD."
    )


def _ciclo_init_con_reintentos() -> bool:
    try:
        ejecutar_con_reintentos(
            preparar_pocketbase_al_arranque,
            max_intentos=10,
            etiqueta="Inicialización PocketBase",
        )
        return True
    except ClientResponseError as exc:
        status = getattr(exc, "status", "?")
        if es_error_transitorio(exc):
            logger.warning("Inicialización PocketBase falló tras reintentos (HTTP %s).", status)
        else:
            logger.error(
                "Inicialización PocketBase falló (HTTP %s). Revisa credenciales admin.",
                status,
            )
        return False
    except (RuntimeError, TimeoutError, httpx.HTTPError, OSError) as exc:
        if es_error_transitorio(exc):
            logger.warning("Inicialización PocketBase falló tras reintentos (%s).", type(exc).__name__)
        else:
            logger.error("Inicialización PocketBase falló (%s).", type(exc).__name__)
        return False
    except Exception:
        logger.exception("Error inesperado al preparar PocketBase.")
        return False


def _worker_init(stop: threading.Event) -> None:
    while not stop.is_set():
        if _ciclo_init_con_reintentos():
            _marcar_listo(True)
            return
        _marcar_listo(False)
        if stop.wait(_REINTENTO_SEGUNDO_PLANO):
            return


def preparar_pocketbase_al_arranque_seguro() -> None:
    """No bloquea el arranque de Uvicorn: init en hilo daemon con reintentos."""
    global _worker_started, _stop_event
    with _estado_lock:
        if _worker_started:
            return
        _worker_started = True
        _stop_event = threading.Event()
        hilo = threading.Thread(
            target=_worker_init,
            args=(_stop_event,),
            name="pocketbase-init",
            daemon=True,
        )
        hilo.start()


def detener_init_pocketbase_en_segundo_plano() -> None:
    global _stop_event
    if _stop_event is not None:
        _stop_event.set()
