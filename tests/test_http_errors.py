"""Mapeo IntegrityError / PocketBase a HTTP 4xx/503."""
from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.core.http_errors import _mensaje_desde_integrity


def test_integrity_unique_es_409():
    exc = IntegrityError("stmt", {}, Exception("UNIQUE constraint failed"))
    status, detail = _mensaje_desde_integrity(exc)
    assert status == 409
    assert "única" in detail.lower() or "existe" in detail.lower()
