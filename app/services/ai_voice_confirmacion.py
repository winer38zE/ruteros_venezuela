"""Confirmación hablada de acciones sensibles (TTL 2 min, servidor)."""
from __future__ import annotations

import re
import threading
import time
import unicodedata
from dataclasses import dataclass
from typing import Any

_TTL_SEGUNDOS = 120
_LOCK = threading.Lock()
_PENDIENTES: dict[str, "_PendienteConfirmacion"] = {}

HERRAMIENTAS_CON_CONFIRMACION = frozenset(
    {
        "crear_pedido",
        "registrar_cliente",
        "registrar_cobro",
        "registrar_gasto",
        "registrar_producto_inventario",
        "registrar_proveedor",
        "crear_factura_proveedor",
        "solicitar_reporte",
    }
)


@dataclass
class _PendienteConfirmacion:
    herramienta: str
    args: dict[str, Any]
    resumen: str
    transcripcion_origen: str
    created_at: float


def requiere_confirmacion(herramienta: str | None) -> bool:
    return (herramienta or "") in HERRAMIENTAS_CON_CONFIRMACION


def _ahora() -> float:
    return time.time()


def _limpiar_vencidas() -> None:
    ahora = _ahora()
    for k in [uid for uid, p in _PENDIENTES.items() if ahora - p.created_at > _TTL_SEGUNDOS]:
        _PENDIENTES.pop(k, None)


def limpiar_confirmacion(usuario_id: str) -> None:
    with _LOCK:
        _PENDIENTES.pop(str(usuario_id), None)


def obtener_pendiente_confirmacion(usuario_id: str) -> _PendienteConfirmacion | None:
    with _LOCK:
        _limpiar_vencidas()
        p = _PENDIENTES.get(str(usuario_id))
        if p is None:
            return None
        if _ahora() - p.created_at > _TTL_SEGUNDOS:
            _PENDIENTES.pop(str(usuario_id), None)
            return None
        return p


def guardar_pendiente_confirmacion(
    usuario_id: str,
    *,
    herramienta: str,
    args: dict[str, Any],
    resumen: str,
    transcripcion_origen: str,
) -> None:
    uid = str(usuario_id)
    with _LOCK:
        _limpiar_vencidas()
        _PENDIENTES[uid] = _PendienteConfirmacion(
            herramienta=herramienta,
            args=dict(args),
            resumen=resumen.strip(),
            transcripcion_origen=(transcripcion_origen or "").strip(),
            created_at=_ahora(),
        )


def _normalizar(texto: str) -> str:
    s = (texto or "").strip().casefold()
    descompuesto = unicodedata.normalize("NFKD", s)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def evaluar_respuesta_confirmacion(transcripcion: str) -> str:
    """
    Devuelve: confirmar | rechazar | ambiguo
    """
    t = _normalizar(transcripcion)
    if not t:
        return "ambiguo"
    tokens = set(re.split(r"\s+", t))
    negativas = {
        "no",
        "nop",
        "nope",
        "cancelar",
        "cancela",
        "anula",
        "anular",
        "negativo",
    }
    positivas = {
        "si",
        "sí",
        "confirmo",
        "confirmar",
        "dale",
        "ok",
        "okay",
        "vale",
        "correcto",
        "exacto",
        "afirmativo",
        "de acuerdo",
    }
    if tokens & negativas or t.startswith("no "):
        return "rechazar"
    if tokens & positivas or "confirmo" in t or t in ("si", "sí"):
        return "confirmar"
    if re.fullmatch(r"s+i+", t):
        return "confirmar"
    return "ambiguo"


def parece_nueva_intencion_negocio(transcripcion: str) -> bool:
    baja = (transcripcion or "").lower()
    return any(
        x in baja
        for x in (
            "registrar",
            "cliente",
            "vender",
            "venta",
            "pedido",
            "cobro",
            "cobrar",
            "gasto",
            "inventario",
            "producto",
            "proveedor",
            "reporte",
            "stock",
        )
    )


def construir_resumen_confirmacion(
    db,
    usuario,
    herramienta: str,
    args: dict[str, Any],
) -> tuple[str | None, str | None]:
    """Devuelve (mensaje_para_usuario, error). error bloquea la confirmación."""
    from app.services import ai_voice_executor as ex

    h = (herramienta or "").strip()
    a = dict(args or {})

    if h == "registrar_cliente":
        nombre = str(a.get("nombre") or "").strip()
        tel = str(a.get("telefono") or "").strip()
        if not nombre or not tel:
            return None, "Faltan datos del cliente para confirmar."
        return (
            f"Voy a registrar al cliente {nombre} con teléfono {tel}. ¿Confirmas?",
            None,
        )

    if h == "registrar_cobro":
        nombre = str(a.get("cliente_nombre") or "").strip()
        monto = float(a.get("monto_usd") or 0)
        metodo = str(a.get("metodo_pago") or "efectivo")
        if monto <= 0:
            return None, "Monto de cobro inválido."
        return (
            f"Voy a registrar un cobro de {monto:.2f} dólares a {nombre} "
            f"por {metodo.replace('_', ' ')}. ¿Confirmas?",
            None,
        )

    if h == "crear_pedido":
        cliente = str(a.get("cliente_nombre") or "").strip()
        items = a.get("productos") or []
        partes = []
        for item in items:
            if not isinstance(item, dict):
                continue
            pn = str(item.get("nombre") or "").strip()
            cant = int(item.get("cantidad") or 1)
            if pn:
                partes.append(f"{cant} {pn}")
        if not partes:
            return None, "Indica productos para el pedido."
        texto_prod = ", ".join(partes)
        total_txt = ""
        try:
            total = ex.estimar_total_pedido_voz(db, usuario.empresa_id, a, usuario)
            if total is not None:
                total_txt = f" por {total:.2f} dólares"
        except Exception:
            total_txt = ""
        return (
            f"Voy a registrar una venta de {texto_prod} a {cliente}{total_txt}. ¿Confirmas?",
            None,
        )

    if h == "registrar_gasto":
        monto = float(a.get("monto") or 0)
        desc = str(a.get("descripcion") or "").strip()
        if monto <= 0:
            return None, "Monto de gasto inválido."
        return (
            f"Voy a registrar un gasto de {monto:.2f} dólares"
            f"{f' en {desc}' if desc else ''}. ¿Confirmas?",
            None,
        )

    if h == "registrar_producto_inventario":
        nombre = str(a.get("nombre") or "").strip()
        precio = float(a.get("precio_venta") or 0)
        stock = float(a.get("stock_inicial") or 0)
        return (
            f"Voy a agregar al inventario {nombre}, precio {precio:.2f} dólares, "
            f"stock inicial {stock:g}. ¿Confirmas?",
            None,
        )

    if h == "registrar_proveedor":
        nombre = str(a.get("nombre") or "").strip()
        return (f"Voy a registrar al proveedor {nombre}. ¿Confirmas?", None)

    if h == "crear_factura_proveedor":
        prov = str(a.get("proveedor_nombre") or "").strip()
        monto = float(a.get("monto") or 0)
        return (
            f"Voy a registrar una factura de {monto:.2f} dólares al proveedor {prov}. ¿Confirmas?",
            None,
        )

    if h == "solicitar_reporte":
        tipo = str(a.get("tipo") or "").strip()
        canal = str(a.get("canal") or "").strip()
        return (
            f"Voy a solicitar el reporte {tipo.replace('_', ' ')} por {canal}. ¿Confirmas?",
            None,
        )

    return (f"Voy a ejecutar {h}. ¿Confirmas?", None)
