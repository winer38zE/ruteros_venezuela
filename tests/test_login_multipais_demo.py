"""Login demo: 4 roles × N países (mock PocketBase, sin red)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.auth import get_password_hash, password_demo_para_username
from app.api.auth_router import login
from app.models.core import Pais, RolUsuario, Usuario
from app.schemas.core import LoginResponse, PaisPublicoResponse


def _pais(iso: str, pid: str) -> Pais:
    moneda = "VES" if iso == "VE" else "COP" if iso == "CO" else "USD"
    sim = "Bs." if iso == "VE" else "$"
    return Pais(
        id=pid,
        nombre=iso,
        codigo_iso=iso,
        moneda_principal=moneda,
        simbolo_moneda=sim,
        activo=True,
        configuracion_bancaria={},
    )


PAISES = [
    _pais("CO", "pais00000000001"),
    _pais("VE", "pais00000000002"),
    _pais("MX", "pais00000000003"),
]

ROLES = [
    ("dueno", RolUsuario.DUENO),
    ("admin", RolUsuario.ADMINISTRADOR),
    ("vendedor", RolUsuario.VENDEDOR),
    ("cobrador", RolUsuario.COBRADOR),
]


@pytest.mark.parametrize("pais", PAISES)
@pytest.mark.parametrize("username,rol", ROLES)
def test_login_demo_todos_paises(monkeypatch, pais, username, rol):
    clave = password_demo_para_username(username)
    usuario = Usuario(
        id=f"usr{username[:3]}123456789",
        empresa_id="emp123456789012",
        nombre=username,
        username=username,
        password_hash=get_password_hash(clave),
        rol=rol,
        activo=True,
        pais_id=PAISES[1].id,
    )

    h = get_password_hash(clave)
    monkeypatch.setattr(
        "app.api.auth_router._autenticar_usuario_login",
        lambda db, u, p: (usuario, 1, h) if p == clave else (None, 1, h),
    )
    monkeypatch.setattr(
        "app.api.auth_router._obtener_pais_activo",
        lambda db, pid: next(p for p in PAISES if str(p.id) == pid),
    )
    monkeypatch.setattr(
        "app.api.auth_router._emitir_token_jwt",
        lambda u, p: f"token-{p.codigo_iso}",
    )

    request = MagicMock()
    request.client.host = "127.0.0.1"

    from app.api.auth_router import LoginRequest

    resp = login(
        LoginRequest(username=username, password=clave, pais_id=str(pais.id)),
        request,
        db=MagicMock(),
    )
    assert isinstance(resp, LoginResponse)
    assert resp.access_token == f"token-{pais.codigo_iso}"
    assert resp.pais_id == str(pais.id)
    assert resp.pais.codigo_iso == pais.codigo_iso


def test_login_falla_401_solo_credenciales_invalidas(monkeypatch):
    monkeypatch.setattr(
        "app.api.auth_router._autenticar_usuario_login",
        lambda db, u, p: (None, 0, ""),
    )
    request = MagicMock()
    request.client.host = "127.0.0.1"
    from app.api.auth_router import LoginRequest

    with pytest.raises(HTTPException) as exc:
        login(
            LoginRequest(username="dueno", password="000000", pais_id=PAISES[0].id),
            request,
            db=MagicMock(),
        )
    assert exc.value.status_code == 401
    assert "incorrectos" in str(exc.value.detail).lower()


def test_pocketbase_502_no_simula_401(monkeypatch):
    from pocketbase.errors import ClientResponseError

    def _raise(_db, _u, _p):
        raise ClientResponseError("bad gateway", url="", status=502, data={})

    monkeypatch.setattr("app.api.auth_router._autenticar_usuario_login", _raise)
    request = MagicMock()
    request.client.host = "127.0.0.1"
    from app.api.auth_router import LoginRequest

    with pytest.raises(HTTPException) as exc:
        login(
            LoginRequest(username="dueno", password="123456", pais_id=PAISES[0].id),
            request,
            db=MagicMock(),
        )
    assert exc.value.status_code == 503
    assert "reintenta" in str(exc.value.detail).lower()
