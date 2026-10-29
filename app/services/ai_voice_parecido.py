"""Coincidencias aproximadas de clientes y productos, aisladas por empresa y rol."""
from __future__ import annotations

import unicodedata
from difflib import SequenceMatcher
from typing import Any

from app.models.core import Cliente, Producto, RolUsuario


def _fold(texto: str) -> str:
    s = (texto or "").strip().casefold()
    descompuesto = unicodedata.normalize("NFKD", s)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def coincidencia_parecida(dicho: str, nombres: list[str]) -> str | None:
    """Devuelve un nombre del catálogo si se parece y no es exacto. None si no hay uno claro."""
    consulta = _fold(dicho)
    if len(consulta) < 3:
        return None
    unicos: list[str] = []
    vistos: set[str] = set()
    for nombre in nombres:
        limpio = (nombre or "").strip()
        clave = _fold(limpio)
        if not clave or clave in vistos:
            continue
        vistos.add(clave)
        unicos.append(limpio)
    if any(_fold(n) == consulta for n in unicos):
        return None
    contiene = [n for n in unicos if consulta in _fold(n)]
    if len(contiene) == 1:
        return contiene[0]
    if len(contiene) > 1:
        return None
    mejor: str | None = None
    mejor_ratio = 0.0
    segundo = 0.0
    for nombre in unicos:
        ratio = SequenceMatcher(None, consulta, _fold(nombre)).ratio()
        if ratio > mejor_ratio:
            segundo = mejor_ratio
            mejor_ratio = ratio
            mejor = nombre
        elif ratio > segundo:
            segundo = ratio
    if mejor and mejor_ratio >= 0.78 and mejor_ratio - segundo >= 0.05:
        return mejor
    return None


def _nombres_cliente_visibles(db, usuario) -> list[str]:
    q = db.query(Cliente).filter(Cliente.empresa_id == usuario.empresa_id)
    rol = getattr(usuario, "rol", None)
    if rol == RolUsuario.VENDEDOR:
        q = q.filter(Cliente.vendedor_id == usuario.id)
    elif rol == RolUsuario.COBRADOR:
        from app.services.ai_voice_executor import _ids_clientes_con_deuda

        ids = _ids_clientes_con_deuda(db, usuario.empresa_id)
        if not ids:
            return []
        q = q.filter(Cliente.id.in_(ids))
    try:
        filas = q.all()
    except Exception:
        return []
    nombres: list[str] = []
    for fila in filas:
        nombre = getattr(fila, "nombre", None)
        if isinstance(nombre, str) and nombre.strip():
            nombres.append(nombre.strip())
    return nombres


def _nombres_producto_visibles(db, usuario) -> list[str]:
    try:
        filas = (
            db.query(Producto)
            .filter(Producto.empresa_id == usuario.empresa_id, Producto.activo.is_(True))
            .all()
        )
    except Exception:
        return []
    nombres: list[str] = []
    for fila in filas:
        nombre = getattr(fila, "nombre", None)
        if isinstance(nombre, str) and nombre.strip():
            nombres.append(nombre.strip())
    return nombres


def sugerencia_para_args(db, usuario, herramienta: str, args: dict[str, Any]) -> dict[str, Any] | None:
    """Si un nombre se parece a uno solo del catálogo visible, propone confirmarlo."""
    if herramienta in ("crear_pedido", "registrar_cobro", "registrar_cliente"):
        campo = "nombre" if herramienta == "registrar_cliente" else "cliente_nombre"
        dicho = str(args.get(campo) or "").strip()
        match = coincidencia_parecida(dicho, _nombres_cliente_visibles(db, usuario))
        if match:
            return {
                "herramienta": herramienta,
                "campo": campo,
                "dicho": dicho,
                "valor": match,
                "args": dict(args),
            }
    if herramienta == "crear_pedido":
        catalogo = _nombres_producto_visibles(db, usuario)
        for indice, item in enumerate(args.get("productos") or []):
            if not isinstance(item, dict):
                continue
            dicho = str(item.get("nombre") or "").strip()
            match = coincidencia_parecida(dicho, catalogo)
            if match:
                return {
                    "herramienta": herramienta,
                    "campo": "producto",
                    "indice": indice,
                    "dicho": dicho,
                    "valor": match,
                    "args": dict(args),
                }
    return None


def pregunta_sugerencia(propuesta: dict[str, Any]) -> str:
    return f"¿Te refieres a {propuesta['valor']}?"
