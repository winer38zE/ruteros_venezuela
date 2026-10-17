"""Cliente httpx compartido para PocketBase (reintentos de transporte y keepalive corto)."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx
from pocketbase import PocketBase
from pocketbase.errors import ClientResponseError

from app.core.pb_retry import ejecutar_con_reintentos

logger = logging.getLogger(__name__)

_KEEPALIVE = float(os.getenv("PB_HTTP_KEEPALIVE_EXPIRY", "5"))
_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=30.0, pool=10.0)

_clientes_http: dict[str, httpx.Client] = {}


def _crear_cliente_http(base_url: str) -> httpx.Client:
    url = base_url.rstrip("/")
    transport = httpx.HTTPTransport(retries=3)
    return httpx.Client(
        base_url=url,
        transport=transport,
        timeout=_TIMEOUT,
        limits=httpx.Limits(max_keepalive_connections=8, keepalive_expiry=_KEEPALIVE),
        follow_redirects=True,
    )


def obtener_cliente_http(base_url: str) -> httpx.Client:
    url = base_url.rstrip("/")
    cliente = _clientes_http.get(url)
    if cliente is None or cliente.is_closed:
        cliente = _crear_cliente_http(url)
        _clientes_http[url] = cliente
    return cliente


def _resolver_atributo_http(pb: PocketBase) -> str | None:
    for nombre in ("http", "client", "_client", "_http"):
        if hasattr(pb, nombre):
            valor = getattr(pb, nombre)
            if isinstance(valor, httpx.Client):
                return nombre
    return None


def _envolver_send(pb: PocketBase) -> None:
    if getattr(pb, "_ruteros_send_wrapped", False):
        return
    if not hasattr(pb, "send"):
        return
    original = pb.send

    def send_con_reintentos(*args: Any, **kwargs: Any) -> Any:
        def operacion() -> Any:
            return original(*args, **kwargs)

        return ejecutar_con_reintentos(
            operacion,
            max_intentos=5,
            etiqueta="PocketBase API",
        )

    pb.send = send_con_reintentos  # type: ignore[method-assign]
    pb._ruteros_send_wrapped = True


def instalar_cliente_http_pocketbase(pb: PocketBase) -> None:
    """Reutiliza un httpx.Client con transporte robusto; respeta pb.base_url."""
    url = getattr(pb, "base_url", "").rstrip("/")
    if not url:
        return
    if getattr(pb, "_ruteros_http_instalado", False):
        return

    cliente = obtener_cliente_http(url)
    attr = _resolver_atributo_http(pb)
    if attr:
        anterior = getattr(pb, attr)
        if anterior is not cliente and isinstance(anterior, httpx.Client):
            try:
                anterior.close()
            except Exception:
                pass
        setattr(pb, attr, cliente)

    _envolver_send(pb)
    pb._ruteros_http_instalado = True
    logger.debug("Cliente HTTP PocketBase instalado (%s).", url)


def cerrar_clientes_http() -> None:
    for url, cliente in list(_clientes_http.items()):
        try:
            cliente.close()
        except Exception:
            pass
        _clientes_http.pop(url, None)


def traducir_error_http(exc: BaseException) -> ClientResponseError | None:
    if isinstance(exc, ClientResponseError):
        return exc
    if isinstance(exc, httpx.HTTPStatusError):
        return ClientResponseError(
            str(exc),
            url=str(exc.request.url),
            status=exc.response.status_code,
            data={},
        )
    return None
