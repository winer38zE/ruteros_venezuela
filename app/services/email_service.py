"""Envío de correos vía SMTP estándar de Python."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import (
    SMTP_ENABLED,
    SMTP_FROM,
    SMTP_HOST,
    SMTP_PASSWORD,
    SMTP_PORT,
    SMTP_USE_TLS,
    SMTP_USER,
)

logger = logging.getLogger(__name__)


def enviar_correo(destinatario: str, asunto: str, cuerpo_html: str) -> tuple[bool, str]:
    if not destinatario or "@" not in destinatario:
        return False, "El cliente no tiene un correo electrónico válido"
    if not SMTP_ENABLED:
        logger.info("SMTP no configurado — correo simulado para %s: %s", destinatario, asunto)
        return True, "Correo registrado (configure SMTP_HOST en el servidor para envío real)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = asunto
    msg["From"] = SMTP_FROM
    msg["To"] = destinatario
    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as server:
            if SMTP_USE_TLS:
                server.starttls()
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, [destinatario], msg.as_string())
        logger.info("Correo enviado a %s — %s", destinatario, asunto)
        return True, f"Correo enviado a {destinatario}"
    except Exception as exc:
        logger.exception("Error enviando correo a %s", destinatario)
        return False, f"No se pudo enviar el correo: {exc}"
