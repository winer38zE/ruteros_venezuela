"""Pruebas de hash y login (sin arrancar PocketBase)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.api.auth import get_password_hash, verify_password
from app.api.auth_router import LoginRequest, login
from app.models.core import RolUsuario, Usuario


def test_bootstrap_y_login_usan_mismo_hash_bcrypt():
    password = "123456"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("otra", hashed)


def test_login_ok_con_usuario_demo(monkeypatch):
    demo_hash = get_password_hash("123456")
    usuario = Usuario(
        id="abc123def456789",
        empresa_id="emp123456789012",
        nombre="Admin",
        username="dueno",
        password_hash=demo_hash,
        rol=RolUsuario.DUENO,
        activo=True,
    )

    monkeypatch.setattr(
        "app.api.auth_router._buscar_usuario_por_username",
        lambda db, u: usuario,
    )

    request = MagicMock()
    request.client.host = "127.0.0.1"
    resp = login(LoginRequest(username="  Dueno ", password="123456"), request, db=MagicMock())
    assert resp.username == "dueno"
    assert resp.id == usuario.id


def test_login_falla_con_clave_incorrecta(monkeypatch):
    demo_hash = get_password_hash("123456")
    usuario = Usuario(
        id="abc123def456789",
        empresa_id="emp123456789012",
        nombre="Admin",
        username="dueno",
        password_hash=demo_hash,
        rol=RolUsuario.DUENO,
        activo=True,
    )
    monkeypatch.setattr(
        "app.api.auth_router._buscar_usuario_por_username",
        lambda db, u: usuario,
    )

    request = MagicMock()
    request.client.host = "127.0.0.1"
    with pytest.raises(HTTPException) as exc_info:
        login(LoginRequest(username="dueno", password="000000"), request, db=MagicMock())
    assert exc_info.value.status_code == 401


def test_filter_compiler_username_lower():
    from sqlalchemy import func

    from app.core.pb_orm import filter_compiler
    from app.models.core import Usuario

    filt = filter_compiler.compile_filters(
        Usuario,
        (func.lower(Usuario.username) == "dueno", Usuario.activo.is_(True)),
    )
    assert "username:lower = 'dueno'" in filt
    assert "activo = true" in filt
