"""Identificadores de registro compatibles con PocketBase (15 caracteres a-z0-9)."""
from __future__ import annotations

import secrets
import string
import uuid

_ALFABETO = string.ascii_lowercase + string.digits
_LONGITUD = 15


def es_id_pocketbase(value: object) -> bool:
    if value is None:
        return False
    s = str(value)
    return len(s) == _LONGITUD and all(c in _ALFABETO for c in s)


def nuevo_id_pocketbase() -> str:
    return "".join(secrets.choice(_ALFABETO) for _ in range(_LONGITUD))


def id_pocketbase_desde_cualquiera(value: object | None) -> str:
    """Normaliza UUID u otro id externo al formato PocketBase."""
    if value is None:
        return nuevo_id_pocketbase()
    if es_id_pocketbase(value):
        return str(value)
    texto = str(value).replace("-", "").lower()
    if len(texto) >= _LONGITUD and all(c in _ALFABETO for c in texto[:_LONGITUD]):
        return texto[:_LONGITUD]
    if len(texto) >= _LONGITUD:
        return "".join(c for c in texto if c in _ALFABETO)[:_LONGITUD] or nuevo_id_pocketbase()
    return nuevo_id_pocketbase()


def id_para_payload_creacion(value: object | None) -> str | None:
    """
    Devuelve id válido para POST /records o None para que PocketBase lo genere.
    """
    if value is None:
        return None
    if es_id_pocketbase(value):
        return str(value)
    normalizado = id_pocketbase_desde_cualquiera(value)
    return normalizado if es_id_pocketbase(normalizado) else None
