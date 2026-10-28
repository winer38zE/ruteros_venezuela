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
    {
        "type": "function",
        "function": {
            "name": "registrar_producto_inventario",
            "description": "Alta de producto nuevo en inventario con precio y stock inicial.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "precio_venta": {"type": "number", "exclusiveMinimum": 0},
                    "stock_inicial": {"type": "number", "minimum": 0},
                    "categoria": {"type": "string", "description": "Opcional"},
                },
                "required": ["nombre", "precio_venta", "stock_inicial"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_inventario",
            "description": "Consulta stock disponible; opcionalmente filtra por nombre de producto.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_producto": {
                        "type": "string",
                        "description": "Opcional; si falta, resume el catálogo",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_gasto",
            "description": "Registra un gasto operativo (salida de caja).",
            "parameters": {
                "type": "object",
                "properties": {
                    "monto": {"type": "number", "exclusiveMinimum": 0},
                    "descripcion": {"type": "string"},
                    "categoria_gasto": {
                        "type": "string",
                        "description": "Ej. combustible, moto, servicios, general",
                    },
                    "metodo_pago": {
                        "type": "string",
                        "enum": ["efectivo", "transferencia", "pago_movil", "tarjeta", "otro"],
                    },
                },
                "required": ["monto", "descripcion", "categoria_gasto", "metodo_pago"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "registrar_proveedor",
            "description": "Alta de proveedor en el módulo de compras.",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {"type": "string"},
                    "telefono": {"type": "string"},
                    "direccion": {"type": "string", "description": "Opcional"},
                    "condicion_pago": {
                        "type": "string",
                        "description": "Ej. contado, crédito 30 días",
                    },
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "crear_factura_proveedor",
            "description": "Registra deuda/factura pendiente con un proveedor.",
            "parameters": {
                "type": "object",
                "properties": {
                    "proveedor_nombre": {"type": "string"},
                    "monto": {"type": "number", "exclusiveMinimum": 0},
                    "fecha_vencimiento": {
                        "type": "string",
                        "description": "Fecha ISO YYYY-MM-DD",
                    },
                },
                "required": ["proveedor_nombre", "monto"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calcular_nomina",
            "description": "Calcula nómina de un empleado (salario, comisiones, totales).",
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_empleado": {"type": "string"},
                    "monto": {
                        "type": "number",
                        "description": "Opcional: salario base manual en moneda local",
                    },
                    "tipo_pago": {
                        "type": "string",
                        "enum": ["salario_basico", "comision", "mixto"],
                        "description": "Default mixto",
                    },
                },
                "required": ["nombre_empleado"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_ventas_del_dia",
            "description": "Total vendido hoy (USD) y cantidad de ventas.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

HERRAMIENTAS_VOZ_TODAS: frozenset[str] = frozenset(
    t["function"]["name"] for t in HERRAMIENTAS_OPENAI
)

HERRAMIENTAS_VOZ_RUTA: frozenset[str] = frozenset(
    {
        "crear_pedido",
        "registrar_cliente",
        "registrar_cobro",
        "consultar_inventario",
    }
)

MENSAJE_CONFUSION_VOZ = (
    "No entendí bien. ¿Quieres que registre un gasto, un cliente o consultes el inventario?"
)

_ACCION_POR_HERRAMIENTA: dict[str, str] = {
    "registrar_producto_inventario": "registrar productos en inventario",
    "registrar_gasto": "registrar gastos",
    "registrar_proveedor": "crear proveedores",
    "crear_factura_proveedor": "registrar facturas de proveedor",
    "calcular_nomina": "calcular nómina",
    "consultar_ventas_del_dia": "consultar ventas del día",
    "crear_pedido": "crear pedidos",
    "registrar_cliente": "registrar clientes",
    "registrar_cobro": "registrar cobros",
    "consultar_inventario": "consultar inventario",
}


def _normalizar_rol(rol: Any) -> Any:
    from app.models.core import RolUsuario

    if isinstance(rol, RolUsuario):
        return rol
    if rol is None:
        return None
    texto = str(rol).strip().upper()
    for miembro in RolUsuario:
        if miembro.value.upper() == texto or miembro.name == texto:
            return miembro
    return None


def herramientas_permitidas_para_rol(rol: Any) -> frozenset[str]:
    from app.models.core import RolUsuario

    r = _normalizar_rol(rol)
    if r in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        return HERRAMIENTAS_VOZ_TODAS
    if r in (RolUsuario.VENDEDOR, RolUsuario.COBRADOR):
        return HERRAMIENTAS_VOZ_RUTA
    return HERRAMIENTAS_VOZ_RUTA


def herramientas_openai_para_rol(rol: Any) -> list[dict[str, Any]]:
    permitidas = herramientas_permitidas_para_rol(rol)
    return [t for t in HERRAMIENTAS_OPENAI if t["function"]["name"] in permitidas]


def etiqueta_rol_voz(rol: Any) -> str:
    from app.models.core import RolUsuario

    r = _normalizar_rol(rol)
    if r == RolUsuario.VENDEDOR:
        return "vendedor"
    if r == RolUsuario.COBRADOR:
        return "cobrador"
    if r == RolUsuario.ADMINISTRADOR:
        return "administrador"
    if r == RolUsuario.DUENO:
        return "dueño"
    return "usuario"


def mensaje_permiso_denegado(rol: Any, herramienta: str) -> str | None:
    if herramienta not in HERRAMIENTAS_VOZ_TODAS:
        return None
    if herramienta in herramientas_permitidas_para_rol(rol):
        return None
    accion = _ACCION_POR_HERRAMIENTA.get(herramienta, "realizar esa acción")
    return (
        f"Lo siento, tu rol de {etiqueta_rol_voz(rol)} no tiene permisos para {accion}. "
        "Contacta al administrador."
    )


SYSTEM_PROMPT = f"""Eres el asistente de voz de Ruteros (ruta, Venezuela/Colombia).
Interpreta órdenes en español y llama EXACTAMENTE UNA herramienta cuando la intención sea clara.

Herramientas disponibles (usa la que corresponda):
- crear_pedido: venta/pedido al contado con productos y cantidades.
- registrar_cliente: alta de cliente (nombre, teléfono, dirección opcional).
- registrar_cobro: abono sobre deuda (cliente, monto USD, método de pago).
- registrar_producto_inventario: nuevo producto (nombre, precio_venta USD, stock_inicial, categoría opcional).
- consultar_inventario: stock disponible; opcional nombre_producto ("¿cuánto stock de sábanas?").
- registrar_gasto: gasto operativo (monto, descripción, categoría, método de pago).
- registrar_proveedor: nuevo proveedor (nombre, teléfono, dirección, condición de pago).
- crear_factura_proveedor: deuda/factura con proveedor (nombre, monto USD, fecha vencimiento opcional).
- calcular_nomina: cálculo de pago de empleado (nombre_empleado, tipo_pago, monto opcional).
- consultar_ventas_del_dia: total vendido hoy.

Ejemplos:
- "Registra un gasto de 50 dólares en combustible" → registrar_gasto.
- "¿Cuánto stock queda de sábanas?" → consultar_inventario.
- "Crea un proveedor que se llama Distribuidora XYZ" → registrar_proveedor.
- "¿Cuánto vendí hoy?" → consultar_ventas_del_dia.

Registro de cliente (MUY IMPORTANTE):
- Si el historial muestra registro de cliente en curso, pide SOLO el dato faltante.
- Dígitos solos (04141234567) suelen ser teléfono pendiente con el nombre del historial.

Reglas generales:
- Extrae cantidades explícitas; si falta cantidad en pedido usa 1.
- Normaliza teléfonos a dígitos.
- No inventes montos, productos ni nombres no dichos.
- Respeta INVENTARIO DEL NEGOCIO: en crear_pedido solo productos listados.
- Si hay CONTEXTO DE CONVERSACIÓN o historial, úsalo.
- Si la intención es ambigua o no hay herramienta clara, NO inventes: responde exactamente:
  «{MENSAJE_CONFUSION_VOZ}» SIN llamar herramientas.
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
