from app.models.core import RolUsuario
from app.services.ai_llm_tools import (
    herramientas_permitidas_para_rol,
    mensaje_permiso_denegado,
    parse_tool_call,
)


def test_parse_tool_call_openai_format():
    msg = {
        "tool_calls": [
            {
                "function": {
                    "name": "crear_pedido",
                    "arguments": '{"cliente_nombre":"Ana","productos":[{"nombre":"Arroz","cantidad":2}]}',
                }
            }
        ]
    }
    name, args = parse_tool_call(msg)
    assert name == "crear_pedido"
    assert args["cliente_nombre"] == "Ana"
    assert args["productos"][0]["cantidad"] == 2


def test_rbac_vendedor_no_registrar_gasto():
    permitidas = herramientas_permitidas_para_rol(RolUsuario.VENDEDOR)
    assert "registrar_gasto" not in permitidas
    assert "crear_pedido" in permitidas
    assert "consultar_inventario" not in permitidas
    msg = mensaje_permiso_denegado(RolUsuario.VENDEDOR, "registrar_gasto")
    assert msg == "Eso no está disponible para tu rol."


def test_rbac_dueno_todas_herramientas():
    permitidas = herramientas_permitidas_para_rol(RolUsuario.DUENO)
    assert "calcular_nomina" not in permitidas
    assert "solicitar_reporte" in permitidas
    assert mensaje_permiso_denegado(RolUsuario.DUENO, "registrar_gasto") is None
