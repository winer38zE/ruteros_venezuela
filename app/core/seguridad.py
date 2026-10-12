"""Cabeceras HTTP y límite de intentos de login. No altera las reglas de negocio."""
import threading
import time

from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

_LOCK = threading.Lock()
_FALLOS: dict[str, list[float]] = {}
_VENTANA_SEGUNDOS = 600
_MAX_FALLOS = 8


class CabecerasSeguridadMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Cache-Control"] = "no-store"
        return response


def _clave_login(request: Request, username: str) -> str:
    ip = request.client.host if request.client else "sin-ip"
    return f"{ip}:{(username or '').strip().lower()}"


def _marcar(clave: str, ahora: float) -> list[float]:
    marcas = [t for t in _FALLOS.get(clave, []) if ahora - t < _VENTANA_SEGUNDOS]
    _FALLOS[clave] = marcas
    if len(_FALLOS) > 5000:
        vencidas = [k for k, v in _FALLOS.items() if not v or ahora - v[-1] >= _VENTANA_SEGUNDOS]
        for k in vencidas:
            _FALLOS.pop(k, None)
    return marcas


def exigir_cupo_login(request: Request, username: str) -> None:
    ahora = time.time()
    with _LOCK:
        marcas = _marcar(_clave_login(request, username), ahora)
        if len(marcas) >= _MAX_FALLOS:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos de ingreso. Espera unos minutos e inténtalo de nuevo.",
            )


def registrar_fallo_login(request: Request, username: str) -> None:
    ahora = time.time()
    with _LOCK:
        marcas = _marcar(_clave_login(request, username), ahora)
        marcas.append(ahora)
        _FALLOS[_clave_login(request, username)] = marcas


def limpiar_fallos_login(request: Request, username: str) -> None:
    with _LOCK:
        _FALLOS.pop(_clave_login(request, username), None)
