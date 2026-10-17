"""Reintentos ante fallos transitorios de PocketBase / red."""
from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import TypeVar

import httpx
from pocketbase.errors import ClientResponseError

logger = logging.getLogger(__name__)

T = TypeVar("T")

_TRANSIENT_HTTP = frozenset({502, 503, 504})
_ESPERAS_CRECIENTES = (0.5, 1.0, 2.0, 4.0)


def pausa_reintento(intento: int) -> float:
    """Espera creciente: 0.5s, 1s, 2s, 4s (último valor se repite)."""
    idx = min(max(intento - 1, 0), len(_ESPERAS_CRECIENTES) - 1)
    return _ESPERAS_CRECIENTES[idx]


def es_error_transitorio(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError, OSError, ConnectionError)):
        return True
    if isinstance(exc, ClientResponseError):
        return int(getattr(exc, "status", 0) or 0) in _TRANSIENT_HTTP
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in _TRANSIENT_HTTP
    return False


def ejecutar_con_reintentos(
    operacion: Callable[[], T],
    *,
    max_intentos: int = 5,
    etiqueta: str = "PocketBase",
) -> T:
    ultimo: BaseException | None = None
    for intento in range(1, max_intentos + 1):
        try:
            return operacion()
        except BaseException as exc:
            ultimo = exc
            if not es_error_transitorio(exc) or intento >= max_intentos:
                raise
            pausa = pausa_reintento(intento)
            logger.warning(
                "%s no disponible (intento %d/%d, %s); reintento en %.1fs.",
                etiqueta,
                intento,
                max_intentos,
                type(exc).__name__,
                pausa,
            )
            time.sleep(pausa)
    assert ultimo is not None
    raise ultimo
