"""Estado y sondas de disponibilidad de PocketBase."""
from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any

from pocketbase.errors import ClientResponseError

from app.core.config import POCKETBASE_URL
from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
from app.core.pb_retry import es_error_transitorio, ejecutar_con_reintentos

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_estado: dict[str, Any] = {
    "disponible": False,
    "ultima_latencia_ms": None,
    "ultimo_exito_utc": None,
    "ultimo_error": None,
    "pocketbase_url": POCKETBASE_URL,
}


def _ahora_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def registrar_exito(latencia_ms: float) -> None:
    with _lock:
        _estado["disponible"] = True
        _estado["ultima_latencia_ms"] = round(latencia_ms, 1)
        _estado["ultimo_exito_utc"] = _ahora_iso()
        _estado["ultimo_error"] = None


def registrar_fallo(mensaje: str) -> None:
    with _lock:
        _estado["disponible"] = False
        _estado["ultimo_error"] = mensaje[:500]


def snapshot_estado() -> dict[str, Any]:
    with _lock:
        return dict(_estado)


def sondear_pocketbase(*, con_reintentos: bool = True) -> dict[str, Any]:
    """Comprueba auth admin + lectura mínima; actualiza métricas en memoria."""
    t0 = time.perf_counter()

    def _probe() -> None:
        pb = get_pocketbase_client()
        autenticar_admin_pocketbase(pb)
        pb.collection("empresas").get_list(1, 1)

    try:
        if con_reintentos:
            ejecutar_con_reintentos(_probe, max_intentos=3, etiqueta="Sonda PocketBase")
        else:
            _probe()
        lat = (time.perf_counter() - t0) * 1000.0
        registrar_exito(lat)
    except ClientResponseError as exc:
        registrar_fallo(f"HTTP {getattr(exc, 'status', '?')}: {type(exc).__name__}")
        raise
    except Exception as exc:
        if es_error_transitorio(exc):
            registrar_fallo(f"{type(exc).__name__}: transitorio")
        else:
            registrar_fallo(f"{type(exc).__name__}")
        raise

    return snapshot_estado()
