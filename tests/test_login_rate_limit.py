"""Bloqueo temporal de login: 5 fallos por usuario e IP."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.core import seguridad
from app.core.seguridad import (
    cuenta_bloqueada_login,
    exigir_cupo_login,
    limpiar_fallos_login,
    registrar_fallo_login,
)


def _request(ip: str = "10.0.0.8") -> MagicMock:
    req = MagicMock()
    req.client.host = ip
    return req


@pytest.fixture(autouse=True)
def _limpiar_fallos():
    with seguridad._LOCK:
        seguridad._FALLOS.clear()
    yield
    with seguridad._LOCK:
        seguridad._FALLOS.clear()


def test_quinto_fallo_bloquea_misma_ip_y_usuario():
    req = _request("1.1.1.1")
    for _ in range(5):
        assert not cuenta_bloqueada_login(req, "dueno")
        registrar_fallo_login(req, "dueno")
    assert cuenta_bloqueada_login(req, "dueno")
    with pytest.raises(HTTPException) as exc:
        exigir_cupo_login(req, "dueno")
    assert exc.value.status_code == 429


def test_otra_ip_o_otro_usuario_no_comparten_bloqueo():
    req_a = _request("1.1.1.1")
    req_b = _request("2.2.2.2")
    for _ in range(5):
        registrar_fallo_login(req_a, "dueno")
    assert cuenta_bloqueada_login(req_a, "dueno")
    assert not cuenta_bloqueada_login(req_b, "dueno")
    assert not cuenta_bloqueada_login(req_a, "vendedor")


def test_login_exitoso_limpia_fallos():
    req = _request()
    for _ in range(4):
        registrar_fallo_login(req, "cobrador")
    limpiar_fallos_login(req, "cobrador")
    assert not cuenta_bloqueada_login(req, "cobrador")
