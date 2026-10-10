"""Envío de texto e imágenes por Evolution API (WhatsApp)."""
import base64
import logging
from pathlib import Path

import httpx

from app.core.config import (
    EVOLUTION_ADMIN_PHONE,
    EVOLUTION_API_KEY,
    EVOLUTION_API_URL,
    EVOLUTION_ENABLED,
    EVOLUTION_INSTANCE,
)

logger = logging.getLogger(__name__)

_ETIQUETAS_DIA = {
    "LUNES": "Lunes",
    "MARTES": "Martes",
    "MIERCOLES": "Miércoles",
    "JUEVES": "Jueves",
    "VIERNES": "Viernes",
    "SABADO": "Sábado",
    "DOMINGO": "Domingo",
}


def normalizar_telefono(numero: str) -> str:
    """Deja el número en dígitos internacionales, sin + ni espacios."""
    digitos = "".join(ch for ch in (numero or "") if ch.isdigit())
    if digitos.startswith("00"):
        digitos = digitos[2:]
    if len(digitos) == 11 and digitos.startswith("0"):
        digitos = digitos[1:]
    if len(digitos) == 10 and digitos.startswith("4"):
        digitos = "58" + digitos
    if len(digitos) < 10 or len(digitos) > 15:
        raise ValueError(
            "Número de teléfono inválido. Use el formato internacional, por ejemplo 58412XXXXXXX."
        )
    return digitos


def formatear_resumen_rutas(resumen: dict) -> str:
    """Arma el texto del reporte diario de rutas para WhatsApp."""
    dia = _ETIQUETAS_DIA.get(str(resumen.get("dia") or ""), str(resumen.get("dia") or ""))
    fecha = resumen.get("fecha")
    lineas = [
        "*Ruteros — Resumen de rutas*",
        f"Día: {dia}",
        f"Fecha: {fecha}",
        "",
    ]
    vendedores = resumen.get("vendedores") or []
    if not vendedores:
        lineas.append("No hay rutas activas para este día.")
        return "\n".join(lineas)

    for vendedor in vendedores:
        lineas.append(f"• {vendedor['vendedor_nombre']}")
        lineas.append(
            "  {total} clientes · {visitados} visitados · {pendientes} pendientes · {no_enc} no encontrados".format(
                total=vendedor["total_clientes"],
                visitados=vendedor["visitados"],
                pendientes=vendedor["pendientes"],
                no_enc=vendedor.get("no_encontrados", 0),
            )
        )
        lineas.append(f"  Avance: {vendedor['porcentaje_avance']}%")
        lineas.append("")

    lineas.append(f"Vendedores con ruta: {len(vendedores)}")
    return "\n".join(lineas).strip()


def enviar_texto(numero: str, texto: str) -> tuple[bool, str]:
    """Envía un mensaje de texto por la instancia configurada de Evolution API."""
    if not texto or not texto.strip():
        return False, "El reporte está vacío"

    try:
        destino = normalizar_telefono(numero)
    except ValueError as exc:
        return False, str(exc)

    if not EVOLUTION_ENABLED:
        logger.info("Evolution API no configurada — no se envió el mensaje a %s", destino)
        return False, (
            "Evolution API no está configurada. Defina EVOLUTION_API_URL, "
            "EVOLUTION_API_KEY y EVOLUTION_INSTANCE en el servidor."
        )

    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    payload = {"number": destino, "text": texto.strip()}
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=20.0) as client:
            respuesta = client.post(url, json=payload, headers=headers)
        if respuesta.status_code >= 400:
            detalle = respuesta.text[:300]
            logger.warning("Evolution API respondió %s: %s", respuesta.status_code, detalle)
            return False, f"Evolution API rechazó el envío ({respuesta.status_code})"
    except httpx.HTTPError as exc:
        logger.exception("Error de red al contactar Evolution API")
        return False, f"No se pudo contactar Evolution API: {exc}"

    logger.info("Mensaje de WhatsApp enviado a %s", destino)
    return True, f"Reporte enviado por WhatsApp a {destino}"


def _mime_y_nombre(data: bytes, nombre: str | None = None) -> tuple[str, str]:
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        mime, ext = "image/png", ".png"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        mime, ext = "image/webp", ".webp"
    else:
        mime, ext = "image/jpeg", ".jpg"
    if nombre and nombre.strip():
        return mime, nombre.strip()
    return mime, f"comprobante{ext}"


