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

# Asistente de voz (Whisper + LLM con function calling, API compatible OpenAI).
_GROQ_OPENAI_V1 = "https://api.groq.com/openai/v1"


def _normalizar_ai_base_url(raw: str | None, *, default: str) -> str:
    url = (raw or default).strip().rstrip("/")
    if "api.groq.com" in url and "/openai/v1" not in url:
        return _GROQ_OPENAI_V1
    return url or default


AI_LLM_BASE_URL = _normalizar_ai_base_url(
    os.getenv("AI_LLM_BASE_URL"),
    default=_GROQ_OPENAI_V1,
)
AI_LLM_API_KEY = os.getenv("AI_LLM_API_KEY", os.getenv("GROQ_API_KEY", "")).strip()
# llama-3.3-70b-versatile fue retirado en Groq; usar gpt-oss-120b o llama-3.1-8b-instant.
AI_LLM_MODEL = os.getenv("AI_LLM_MODEL", "openai/gpt-oss-120b")
AI_LLM_MAX_TOKENS = max(256, int(os.getenv("AI_LLM_MAX_TOKENS", "800")))
AI_WHISPER_BASE_URL = _normalizar_ai_base_url(
    os.getenv("AI_WHISPER_BASE_URL") or os.getenv("AI_LLM_BASE_URL"),
    default=_GROQ_OPENAI_V1,
)
AI_WHISPER_API_KEY = os.getenv(
    "AI_WHISPER_API_KEY",
    os.getenv("AI_LLM_API_KEY", os.getenv("GROQ_API_KEY", "")),
).strip()
AI_WHISPER_MODEL = os.getenv("AI_WHISPER_MODEL", "whisper-large-v3")
AI_ENABLED = bool(AI_LLM_API_KEY and AI_WHISPER_API_KEY)
