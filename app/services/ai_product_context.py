"""Inventario de la empresa para Whisper y Groq (cache 5 min)."""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.core import Producto

MENSAJE_INVENTARIO_VACIO = (
    "El inventario está vacío. Por favor, agregue productos primero antes de usar el asistente de voz."
)

_LIMITE_NOMBRES_PROMPT = 30
_CACHE_TTL_SEG = 300
_LOCK = threading.Lock()
_CACHE: dict[str, tuple[float, "ContextoProductos"]] = {}


@dataclass(frozen=True)
class ContextoProductos:
    """Nombres de producto activos de la empresa (muestra + total en catálogo)."""

    nombres: tuple[str, ...]
    total: int

    @property
    def vacio(self) -> bool:
        return self.total <= 0

    def prompt_whisper(self) -> str | None:
        if self.vacio or not self.nombres:
            return None
        items = ", ".join(self.nombres)
        return (
            "Contexto del negocio: vendedor de ruta hablando de clientes, pedidos, cobros y productos. "
            f"Productos como {items}."
        )

    def bloque_inventario_llm(self) -> str:
        if self.vacio:
            return ""
        items = ", ".join(self.nombres)
        muestra = ""
        if self.total > len(self.nombres):
            muestra = f" (mostrando {len(self.nombres)} de {self.total} productos)"
        return (
            f"INVENTARIO DEL NEGOCIO{muestra}:\n"
            f"El negocio vende: {items}.\n"
            "Si el usuario pide vender o incluir en un pedido un producto que NO está en esta lista "
            "(ni es claramente el mismo artículo), responde SIN llamar herramientas: "
            "«Producto no encontrado en el inventario».\n"
            "Alta de producto por voz: si piden registrar o agregar un producto nuevo, pide el nombre "
            "(si falta), precio en USD y cantidad en stock; al tenerlos, indica que debe confirmarlo "
            "en la app móvil (aún no se guarda automáticamente por voz)."
        )


def _empresa_key(empresa_id: Any) -> str:
    return str(empresa_id)


def _consultar_inventario(db: Session, empresa_id: Any) -> ContextoProductos:
    base = db.query(Producto).filter(
        Producto.empresa_id == empresa_id,
        Producto.activo.is_(True),
    )
    total = base.count()
    if total == 0:
        return ContextoProductos(nombres=(), total=0)

    filas = (
        base.with_entities(Producto.nombre)
        .order_by(Producto.nombre.asc())
        .limit(_LIMITE_NOMBRES_PROMPT)
        .all()
    )
    nombres = tuple(n.strip() for (n,) in filas if n and str(n).strip())
    return ContextoProductos(nombres=nombres, total=total)


def invalidar_cache_inventario(empresa_id: Any) -> None:
    """Útil tras crear/editar productos (opcional)."""
    key = _empresa_key(empresa_id)
    with _LOCK:
        _CACHE.pop(key, None)


def obtener_contexto_productos(db: Session, empresa_id: Any) -> ContextoProductos:
    """Lista de productos con cache TTL 5 min por empresa."""
    key = _empresa_key(empresa_id)
    ahora = time.time()
    with _LOCK:
        hit = _CACHE.get(key)
        if hit and ahora - hit[0] < _CACHE_TTL_SEG:
            return hit[1]

    ctx = _consultar_inventario(db, empresa_id)
    with _LOCK:
        _CACHE[key] = (ahora, ctx)
    return ctx
