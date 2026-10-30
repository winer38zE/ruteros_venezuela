"""DEMO_USERS_ENABLED desactiva la sincronización demo en producción."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.api.auth import demo_users_enabled, motivo_omitir_sync_usuarios_demo
from app.core.bootstrap import asegurar_usuario_admin


def test_demo_users_desactivado_por_defecto_en_produccion(monkeypatch):
    monkeypatch.delenv("DEMO_USERS_ENABLED", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEMO_PASSWORD", "clave-larga-12")
    assert demo_users_enabled() is False
    msg = motivo_omitir_sync_usuarios_demo()
    assert msg is not None
    assert "DEMO_USERS_ENABLED" in msg


def test_demo_users_se_puede_activar_en_produccion(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("DEMO_USERS_ENABLED", "true")
    monkeypatch.setenv("DEMO_PASSWORD", "clave-larga-12")
    assert demo_users_enabled() is True
    assert motivo_omitir_sync_usuarios_demo() is None


def test_demo_users_activo_fuera_de_produccion_si_no_hay_flag(monkeypatch):
    monkeypatch.delenv("DEMO_USERS_ENABLED", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("ENV", raising=False)
    monkeypatch.delenv("COOLIFY_FQDN", raising=False)
    monkeypatch.delenv("COOLIFY_URL", raising=False)
    monkeypatch.setenv("DEMO_PASSWORD", "clave-larga-12")
    assert demo_users_enabled() is True
    assert motivo_omitir_sync_usuarios_demo() is None


def test_bootstrap_no_sincroniza_si_demo_users_disabled(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test.local")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-pass")
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("DEMO_USERS_ENABLED", raising=False)
    monkeypatch.setenv("DEMO_PASSWORD", "clave-larga-12")

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock(
        id="emp1", pais_id="p1", activa=True, nombre="E"
    )
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.all.return_value = []

    with (
        patch("app.core.bootstrap.get_pocketbase_client"),
        patch("app.core.bootstrap.preparar_esquema_pocketbase"),
        patch("app.core.bootstrap.verificar_colecciones_completas"),
        patch("app.core.bootstrap.SessionLocal", return_value=db),
        patch("app.core.bootstrap.asegurar_catalogo_paises"),
        patch("app.core.bootstrap.asegurar_payroll_rules_2026"),
        patch("app.core.bootstrap.pais_por_defecto", return_value=None),
        patch("app.core.bootstrap._asegurar_almacen_principal"),
        patch("app.core.bootstrap._asegurar_usuario_demo") as sync_demo,
        patch("app.core.bootstrap.verificar_hashes_usuarios_demo") as verif,
    ):
        asegurar_usuario_admin()

    sync_demo.assert_not_called()
    verif.assert_not_called()
