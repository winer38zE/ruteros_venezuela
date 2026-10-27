"""Inventario de la empresa para Whisper y Groq (cache 5 min)."""
from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.core import Producto

logger = logging.getLogger(__name__)

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
    consulta_ok: bool = True

    @property
    def vacio(self) -> bool:
        return self.consulta_ok and self.total <= 0

    def prompt_whisper(self) -> str | None:
        if not self.consulta_ok:
            return _WHISPER_SIN_INVENTARIO
        if self.total <= 0 or not self.nombres:
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


_WHISPER_SIN_INVENTARIO = (
    "Contexto del negocio: vendedor de ruta hablando de clientes, pedidos, cobros y productos."
)


def _extraer_nombre_producto(fila: Any) -> str | None:
    """PocketBase ORM devuelve instancias Producto; SQLAlchemy clásico puede devolver str o tupla."""
    if fila is None:
        return None
    if isinstance(fila, Producto):
        texto = str(fila.nombre or "").strip()
        return texto or None
    if isinstance(fila, str):
        texto = fila.strip()
        return texto or None
    if isinstance(fila, (list, tuple)):
        if not fila:
            return None
        return _extraer_nombre_producto(fila[0])
    nombre = getattr(fila, "nombre", None)
    if nombre is not None:
        texto = str(nombre).strip()
        return texto or None
    return None


def _consultar_inventario(db: Session, empresa_id: Any) -> ContextoProductos:
    filtro = (
        Producto.empresa_id == empresa_id,
        Producto.activo.is_(True),
    )
    total = int(db.query(Producto).filter(*filtro).count())
    if total == 0:
        return ContextoProductos(nombres=(), total=0, consulta_ok=True)

    # PbQuery.with_entities() es no-op: siempre hay que leer Producto.nombre del modelo.
    productos = (
        db.query(Producto)
        .filter(*filtro)
        .order_by(Producto.nombre.asc())
        .limit(_LIMITE_NOMBRES_PROMPT)
        .all()
    )
    nombres: list[str] = []
    for fila in productos:
        nombre = _extraer_nombre_producto(fila)
        if nombre:
            nombres.append(nombre)
    return ContextoProductos(nombres=tuple(nombres), total=total, consulta_ok=True)


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

    try:
        ctx = _consultar_inventario(db, empresa_id)
    except Exception:
        logger.exception("Error leyendo inventario para asistente de voz (empresa=%s)", empresa_id)
        ctx = ContextoProductos(nombres=(), total=0, consulta_ok=False)
    with _LOCK:
        _CACHE[key] = (ahora, ctx)
    return ctx
