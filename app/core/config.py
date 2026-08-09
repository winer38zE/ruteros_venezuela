"""Configuración de la aplicación."""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ruteros_local.db")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER or "noreply@ruteros.local")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes")
SMTP_ENABLED = bool(SMTP_HOST and SMTP_FROM)
