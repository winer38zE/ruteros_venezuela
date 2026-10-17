"""Pruebas de hash y login (sin arrancar PocketBase)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from pocketbase.errors import ClientResponseError

from app.api.auth import (
    get_password_hash,
    huella_contraseña_log,
    obtener_demo_password,
    verify_password,
)
from app.api.auth_router import LoginRequest, login
from app.core.pb_ready import PocketBaseNoDisponible
from app.core.pb_orm.ids import es_id_pocketbase, resolver_id_registro
from app.core.deps import obtener_usuario_actual
from app.models.core import RolUsuario, Usuario


def test_demo_password_hash_misma_funcion_que_verificacion():
    clave = "mi_clave_demo"
    hashed = get_password_hash(clave)
    assert verify_password(clave, hashed)
    assert not verify_password(clave + "x", hashed)


def test_obtener_demo_password_strip_entorno(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "  abcdef  ")
    assert obtener_demo_password() == "abcdef"
    monkeypatch.delenv("DEMO_PASSWORD", raising=False)
    assert obtener_demo_password() == "123456"


def test_huella_contraseña_sin_revelar_contenido():
    ln, pref = huella_contraseña_log("123456")
    assert ln == 6
    assert len(pref) == 6
    assert pref.isalnum()


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


def test_login_503_si_pocketbase_caido(monkeypatch):
    def _falla(_db, _u):
        raise ClientResponseError("bad gateway", url="", status=502, data={})

    monkeypatch.setattr("app.api.auth_router._buscar_usuario_por_username", _falla)
    request = MagicMock()
    request.client.host = "127.0.0.1"
    with pytest.raises(HTTPException) as exc_info:
        login(LoginRequest(username="dueno", password="123456"), request, db=MagicMock())
    assert exc_info.value.status_code == 503
    assert "no disponible" in str(exc_info.value.detail).lower()


def test_login_503_si_pocketbase_no_disponible(monkeypatch):
    def _raise(_db, _u):
        raise PocketBaseNoDisponible("Base de datos no disponible, intenta de nuevo")

    monkeypatch.setattr("app.api.auth_router._buscar_usuario_por_username", _raise)
    request = MagicMock()
    request.client.host = "127.0.0.1"
    with pytest.raises(HTTPException) as exc_info:
        login(LoginRequest(username="dueno", password="123456"), request, db=MagicMock())
    assert exc_info.value.status_code == 503


def test_resolver_id_pocketbase_15_chars():
    pid = "abc123def456789"
    assert es_id_pocketbase(pid)
    assert resolver_id_registro(pid) == pid


def test_obtener_usuario_acepta_id_pocketbase(monkeypatch):
    usuario = Usuario(
        id="abc123def456789",
        empresa_id="emp123456789012",
        nombre="Admin",
        username="dueno",
        password_hash="x",
        rol=RolUsuario.DUENO,
        activo=True,
    )
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = usuario
    db.query.return_value = q

    out = obtener_usuario_actual(x_usuario_id="abc123def456789", db=db)
    assert out.username == "dueno"


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
