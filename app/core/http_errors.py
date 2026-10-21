"""Mapeo de excepciones internas a respuestas HTTP coherentes (sin filtrar secretos)."""
from __future__ import annotations

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pocketbase.errors import ClientResponseError
from sqlalchemy.exc import IntegrityError

from app.core.pb_ready import PocketBaseNoDisponible

logger = logging.getLogger(__name__)


def _mensaje_desde_integrity(exc: IntegrityError) -> tuple[int, str]:
    orig = getattr(exc, "orig", exc)
    texto = str(orig) if orig else str(exc)
    if isinstance(orig, ClientResponseError):
        status = int(getattr(orig, "status", 0) or 0)
        if status in (502, 503, 504):
            return 503, "Base de datos no disponible, intenta de nuevo"
        if status == 404:
            return 503, "Esquema de base de datos incompleto, contacta soporte"
        data = getattr(orig, "data", None) or {}
        if isinstance(data, dict):
            msg = data.get("message") or data.get("data", {})
            if isinstance(msg, dict):
                msg = msg.get("message") or str(msg)
            if msg:
                texto = str(msg)
    lower = texto.lower()
    if "unique" in lower or "already exists" in lower or "duplicate" in lower:
        return 409, "El registro ya existe o viola una restricción única"
    if "validation" in lower or "invalid" in lower or "required" in lower:
        return 400, "Datos inválidos para guardar en la base de datos"
    if len(texto) > 280:
        texto = texto[:280] + "…"
    return 400, texto or "No se pudo guardar el registro"


def _mensaje_runtime(exc: RuntimeError) -> tuple[int, str]:
    texto = str(exc)
    if "colección" in texto.lower() or "collection" in texto.lower():
        logger.error("RuntimeError esquema PocketBase: %s", texto)
        return 503, "Base de datos no disponible, intenta de nuevo"
    logger.exception("RuntimeError no esperado")
    return 500, "Error interno del servidor"


def registrar_manejadores_excepciones(app: FastAPI) -> None:
    @app.exception_handler(PocketBaseNoDisponible)
    async def _pb_no_disponible(_request: Request, exc: PocketBaseNoDisponible) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(IntegrityError)
    async def _integrity(_request: Request, exc: IntegrityError) -> JSONResponse:
        logger.warning("IntegrityError en request %s", _request.url.path, exc_info=exc)
        status, detail = _mensaje_desde_integrity(exc)
        return JSONResponse(status_code=status, content={"detail": detail})

    @app.exception_handler(ClientResponseError)
    async def _client_response(_request: Request, exc: ClientResponseError) -> JSONResponse:
        status_pb = int(getattr(exc, "status", 0) or 0)
        logger.warning(
            "ClientResponseError PocketBase HTTP %s en %s",
            status_pb,
            _request.url.path,
            exc_info=exc,
        )
        if status_pb in (401, 403):
            return JSONResponse(status_code=503, content={"detail": "Servidor no disponible, reintenta"})
        if status_pb in (502, 503, 504, 404):
            return JSONResponse(
                status_code=503,
                content={"detail": "Base de datos no disponible, intenta de nuevo"},
            )
        data = getattr(exc, "data", None)
        detail = "No se pudo completar la operación"
        if isinstance(data, dict):
            detail = str(data.get("message") or detail)
        return JSONResponse(status_code=400, content={"detail": detail})

    @app.exception_handler(RuntimeError)
    async def _runtime(_request: Request, exc: RuntimeError) -> JSONResponse:
        status, detail = _mensaje_runtime(exc)
        return JSONResponse(status_code=status, content={"detail": detail})
