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

# Evolution API (WhatsApp). La URL es la raíz del servidor, sin /manager ni /message.
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL", "http://178.105.48.103:8081").rstrip("/")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY", "")
EVOLUTION_INSTANCE = os.getenv("EVOLUTION_INSTANCE", "tutor-ia-personal")
EVOLUTION_ENABLED = bool(EVOLUTION_API_URL and EVOLUTION_API_KEY and EVOLUTION_INSTANCE)
