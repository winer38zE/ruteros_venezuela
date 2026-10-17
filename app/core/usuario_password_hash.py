"""Campo y utilidades del hash de contraseña en usuarios (ORM ↔ PocketBase)."""
from __future__ import annotations

from app.models.core import Usuario

# Mismo nombre en SQLAlchemy y en la colección PocketBase `usuarios`.
CAMPO_HASH_USUARIO = "password_hash"


def nombre_campo_hash_escritura() -> str:
    col = Usuario.__table__.columns.get(CAMPO_HASH_USUARIO)
    if col is not None:
        return col.key
    return CAMPO_HASH_USUARIO


def nombre_campo_hash_lectura_login() -> str:
    return nombre_campo_hash_escritura()


def hash_desde_modelo_usuario(usuario: Usuario) -> str:
    raw = getattr(usuario, CAMPO_HASH_USUARIO, None)
    if raw is None:
        return ""
    return raw if isinstance(raw, str) else str(raw)


def hash_desde_payload_pocketbase(data: dict) -> str | None:
    campo = nombre_campo_hash_lectura_login()
    raw = data.get(campo)
    if raw is None or raw == "":
        return None
    return str(raw)


def prefijo_bcrypt(hash_str: str | None) -> str:
    if not hash_str:
        return ""
    return hash_str[:7] if len(hash_str) >= 7 else hash_str
