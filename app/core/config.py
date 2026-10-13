"""Configuración de la aplicación."""
import os

POCKETBASE_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "").strip()
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")

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
# Si está vacío, se usa el teléfono del dueño y, si no tiene, el del administrador.
EVOLUTION_ADMIN_PHONE = os.getenv("EVOLUTION_ADMIN_PHONE", "").strip()
