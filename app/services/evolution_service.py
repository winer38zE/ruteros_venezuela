"""Envío de mensajes de texto por Evolution API (WhatsApp)."""
import logging

import httpx

from app.core.config import (
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
