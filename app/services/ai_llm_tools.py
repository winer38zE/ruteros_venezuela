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
                    "apellido": {"type": "string", "description": "Apellido del cliente"},
                    "direccion": {"type": "string", "description": "Dirección de domicilio"},
                    "whatsapp": {
                        "type": "string",
                        "description": "WhatsApp con código de país, por ejemplo +58...",
                    },
                    "identificacion": {
                        "type": "string",
                        "description": "Cédula solo si el formulario o el país la exigen",
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
            "name": "consultar_ventas_del_dia",
            "description": "Total vendido hoy (USD) y cantidad de ventas.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_clientes_deuda",
            "description": (
                "Lista clientes con saldo pendiente de cobro (cartera). "
                "Opcional nombre_cliente para filtrar."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre_cliente": {
                        "type": "string",
                        "description": "Opcional; filtra por nombre",
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "solicitar_reporte",
            "description": (
                "Solicita un reporte operativo (n8n lo envía al dueño por WhatsApp o correo). "
                "No indiques destino ni número."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "tipo": {
                        "type": "string",
                        "enum": ["ventas_hoy", "cobros_hoy", "inventario_bajo"],
                    },
                    "canal": {
                        "type": "string",
                        "enum": ["whatsapp", "correo"],
                    },
                },
                "required": ["tipo", "canal"],
            },
        },
    },
]

def _aplicar_campos_de_formulario() -> None:
    """Venta y cobro exigen en la herramienta las mismas claves que el formulario."""
    from app.services.esquema_formulario import claves_obligatorias, pregunta_del_campo

    for tool in HERRAMIENTAS_OPENAI:
        nombre = tool["function"]["name"]
        params = tool["function"]["parameters"]
        if nombre in ("crear_pedido", "registrar_cobro"):
            params["required"] = list(claves_obligatorias(nombre))
        if nombre != "registrar_cliente":
            continue
        props = params["properties"]
        for clave in claves_obligatorias(nombre):
            props.setdefault(
                clave,
                {"type": "string", "description": pregunta_del_campo(nombre, clave)},
            )


_aplicar_campos_de_formulario()

HERRAMIENTAS_VOZ_TODAS: frozenset[str] = frozenset(
    t["function"]["name"] for t in HERRAMIENTAS_OPENAI
)

MENSAJE_PERMISO_ROL = "Eso no está disponible para tu rol."

MENSAJE_CONFUSION_VOZ = (
    "No entendí bien. ¿Quieres registrar un cliente, una venta, un cobro o consultar inventario?"
)

_HERRAMIENTAS_OPERATIVAS = frozenset(
    t["function"]["name"]
    for t in HERRAMIENTAS_OPENAI
    if t["function"]["name"] != "solicitar_reporte"
)

HERRAMIENTAS_VOZ_DUENO: frozenset[str] = _HERRAMIENTAS_OPERATIVAS | frozenset({"solicitar_reporte"})

HERRAMIENTAS_VOZ_VENDEDOR: frozenset[str] = frozenset(
    {
        "crear_pedido",
        "registrar_cliente",
        "consultar_ventas_del_dia",
    }
)

HERRAMIENTAS_VOZ_COBRADOR: frozenset[str] = frozenset(
    {
        "registrar_cobro",
        "consultar_clientes_deuda",
    }
)

HERRAMIENTAS_VOZ_ADMINISTRADOR: frozenset[str] = frozenset(
    {
        "registrar_producto_inventario",
        "consultar_inventario",
        "consultar_ventas_del_dia",
    }
)

_MAPA_HERRAMIENTAS_POR_ROL: dict[Any, frozenset[str]] = {}


def _mapa_herramientas_por_rol() -> dict[Any, frozenset[str]]:
    from app.models.core import RolUsuario

    global _MAPA_HERRAMIENTAS_POR_ROL
    if not _MAPA_HERRAMIENTAS_POR_ROL:
        _MAPA_HERRAMIENTAS_POR_ROL = {
            RolUsuario.DUENO: HERRAMIENTAS_VOZ_DUENO,
            RolUsuario.VENDEDOR: HERRAMIENTAS_VOZ_VENDEDOR,
            RolUsuario.COBRADOR: HERRAMIENTAS_VOZ_COBRADOR,
            RolUsuario.ADMINISTRADOR: HERRAMIENTAS_VOZ_ADMINISTRADOR,
        }
    return _MAPA_HERRAMIENTAS_POR_ROL


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
    r = _normalizar_rol(rol)
    if r is None:
        return frozenset()
    return _mapa_herramientas_por_rol().get(r, frozenset())


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
    return MENSAJE_PERMISO_ROL


