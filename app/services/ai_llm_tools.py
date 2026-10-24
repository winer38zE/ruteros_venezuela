"""Definición de herramientas (function calling) del asistente Ruteros."""
from __future__ import annotations

import json
from typing import Any

HERRAMIENTAS_OPENAI: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "crear_pedido",
            "description": (
                "Registra una venta/pedido al contado para un cliente con lista de productos."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_nombre": {"type": "string", "description": "Nombre del cliente"},
                    "telefono": {
                        "type": "string",
                        "description": "Teléfono WhatsApp del cliente (opcional si se conoce el nombre)",
                    },
                    "productos": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "nombre": {"type": "string"},
                                "cantidad": {"type": "integer", "minimum": 1},
                            },
                            "required": ["nombre", "cantidad"],
                        },
                        "minItems": 1,
                    },
                    "metodo_pago": {
                        "type": "string",
                        "enum": ["efectivo", "transferencia", "pago_movil"],
                        "description": "Default efectivo",
                    },
                },
                "required": ["cliente_nombre", "productos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_cliente",
            "description": "Alta de cliente nuevo en la ruta.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "telefono": {"type": "string"},
                    "direccion": {"type": "string"},
                    "identificacion": {
                        "type": "string",
                        "description": "Cédula/RIF; si no se menciona, omitir",
                    },
                },
                "required": ["nombre", "telefono"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_cobro",
            "description": "Abono o cobro sobre deuda pendiente de un cliente.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente_nombre": {"type": "string"},
                    "telefono": {"type": "string"},
                    "monto_usd": {"type": "number", "exclusiveMinimum": 0},
                    "metodo_pago": {
                        "type": "string",
                        "enum": [
                            "efectivo",
                            "transferencia",
                            "pago_movil",
                            "dolar",
                            "bolivar",
                        ],
                    },
                },
                "required": ["cliente_nombre", "monto_usd", "metodo_pago"],
            },
        },
    },
]

SYSTEM_PROMPT = """Eres el asistente de voz de Ruteros (ventas en ruta, Venezuela/Colombia).
Interpreta órdenes habladas en español y llama EXACTAMENTE UNA herramienta cuando la intención sea clara:
- crear_pedido: ventas con productos y cantidades.
- registrar_cliente: nuevo cliente (nombre, teléfono, dirección).
- registrar_cobro: cobro de deuda (cliente, monto en USD, método de pago).

Reglas:
- Extrae cantidades numéricas explícitas; si falta cantidad usa 1.
- Normaliza teléfonos a dígitos.
- No inventes productos ni montos no dichos.
- Si la frase no encaja en ninguna herramienta, responde brevemente pidiendo aclaración SIN llamar herramientas.
"""


def parse_tool_call(message: dict[str, Any]) -> tuple[str | None, dict[str, Any]]:
    """Devuelve (nombre_herramienta, argumentos) o (None, {})."""
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        call = tool_calls[0]
        fn = call.get("function") or {}
        name = fn.get("name")
        raw = fn.get("arguments") or "{}"
        try:
            args = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except json.JSONDecodeError:
            args = {}
        return name, args

    content = (message.get("content") or "").strip()
    if content.startswith("{"):
        try:
            data = json.loads(content)
            if isinstance(data, dict) and data.get("tool"):
                return str(data["tool"]), data.get("args") or {}
        except json.JSONDecodeError:
            pass
    return None, {}
