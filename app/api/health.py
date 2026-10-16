"""Healthchecks para proxy / Coolify."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pocketbase.errors import ClientResponseError

from app.core.config import POCKETBASE_URL
from app.core.db import get_pocketbase_client
from app.core.pocketbase_init import pocketbase_esta_listo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_liveness():
    """Responde 200 aunque PocketBase aún no esté listo (contenedor vivo)."""
    return {"status": "ok"}


@router.get("/health/ready")
def health_readiness():
    """503 hasta que la inicialización PocketBase (esquema + bootstrap) haya terminado."""
    if not pocketbase_esta_listo():
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "pocketbase_initialized": False},
        )
    try:
        pb = get_pocketbase_client()
        pb.collection("empresas").get_list(1, 1)
    except ClientResponseError as exc:
        logger.warning("Readiness: PocketBase respondió HTTP %s.", getattr(exc, "status", "?"))
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "pocketbase_initialized": True, "probe": "failed"},
        ) from exc
    except Exception as exc:
        logger.warning("Readiness: probe PocketBase falló (%s).", type(exc).__name__)
        raise HTTPException(
            status_code=503,
            detail={"status": "not_ready", "pocketbase_initialized": True, "probe": "failed"},
        ) from exc
    return {
        "status": "ready",
        "pocketbase_initialized": True,
        "pocketbase_url_configured": bool(POCKETBASE_URL),
    }