_GUIA_INTENCIONES = (
    ("registrar_cliente", "registrar un cliente", ("agrega un cliente", "agregar un cliente", "nuevo cliente", "cliente nuevo")),
    ("crear_pedido", "registrar una venta", ("le vendi", "vendi", "compro", "pedido", "vender", "venta")),
    ("registrar_cobro", "registrar un cobro", ("me pago", "cobre", "abono", "cobro", "cobrar", "pago de")),
    ("consultar_inventario", "consultar el inventario", ("cuanto hay de", "me queda", "tengo en inventario")),
    ("solicitar_reporte", "enviarte el reporte", ("enviame el reporte", "envia el reporte", "mandame el reporte")),
)


def _fold_intencion(texto: str) -> str:
    import unicodedata

    plano = unicodedata.normalize("NFKD", (texto or "").casefold())
    return "".join(c for c in plano if not unicodedata.combining(c))


def intenciones_detectadas(texto: str) -> list[tuple[str, str]]:
    """Intenciones cuyas palabras clave aparecen en la frase, sin inventar datos."""
    t = _fold_intencion(texto)
    if "registrar" in t and "cliente" in t:
        encontradas = [("registrar_cliente", "registrar un cliente")]
    else:
        encontradas = []
    for herramienta, etiqueta, frases in _GUIA_INTENCIONES:
        if any(frase in t for frase in frases) and herramienta not in {h for h, _ in encontradas}:
            encontradas.append((herramienta, etiqueta))
    return encontradas


def intencion_de_flujo(texto: str) -> str | None:
    """Una sola intención de alta (cliente, venta o cobro). Si hay dos, no elige."""
    flujos = [
        h
        for h, _ in intenciones_detectadas(texto)
        if h in ("registrar_cliente", "crear_pedido", "registrar_cobro")
    ]
    if len(flujos) == 1:
        return flujos[0]
    return None


def mensaje_si_ambiguo(texto: str) -> str | None:
    hits = intenciones_detectadas(texto)
    if len(hits) >= 2:
        return f"Puede ser {hits[0][1]} o {hits[1][1]}. ¿Cuál de las dos?"
    if len(hits) == 1 and hits[0][0] == "consultar_inventario":
        return "¿De qué producto quieres saber cuánto hay?"
    if len(hits) == 1 and hits[0][0] == "solicitar_reporte":
        return "¿Te envío el reporte de ventas, de cobros o de inventario?"
    return None


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
- consultar_ventas_del_dia: total vendido hoy.
- consultar_clientes_deuda: clientes con saldo pendiente (cobradores).
- solicitar_reporte: reporte ventas_hoy, cobros_hoy o inventario_bajo por whatsapp o correo (solo dueño).

Guía de intenciones (obedece estas palabras; no inventes la que no esté):
- "vendí", "le vendí", "compró" → crear_pedido (registrar venta).
- "cobré", "me pagó", "abonó" → registrar_cobro.
- "cuánto hay de", "me queda", "tengo en inventario" → consultar_inventario.
- "agrega un cliente", "nuevo cliente" → registrar_cliente.
- "envíame el reporte" → solicitar_reporte.

Ejemplos:
- "Registra un gasto de 50 dólares en combustible" → registrar_gasto.
- "¿Cuánto stock queda de sábanas?" → consultar_inventario.
- "Crea un proveedor que se llama Distribuidora XYZ" → registrar_proveedor.
- "¿Cuánto vendí hoy?" → consultar_ventas_del_dia.
- "Le vendí 2 sábanas a Ana" → crear_pedido.
- "Me pagó 10 dólares" → registrar_cobro.

Registro de cliente (MUY IMPORTANTE):
- Si el historial muestra registro de cliente en curso, pide SOLO el dato faltante.
- Dígitos solos (04141234567) suelen ser teléfono pendiente con el nombre del historial.

Reglas generales:
- Extrae cantidades explícitas; si falta cantidad en pedido usa 1.
- Normaliza teléfonos a dígitos.
- No inventes montos, productos ni nombres no dichos.
- Respeta INVENTARIO DEL NEGOCIO: en crear_pedido solo productos listados.
- Si hay CONTEXTO DE CONVERSACIÓN o historial, úsalo.
- Si la frase encaja con dos intenciones, NO digas que no entiendes: ofrece esas dos opciones y espera la elección.
- Si falta un dato (cliente, producto, monto, teléfono), pídelo. Nunca inventes montos, nombres ni productos.
- Si no reconoces ninguna intención, responde exactamente:
  «{MENSAJE_CONFUSION_VOZ}» SIN llamar herramientas.
- Las acciones sensibles se confirman en un segundo audio (sí/no); no pidas confirmación en texto libre.
- Nómina no se gestiona por voz.
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
