"""Frases que nadie dijo no confirman ni cancelan; el botón Confirmar sí registra la venta."""
from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.core import RolUsuario, Usuario
from app.services.ai_product_context import ContextoProductos
from app.services.ai_voice_confirmacion import (
    MENSAJE_REPETIR_CONFIRMACION,
    guardar_pendiente_confirmacion,
    limpiar_confirmacion,
    obtener_pendiente_confirmacion,
)

_BASURA = ("Puedo ver el video", "Gracias por ver el video", "")


@pytest.fixture
def client():
    return TestClient(app)


def test_basura_no_ejecuta_ni_cancela_y_confirmar_registra_la_venta(client):
    uid = "usr0000000000009"
    limpiar_confirmacion(uid)
    usuario = Usuario(
        id=uid,
        empresa_id="emp000000000001",
        nombre="Dueño",
        username="dueno",
        rol=RolUsuario.DUENO,
        activo=True,
    )
    args = {
        "cliente_nombre": "Ana",
        "productos": [{"nombre": "almohada", "cantidad": 2}],
    }
    resumen = "Voy a registrar la venta de 2 almohadas a Ana. ¿Confirmas?"
    guardar_pendiente_confirmacion(
        uid,
        herramienta="crear_pedido",
        args=args,
        resumen=resumen,
        transcripcion_origen="vendí 2 almohadas a Ana",
    )
    db = MagicMock()
    ctx = ContextoProductos(nombres=("almohada",), total=1, consulta_ok=True)

    def override_db():
        yield db

    from app.core.db import get_db
    from app.core.deps import require_ruta_o_superior

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[require_ruta_o_superior] = lambda: usuario
    audio = b"\x00" * 512
    try:
        with (
            patch("app.api.ai.AI_ENABLED", True),
            patch("app.api.ai.obtener_contexto_productos", return_value=ctx),
            patch("app.api.ai.ejecutar_herramienta_voz") as ejecutar,
            patch("app.api.ai.registrar_orden_voz") as auditoria,
            patch("app.api.ai.sintetizar_voz_base64", return_value=None),
        ):
            for frase in _BASURA:
                with patch("app.api.ai.transcribir_audio", return_value=frase):
                    res = client.post(
                        "/api/ai/audio-comando",
                        files={"audio": ("comando.m4a", BytesIO(audio), "audio/mp4")},
                        headers={"X-Usuario-Id": uid},
                    )
                assert res.status_code == 200, res.text
                body = res.json()
                assert body["exito"] is False
                assert body["mensaje"] == MENSAJE_REPETIR_CONFIRMACION
                assert resumen not in body["mensaje"]
                assert body["detalle"]["codigo"] == "confirmacion_pendiente"
                ejecutar.assert_not_called()
                auditoria.assert_not_called()
                pendiente = obtener_pendiente_confirmacion(uid)
                assert pendiente is not None
                assert pendiente.herramienta == "crear_pedido"

            ejecutar.return_value = (
                True,
                "Venta registrada.",
                {"pedido_id": "p1"},
                (False, None),
            )
            res = client.post(
                "/api/ai/confirmacion",
                json={"accion": "confirmar"},
                headers={"X-Usuario-Id": uid},
            )
            quedo = obtener_pendiente_confirmacion(uid)
    finally:
        app.dependency_overrides.clear()
        limpiar_confirmacion(uid)

    assert res.status_code == 200, res.text
    body = res.json()
    assert body["exito"] is True
    assert body["herramienta"] == "crear_pedido"
    assert "Venta registrada" in body["mensaje"]
    ejecutar.assert_called_once()
    assert ejecutar.call_args.args[2] == "crear_pedido"
    assert ejecutar.call_args.args[3]["cliente_nombre"] == "Ana"
    assert quedo is None
