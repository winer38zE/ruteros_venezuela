"""Cliente PocketBase y sesión ORM para FastAPI."""
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from pocketbase import PocketBase

from app.core.config import ADMIN_EMAIL, ADMIN_PASSWORD, POCKETBASE_URL

logger = logging.getLogger(__name__)

_pb_client: PocketBase | None = None


def get_pocketbase_client(base_url: str | None = None) -> PocketBase:
    global _pb_client
    url = (base_url or POCKETBASE_URL).rstrip("/")
    if _pb_client is None or getattr(_pb_client, "base_url", "").rstrip("/") != url:
        _pb_client = PocketBase(url)
        logger.info("Cliente PocketBase inicializado (%s).", url)
    return _pb_client


def autenticar_admin_pocketbase(
    client: PocketBase | None = None,
    *,
    email: str | None = None,
    password: str | None = None,
) -> None:
    admin_email = (email if email is not None else ADMIN_EMAIL).strip()
    admin_password = password if password is not None else ADMIN_PASSWORD
    if not admin_email or not admin_password:
        raise RuntimeError(
            "ADMIN_EMAIL y ADMIN_PASSWORD deben estar configurados en el servidor "
            "(variables de entorno del contenedor API)."
        )

    pb = client or get_pocketbase_client()
    intentos = (
        ("_superusers", lambda: pb.collection("_superusers").auth_with_password(admin_email, admin_password)),
        ("admins (legacy)", lambda: pb.admins.auth_with_password(admin_email, admin_password)),
    )
    errores: list[str] = []
    for etiqueta, auth in intentos:
        try:
            auth()
            logger.info("Sesión admin PocketBase establecida (%s).", etiqueta)
            return
        except Exception as exc:
            errores.append(f"{etiqueta}: {exc}")

    mensaje = "; ".join(errores)
    logger.error("No se pudo autenticar admin PocketBase: %s", mensaje)
    raise RuntimeError(f"Login admin PocketBase falló: {mensaje}")


def reautenticar_admin_pocketbase(client: PocketBase | None = None) -> bool:
    """Reintenta login admin (p. ej. token expirado). Devuelve False si falla."""
    try:
        autenticar_admin_pocketbase(client)
        return True
    except Exception:
        logger.exception("Re-autenticación admin PocketBase falló.")
        return False


def get_pocketbase() -> Generator[PocketBase, None, None]:
    yield get_pocketbase_client()


PocketBaseDep = Annotated[PocketBase, Depends(get_pocketbase)]


def get_db() -> Generator:
    """Dependencia FastAPI: sesión PocketBase con API compatible SQLAlchemy."""
    from app.core.pb_orm.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
