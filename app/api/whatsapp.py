"""Envío del comprobante de pago por Evolution API."""
import base64
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_ruta_o_superior
from app.models.core import Usuario
from app.services.evolution_service import (
    enviar_imagen,
    estado_http_whatsapp,
    normalizar_telefono,
    telefono_administrador,
)

logger = logging.getLogger(__name__)

router = APIRouter()

_MAX_BYTES = 1_500_000


@router.post("/enviar-comprobante")
async def enviar_comprobante_whatsapp(
    telefono: str = Form("", description="Número con código de país. Vacío: WhatsApp del administrador"),
    caption: str = Form(..., description="Texto descriptivo de la venta o transferencia"),
    file: UploadFile = File(..., description="Imagen del comprobante"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_ruta_o_superior),
):
    """Recibe la foto, la convierte a Base64 y la envía por /message/sendMedia/{instance}."""
    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="La imagen del comprobante está vacía")
    if len(contents) > _MAX_BYTES:
        raise HTTPException(status_code=400, detail="La imagen del comprobante es demasiado grande")

    destino = telefono.strip()
    if not destino:
        try:
            destino = telefono_administrador(db, usuario.empresa_id)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    imagen_base64 = base64.b64encode(contents).decode("ascii")
    logger.info("Usuario %s envía comprobante por WhatsApp", usuario.id)
    ok, mensaje = enviar_imagen(destino, None, caption, imagen_base64=imagen_base64)
    if not ok:
        raise HTTPException(status_code=estado_http_whatsapp(mensaje), detail=mensaje)

    try:
        destino = normalizar_telefono(destino)
    except ValueError:
        destino = telefono

    return {
        "status": "success",
        "message": "Comprobante enviado por WhatsApp exitosamente",
        "telefono": destino,
        "mensaje": mensaje,
    }
