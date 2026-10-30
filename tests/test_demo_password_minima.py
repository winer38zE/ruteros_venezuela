"""DEMO_PASSWORD corta no sincroniza usuarios demo."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.api.auth import (
    DEMO_PASSWORD_LONGITUD_MINIMA,
    demo_password_cumple_longitud_minima,
    motivo_rechazo_sync_demo_por_password,
)
from app.core.bootstrap import asegurar_usuario_admin


def test_demo_password_corta_es_rechazada(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "corta123")
    assert not demo_password_cumple_longitud_minima()
    msg = motivo_rechazo_sync_demo_por_password()
    assert msg is not None
    assert "No se sincronizan usuarios demo" in msg
    assert str(DEMO_PASSWORD_LONGITUD_MINIMA) in msg
    assert "8" in msg


def test_demo_password_de_12_o_mas_es_aceptada(monkeypatch):
    monkeypatch.setenv("DEMO_PASSWORD", "docecharsok!")
    assert len("docecharsok!") == 12
    assert demo_password_cumple_longitud_minima()
    assert motivo_rechazo_sync_demo_por_password() is None


def test_bootstrap_no_crea_demo_si_password_corta(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@test.local")
    monkeypatch.setenv("ADMIN_PASSWORD", "admin-pass")
    monkeypatch.setenv("DEMO_USERS_ENABLED", "true")
    monkeypatch.setenv("DEMO_PASSWORD", "123456")

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = MagicMock(id="emp1", pais_id="p1", activa=True, nombre="E")
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
