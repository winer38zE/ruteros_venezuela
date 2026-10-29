"""Webhook n8n para reportes solicitados por voz (solo dueño)."""
from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_HEADER_SECRET = "X-Ruteros-Webhook-Secret"


def solicitar_reporte_n8n(
    *,
    empresa_id: str,
    usuario_id: str,
    tipo: str,
    canal: str,
    destino: str,
) -> tuple[bool, str | None]:
    url = (os.getenv("N8N_REPORT_WEBHOOK") or "").strip()
    secret = (os.getenv("N8N_REPORT_WEBHOOK_SECRET") or "").strip()
    if not url:
        return False, "Webhook de reportes no configurado en el servidor."
    if not secret:
        return False, "Firma del webhook de reportes no configurada."

    payload: dict[str, Any] = {
        "empresa_id": str(empresa_id),
        "usuario_id": str(usuario_id),
        "tipo": tipo,
        "canal": canal,
        "destino": destino,
    }
    headers = {"Content-Type": "application/json", _HEADER_SECRET: secret}
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.warning("n8n reporte HTTP %s: %s", resp.status_code, resp.text[:200])
            return False, f"El servicio de reportes respondió con error ({resp.status_code})."
        return True, None
    except Exception as exc:
        logger.exception("Fallo llamando webhook n8n reportes")
        return False, str(exc)[:200]
