"""Integración ligera: POST /api/ai/audio-comando (mocks, sin PocketBase real)."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.core import RolUsuario, Usuario
from app.services.ai_product_context import ContextoProductos


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def usuario_voz():
    return Usuario(
        id="usr0000000000001",
        empresa_id="emp000000000001",
        nombre="Vendedor Test",
        username="vendedor",
        rol=RolUsuario.VENDEDOR,
        activo=True,
    )


def test_audio_comando_sin_sesion_rechazado(client):
    res = client.post("/api/ai/audio-comando")
    # Sin Bearer/X-Usuario-Id, o PocketBase caído en entorno local (503).
    assert res.status_code in (401, 403, 422, 503)


def test_audio_comando_flujo_ok(client, usuario_voz):
    db = MagicMock()
    ctx = ContextoProductos(nombres=("arroz",), total=1, consulta_ok=True)

    def override_db():
        yield db

    from app.core.db import get_db
    from app.core.deps import require_ruta_o_superior

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_ruta_o_superior] = lambda: usuario_voz

    audio = b"\x00" * 512
    try:
        with (
            patch("app.api.ai.AI_ENABLED", True),
            patch("app.api.ai.obtener_contexto_productos", return_value=ctx),
            patch("app.api.ai.transcribir_audio", return_value="registrar cliente Juan"),
            patch(
                "app.api.ai.interpretar_texto_voz",
                return_value=("registrar_cliente", {"nombre": "Juan", "telefono": "04141234567"}, None),
            ),
            patch("app.api.ai.preparar_ejecucion", return_value=("registrar_cliente", {"nombre": "Juan", "telefono": "04141234567"}, None, True)),
            patch(
                "app.api.ai.ejecutar_herramienta_voz",
                return_value=(True, "Cliente Juan registrado.", {"cliente_id": "c1"}, (False, None)),
            ),
            patch("app.api.ai.sintetizar_voz_base64", return_value=None),
        ):
            res = client.post(
                "/api/ai/audio-comando",
                files={"audio": ("comando.m4a", BytesIO(audio), "audio/mp4")},
                headers={"X-Usuario-Id": str(usuario_voz.id)},
            )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["exito"] is True
    assert "Juan" in body["mensaje"] or body["herramienta"] == "registrar_cliente"
    assert body["transcripcion"] == "registrar cliente Juan"