def preparar_imagen_comprobante(
    ruta_imagen: str | None = None,
    imagen_base64: str | None = None,
) -> tuple[str, str, str]:
    """Lee la foto desde una ruta local o desde el base64 ya guardado.

    Devuelve (base64, mimetype, fileName) listos para sendMedia.
    """
    nombre = None
    if ruta_imagen:
        path = Path(ruta_imagen)
        if not path.is_file():
            raise ValueError("No se encontró la imagen del comprobante")
        data = path.read_bytes()
        nombre = path.name
    else:
        bruto = (imagen_base64 or "").strip()
        if not bruto:
            raise ValueError("No hay imagen del comprobante para enviar")
        if bruto.startswith("data:") and "," in bruto:
            bruto = bruto.split(",", 1)[1]
        bruto = "".join(bruto.split())
        try:
            data = base64.b64decode(bruto, validate=False)
        except Exception as exc:
            raise ValueError("La imagen del comprobante no es válida") from exc

    if not data:
        raise ValueError("La imagen del comprobante está vacía")
    if len(data) > 1_500_000:
        raise ValueError("La imagen del comprobante es demasiado grande")

    mime, nombre_archivo = _mime_y_nombre(data, nombre)
    payload = base64.b64encode(data).decode("ascii")
    return payload, mime, nombre_archivo


def armar_caption_comprobante(
    cliente: str,
    monto: str,
    referencia: str | None,
    metodo: str,
) -> str:
    """Texto que acompaña la foto: monto, cliente y referencia."""
    medio = "pago móvil" if metodo == "pago_movil" else "transferencia"
    ref = (referencia or "").strip() or "Sin referencia"
    nombre = (cliente or "").strip() or "Cliente"
    return (
        f"*Comprobante de {medio}*\n"
        f"Cliente: {nombre}\n"
        f"Monto: {monto}\n"
        f"Referencia: {ref}"
    )


def telefono_administrador(db, empresa_id) -> str:
    """Teléfono de WhatsApp del administrador: variable de entorno, dueño o admin."""
    from app.models.core import RolUsuario, Usuario

    if EVOLUTION_ADMIN_PHONE:
        return EVOLUTION_ADMIN_PHONE

    for rol in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        usuarios = (
            db.query(Usuario)
            .filter(
                Usuario.empresa_id == empresa_id,
                Usuario.rol == rol,
                Usuario.activo.is_(True),
            )
            .order_by(Usuario.fecha_creacion.asc())
            .all()
        )
        for usuario in usuarios:
            telefono = (usuario.telefono or "").strip()
            if telefono:
                return telefono

    raise ValueError(
        "El administrador no tiene teléfono de WhatsApp. "
        "Agrégalo en su usuario o define EVOLUTION_ADMIN_PHONE en el servidor."
    )


def enviar_imagen(
    numero: str,
    ruta_imagen: str | None,
    caption: str,
    imagen_base64: str | None = None,
) -> tuple[bool, str]:
    """Envía la foto del comprobante por /message/sendMedia/{instance}.

    `ruta_imagen` es la ruta del archivo en el servidor. Si la foto ya está
    guardada en la venta o el cobro, se pasa `imagen_base64` y la ruta queda vacía.
    """
    texto = (caption or "").strip()
    if not texto:
        return False, "El mensaje del comprobante está vacío"

    try:
        payload_b64, mime, nombre = preparar_imagen_comprobante(ruta_imagen, imagen_base64)
    except ValueError as exc:
        return False, str(exc)

    try:
        destino = normalizar_telefono(numero)
    except ValueError as exc:
        return False, str(exc)

    if not EVOLUTION_ENABLED:
        logger.info("Evolution API no configurada — no se envió la imagen a %s", destino)
        return False, (
            "Evolution API no está configurada. Defina EVOLUTION_API_URL, "
            "EVOLUTION_API_KEY y EVOLUTION_INSTANCE en el servidor."
        )

    url = f"{EVOLUTION_API_URL}/message/sendMedia/{EVOLUTION_INSTANCE}"
    payload = {
        "number": destino,
        "mediatype": "image",
        "mimetype": mime,
        "caption": texto,
        "media": payload_b64,
        "fileName": nombre,
    }
    headers = {"apikey": EVOLUTION_API_KEY, "Content-Type": "application/json"}

    try:
        with httpx.Client(timeout=50.0) as client:
            respuesta = client.post(url, json=payload, headers=headers)
        if respuesta.status_code >= 400:
            detalle = respuesta.text[:300]
            logger.warning("Evolution API respondió %s al enviar imagen: %s", respuesta.status_code, detalle)
            return False, f"Evolution API rechazó la imagen ({respuesta.status_code})"
    except httpx.HTTPError as exc:
        logger.exception("Error de red al enviar imagen por Evolution API")
        return False, f"No se pudo contactar Evolution API: {exc}"

    logger.info("Comprobante de WhatsApp enviado a %s (%s)", destino, nombre)
    return True, f"Comprobante enviado por WhatsApp a {destino}"


def estado_http_whatsapp(mensaje: str) -> int:
    if "no está configurada" in mensaje:
        return 503
    bajos = (
        "No hay imagen",
        "No se encontró",
        "no es válida",
        "está vacía",
        "demasiado grande",
        "teléfono",
        "mensaje del comprobante",
        "Número de teléfono",
    )
    if any(parte in mensaje for parte in bajos):
        return 400
    return 502
