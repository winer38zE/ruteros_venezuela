"""Simula guardar/leer hash en PocketBase y verificación bcrypt."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.api.auth import get_password_hash, obtener_demo_password, verify_password
from app.core.demo_hash_verificacion import verificar_hash_demo_usuario
from app.core.usuario_password_hash import CAMPO_HASH_USUARIO


def _mock_pb_con_almacen():
    almacen: dict[str, dict] = {}
    pb = MagicMock()
    coll = MagicMock()

    def get_one(rid: str):
        rec = MagicMock()
        data = almacen.get(rid, {"id": rid})
        rec.__dict__ = dict(data)
        return rec

    def update(rid: str, body: dict):
        almacen.setdefault(rid, {"id": rid})
        almacen[rid].update(body)

    coll.get_one = get_one
    coll.update = update
    pb.collection.return_value = coll
    return pb, almacen


def test_verificar_hash_demo_tras_escritura_directa():
    pb, almacen = _mock_pb_con_almacen()
    rid = "abc123def456789"
    clave = obtener_demo_password()
    almacen[rid] = {
        "id": rid,
        CAMPO_HASH_USUARIO: get_password_hash(clave),
    }
    verificar_hash_demo_usuario(pb, username="dueno", record_id=rid)
    assert verify_password(clave, almacen[rid][CAMPO_HASH_USUARIO])


def test_verificar_hash_demo_reintenta_si_falta_hash():
    pb, almacen = _mock_pb_con_almacen()
    rid = "xyz987654321abc"
    almacen[rid] = {"id": rid, "username": "dueno"}
    verificar_hash_demo_usuario(pb, username="dueno", record_id=rid)
    assert CAMPO_HASH_USUARIO in almacen[rid]
    assert verify_password(obtener_demo_password(), almacen[rid][CAMPO_HASH_USUARIO])


def test_verificar_hash_demo_falla_si_campo_ignorado():
    pb, almacen = _mock_pb_con_almacen()
    rid = "fail12345678901"

    def update_noop(_rid: str, _body: dict):
        pass

    pb.collection.return_value.update = update_noop
    almacen[rid] = {"id": rid}

    with pytest.raises(RuntimeError, match="no persistió"):
        verificar_hash_demo_usuario(pb, username="dueno", record_id=rid)
