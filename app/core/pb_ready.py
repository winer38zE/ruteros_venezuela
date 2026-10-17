"""Inicialización perezosa: login y requests no dependen del init de arranque."""
from __future__ import annotations

import logging
import threading

from pocketbase.errors import ClientResponseError

from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
from app.core.pb_retry import ejecutar_con_reintentos
from app.core.pb_schema import preparar_esquema_pocketbase, verificar_colecciones_completas

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_listo_minimo = False


class PocketBaseNoDisponible(RuntimeError):
    """PocketBase no respondió tras reintentos (502/503/504 o red)."""


def _asegurar_esquema_si_falta() -> None:
    pb = get_pocketbase_client()

    def probe() -> None:
        pb.collection("usuarios").get_list(1, 1)

    try:
        ejecutar_con_reintentos(probe, max_intentos=3, etiqueta="Probe usuarios PocketBase")
        return
    except ClientResponseError as exc:
        if exc.status != 404:
            raise
    except Exception:
        raise

    logger.info("Colección usuarios ausente; preparando esquema PocketBase (lazy).")
    preparar_esquema_pocketbase(pb)
    verificar_colecciones_completas(pb)


def asegurar_pocketbase_minimo() -> None:
    """
    Sesión admin + colecciones mínimas. Idempotente y seguro entre hilos.
    El bootstrap demo sigue en el init de arranque (segundo plano).
    """
    global _listo_minimo
    if _listo_minimo:
        return
    with _lock:
        if _listo_minimo:
            return
        try:
            pb = get_pocketbase_client()
            ejecutar_con_reintentos(
                lambda: autenticar_admin_pocketbase(pb),
                max_intentos=5,
                etiqueta="Auth admin PocketBase",
            )
            _asegurar_esquema_si_falta()
            _listo_minimo = True
            logger.info("PocketBase operativo (init perezoso completado).")
        except Exception as exc:
            logger.warning("PocketBase no disponible en init perezoso (%s).", type(exc).__name__)
            raise PocketBaseNoDisponible(
                "Base de datos no disponible, intenta de nuevo"
            ) from exc


def reiniciar_estado_listo() -> None:
    """Solo para pruebas."""
    global _listo_minimo
    with _lock:
        _listo_minimo = False
