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
                    "nombre_cliente": {
                        "type": "string",
                        "description": "Alias de cliente_nombre",
                    },
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
            "description": (
                "Alta de cliente nuevo en la ruta. Puedes llamarla con datos parciales "
                "(solo nombre) mientras el backend pide el teléfono en el siguiente turno."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string", "description": "Nombre completo del cliente"},
                    "telefono": {"type": "string", "description": "Teléfono móvil (solo dígitos)"},
                    "direccion": {"type": "string", "description": "Opcional"},
                    "identificacion": {
                        "type": "string",
                        "description": "Cédula/RIF; si no se menciona, omitir",
                    },
                },
                "required": [],
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
                    "nombre_cliente": {"type": "string", "description": "Alias de cliente_nombre"},
                    "telefono": {"type": "string"},
                    "monto_usd": {"type": "number", "exclusiveMinimum": 0},
                    "monto": {"type": "number", "description": "Alias de monto_usd"},
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

SYSTEM_PROMPT = """Eres un asistente de ventas de Ruteros (ruta, Venezuela/Colombia).
Interpreta órdenes habladas en español y llama EXACTAMENTE UNA herramienta cuando la intención sea clara:
- crear_pedido: ventas con productos y cantidades.
- registrar_cliente: nuevo cliente (nombre, teléfono, dirección opcional).
- registrar_cobro: cobro de deuda (cliente, monto en USD, método de pago).

Registro de cliente (MUY IMPORTANTE):
- Si el historial muestra que ya estás registrando un cliente, NO preguntes "¿qué deseas hacer?".
- Si el usuario ya dio el nombre, NO se lo vuelvas a pedir. Pide SOLO el dato que falta (teléfono o dirección).
- Una respuesta corta con solo dígitos (ej. 04141234567) es casi siempre el teléfono pendiente: llama registrar_cliente
  con el nombre del historial + ese teléfono.
- Si ya tienes nombre y teléfono, llama registrar_cliente de inmediato (dirección opcional).
- En una sola frase puedes extraer todo: "Registrar cliente Edwuar Cárdenas teléfono 04141234567 dirección Calle 123".

Otras reglas:
- Extrae cantidades numéricas explícitas; si falta cantidad usa 1.
- Normaliza teléfonos a dígitos.
- No inventes productos ni montos no dichos.
- Si hay CONTEXTO DE CONVERSACIÓN o historial previo, úsalo; no reinicies el flujo.
- Si no hay flujo activo y la frase no encaja, responde breve pidiendo aclaración SIN llamar herramientas.
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
