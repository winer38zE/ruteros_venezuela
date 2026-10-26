from app.services.ai_llm_tools import parse_tool_call


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
