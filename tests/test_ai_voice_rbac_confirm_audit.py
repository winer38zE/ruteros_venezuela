"""RBAC, confirmación hablada y auditoría del asistente de voz."""
from __future__ import annotations

import time
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.core import RolUsuario, Usuario
from app.services.ai_llm_tools import (
    HERRAMIENTAS_VOZ_COBRADOR,
    HERRAMIENTAS_VOZ_DUENO,
    HERRAMIENTAS_VOZ_VENDEDOR,
    MENSAJE_PERMISO_ROL,
    herramientas_permitidas_para_rol,
    mensaje_permiso_denegado,
)
from app.services.ai_voice_confirmacion import (
    evaluar_respuesta_confirmacion,
    guardar_pendiente_confirmacion,
    limpiar_confirmacion,
    obtener_pendiente_confirmacion,
    requiere_confirmacion,
)
from app.services.ai_voice_executor import ejecutar_herramienta_voz
from app.services.ai_product_context import ContextoProductos


@pytest.fixture
def client():
    return TestClient(app)


def test_rbac_mapas_por_rol():
    assert "calcular_nomina" not in HERRAMIENTAS_VOZ_DUENO
    assert "solicitar_reporte" in HERRAMIENTAS_VOZ_DUENO
    assert herramientas_permitidas_para_rol(RolUsuario.VENDEDOR) == HERRAMIENTAS_VOZ_VENDEDOR
    assert herramientas_permitidas_para_rol(RolUsuario.COBRADOR) == HERRAMIENTAS_VOZ_COBRADOR
    assert "consultar_inventario" not in HERRAMIENTAS_VOZ_VENDEDOR
    assert mensaje_permiso_denegado(RolUsuario.VENDEDOR, "registrar_gasto") == MENSAJE_PERMISO_ROL


def test_executor_rechaza_herramienta_fuera_de_rol():
    db = MagicMock()
    vendedor = Usuario(
        id="usr0000000000001",
        empresa_id="emp000000000001",
        nombre="V",
        username="v",
        rol=RolUsuario.VENDEDOR,
        activo=True,
    )
    ok, msg, det, _ = ejecutar_herramienta_voz(
        db, vendedor, "registrar_gasto", {"monto": 10, "descripcion": "x", "categoria_gasto": "general", "metodo_pago": "efectivo"}
    )
    assert ok is False
    assert MENSAJE_PERMISO_ROL in msg
    assert det.get("codigo") == "permiso_denegado"


def test_confirmacion_si_no():
    assert evaluar_respuesta_confirmacion("sí confirmo") == "confirmar"
    assert evaluar_respuesta_confirmacion("no gracias") == "rechazar"
    assert evaluar_respuesta_confirmacion("tal vez") == "ambiguo"


def test_confirmacion_vence():
    uid = "usr-ttl-test"
    limpiar_confirmacion(uid)
    with patch("app.services.ai_voice_confirmacion._TTL_SEGUNDOS", 0.05):
        guardar_pendiente_confirmacion(
            uid,
            herramienta="registrar_gasto",
            args={"monto": 1},
            resumen="¿Confirmas?",
            transcripcion_origen="gasto",
        )
        time.sleep(0.06)
        assert obtener_pendiente_confirmacion(uid) is None
    limpiar_confirmacion(uid)


def test_acciones_sensibles_requieren_confirmacion():
    assert requiere_confirmacion("crear_pedido")
    assert requiere_confirmacion("registrar_cliente")
    assert not requiere_confirmacion("consultar_inventario")


def test_audio_comando_rechaza_herramienta_modelo_sin_permiso(client):
    db = MagicMock()
    ctx = ContextoProductos(nombres=("arroz",), total=1, consulta_ok=True)
    vendedor = Usuario(
        id="usr0000000000002",
        empresa_id="emp000000000001",
        nombre="Vendedor",
        username="vendedor",
        rol=RolUsuario.VENDEDOR,
        activo=True,
    )

    from app.core.db import get_db
    from app.core.deps import require_ruta_o_superior

    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[require_ruta_o_superior] = lambda: vendedor

    audio = b"\x00" * 512
    try:
        with (
            patch("app.api.ai.AI_ENABLED", True),
            patch("app.api.ai.obtener_contexto_productos", return_value=ctx),
            patch("app.api.ai.transcribir_audio", return_value="registrar gasto"),
            patch(
                "app.api.ai.interpretar_texto_voz",
                return_value=(
                    "registrar_gasto",
                    {"monto": 5, "descripcion": "x", "categoria_gasto": "general", "metodo_pago": "efectivo"},
                    None,
                ),
            ),
            patch("app.api.ai.preparar_ejecucion", return_value=("registrar_gasto", {}, None, True)),
            patch("app.api.ai.sintetizar_voz_base64", return_value=None),
            patch("app.api.ai.registrar_orden_voz"),
        ):
            res = client.post(
                "/api/ai/audio-comando",
                files={"audio": ("comando.m4a", BytesIO(audio), "audio/mp4")},
                headers={"X-Usuario-Id": str(vendedor.id)},
            )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()
    assert body["exito"] is False
    assert body["mensaje"] == MENSAJE_PERMISO_ROL


def test_audio_comando_pide_confirmacion_antes_de_guardar(client):
    db = MagicMock()
    ctx = ContextoProductos(nombres=("arroz",), total=1, consulta_ok=True)
    dueno = Usuario(
        id="usr0000000000003",
        empresa_id="emp000000000001",
        nombre="Dueño",
        username="dueno@test.com",
        rol=RolUsuario.DUENO,
        activo=True,
    )

    from app.core.db import get_db
    from app.core.deps import require_ruta_o_superior

    app.dependency_overrides[get_db] = lambda: (yield db)
    app.dependency_overrides[require_ruta_o_superior] = lambda: dueno

    audio = b"\x00" * 512
    try:
        with (
            patch("app.api.ai.AI_ENABLED", True),
            patch("app.api.ai.obtener_contexto_productos", return_value=ctx),
            patch("app.api.ai.transcribir_audio", return_value="registrar cliente"),
            patch(
                "app.api.ai.interpretar_texto_voz",
                return_value=(
                    "registrar_cliente",
                    {"nombre": "Ana", "telefono": "04141234567"},
                    None,
                ),
            ),
            patch(
                "app.api.ai.preparar_ejecucion",
                return_value=(
                    "registrar_cliente",
                    {"nombre": "Ana", "telefono": "04141234567"},
                    None,
                    True,
                ),
            ),
            patch("app.api.ai.sintetizar_voz_base64", return_value=None),
            patch("app.api.ai.registrar_orden_voz") as mock_audit,
        ):
            res = client.post(
                "/api/ai/audio-comando",
                files={"audio": ("comando.m4a", BytesIO(audio), "audio/mp4")},
                headers={"X-Usuario-Id": str(dueno.id)},
            )
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()
    assert body["detalle"]["codigo"] == "confirmacion_pendiente"
    assert "¿Confirmas?" in body["mensaje"]
    mock_audit.assert_called()
    assert mock_audit.call_args.kwargs.get("resultado") == "pendiente_confirmacion"
