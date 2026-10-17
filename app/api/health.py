"""Healthchecks para proxy / Coolify."""
from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pocketbase.errors import ClientResponseError

from app.core.config import POCKETBASE_URL
from app.core.pb_health import snapshot_estado, sondear_pocketbase
from app.core.pb_retry import es_error_transitorio
from app.core.pocketbase_init import pocketbase_esta_listo

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_liveness():
    """Responde 200 aunque PocketBase aún no esté listo (contenedor vivo)."""
    return {"status": "ok"}


@router.get("/health/ready")
def health_readiness():
    """503 si PocketBase no responde; JSON con latencia y último error."""
    estado_previo = snapshot_estado()
    try:
        estado = sondear_pocketbase(con_reintentos=True)
    except ClientResponseError as exc:
        logger.warning("Readiness: PocketBase HTTP %s.", getattr(exc, "status", "?"))
        detalle = {
            "status": "not_ready",
            "pocketbase_initialized": pocketbase_esta_listo(),
            "pocketbase_url_configured": bool(POCKETBASE_URL),
            **estado_previo,
            "ultimo_error": estado_previo.get("ultimo_error") or f"HTTP {exc.status}",
        }
        raise HTTPException(status_code=503, detail=detalle) from exc
    except Exception as exc:
        logger.warning("Readiness: probe falló (%s).", type(exc).__name__)
        detalle = {
            "status": "not_ready",
            "pocketbase_initialized": pocketbase_esta_listo(),
            "pocketbase_url_configured": bool(POCKETBASE_URL),
            **estado_previo,
            "ultimo_error": estado_previo.get("ultimo_error") or type(exc).__name__,
        }
        if not es_error_transitorio(exc):
            detalle["probe"] = "failed"
        raise HTTPException(status_code=503, detail=detalle) from exc

    return {
        "status": "ready",
        "pocketbase_initialized": pocketbase_esta_listo(),
        "pocketbase_url_configured": bool(POCKETBASE_URL),
        **estado,
    }
