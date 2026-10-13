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


def get_pocketbase_client() -> PocketBase:
    global _pb_client
    if _pb_client is None:
        _pb_client = PocketBase(POCKETBASE_URL)
        logger.info("Cliente PocketBase inicializado (%s).", POCKETBASE_URL)
    return _pb_client


def autenticar_admin_pocketbase(client: PocketBase | None = None) -> None:
    if not ADMIN_EMAIL or not ADMIN_PASSWORD:
        logger.warning(
            "ADMIN_EMAIL / ADMIN_PASSWORD no configurados; "
            "el backend no autenticará contra PocketBase."
        )
        return

    pb = client or get_pocketbase_client()
    intentos = (
        ("_superusers", lambda: pb.collection("_superusers").auth_with_password(ADMIN_EMAIL, ADMIN_PASSWORD)),
        ("admins (legacy)", lambda: pb.admins.auth_with_password(ADMIN_EMAIL, ADMIN_PASSWORD)),
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
