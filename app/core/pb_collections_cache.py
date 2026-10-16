"""Caché en memoria del listado de colecciones PocketBase (reduce GET /api/collections)."""
from __future__ import annotations

import logging
import threading
import time
from typing import Any

from pocketbase import PocketBase

logger = logging.getLogger(__name__)

_TTL_SEGUNDOS = float(__import__("os").getenv("PB_COLLECTIONS_CACHE_TTL", "300"))
_lock = threading.Lock()
_cache_por_url: dict[str, tuple[float, list[Any]]] = {}


def invalidar_cache_colecciones(pb: PocketBase | None = None) -> None:
    with _lock:
        if pb is None:
            _cache_por_url.clear()
            return
        url = getattr(pb, "base_url", "").rstrip("/")
        _cache_por_url.pop(url, None)


def _url_pb(pb: PocketBase) -> str:
    return getattr(pb, "base_url", "").rstrip("/")


def _lista_en_cache(url: str) -> list[Any] | None:
    with _lock:
        entry = _cache_por_url.get(url)
        if not entry:
            return None
        ts, items = entry
        if time.monotonic() - ts > _TTL_SEGUNDOS:
            _cache_por_url.pop(url, None)
            return None
        return items


def _guardar_cache(url: str, items: list[Any]) -> None:
    with _lock:
        _cache_por_url[url] = (time.monotonic(), items)


def instalar_cache_colecciones(pb: PocketBase) -> None:
    """Parchea collections.get_full_list para reutilizar la lista durante el TTL."""
    if getattr(pb, "_ruteros_cache_colecciones", False):
        return
    servicio = pb.collections
    original = servicio.get_full_list

    def get_full_list_cached(*args: Any, **kwargs: Any) -> list[Any]:
        url = _url_pb(pb)
        cached = _lista_en_cache(url)
        if cached is not None:
            return cached
        items = original(*args, **kwargs)
        _guardar_cache(url, list(items))
        return items

    servicio.get_full_list = get_full_list_cached  # type: ignore[method-assign]
    pb._ruteros_cache_colecciones = True
    logger.debug("Caché de colecciones PocketBase activa (TTL %.0fs).", _TTL_SEGUNDOS)


def mapa_colecciones_por_nombre(pb: PocketBase) -> dict[str, Any]:
    instalar_cache_colecciones(pb)
    return {c.name: c for c in pb.collections.get_full_list()}


def ids_colecciones_por_nombre(pb: PocketBase) -> dict[str, str]:
    instalar_cache_colecciones(pb)
    return {c.name: c.id for c in pb.collections.get_full_list()}
