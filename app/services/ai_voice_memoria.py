"""Memoria persistente de voz (apodos clientes/productos, vocabulario Whisper)."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.pb_orm.ids import nuevo_id_pocketbase
from app.services.ai_voice_models import MemoriaVoz

logger = logging.getLogger(__name__)

_LIMITE_APODOS = 40
_LIMITE_WHISPER_CHARS = 800


def _lista_apodos(raw: Any) -> list[str]:
    if raw is None or isinstance(raw, (bool, int, float)):
        return []
    if not isinstance(raw, (list, dict, str)):
        return []
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, dict):
        out: list[str] = []
        for k, v in raw.items():
            k = str(k).strip()
            v = str(v).strip()
            if k and v:
                out.append(f"{k}={v}")
            elif k:
                out.append(k)
        return out
    return [str(raw).strip()] if str(raw).strip() else []


def obtener_o_crear_memoria(db: Session, empresa_id, usuario_id) -> MemoriaVoz:
    fila = (
        db.query(MemoriaVoz)
        .filter(
            MemoriaVoz.empresa_id == empresa_id,
            MemoriaVoz.usuario_id == usuario_id,
        )
        .first()
    )
    if isinstance(fila, MemoriaVoz):
        return fila
    fila = MemoriaVoz(
        id=nuevo_id_pocketbase(),
        empresa_id=empresa_id,
        usuario_id=usuario_id,
        apodos_clientes=[],
        apodos_productos=[],
        vocabulario_whisper="",
        updated_at=datetime.utcnow(),
    )
    db.add(fila)
    db.flush()
    return fila


def bloque_memoria_llm(db: Session, empresa_id, usuario_id) -> str:
    try:
        mem = obtener_o_crear_memoria(db, empresa_id, usuario_id)
    except Exception:
        logger.debug("memoria_voz no disponible para LLM", exc_info=True)
        return ""
    clientes = _lista_apodos(mem.apodos_clientes)[:_LIMITE_APODOS]
    productos = _lista_apodos(mem.apodos_productos)[:_LIMITE_APODOS]
    if not clientes and not productos:
        return ""
    partes = ["MEMORIA DE VOZ (apodos confirmados — úsalos al interpretar):"]
    if clientes:
        partes.append(f"- Clientes: {', '.join(clientes)}.")
    if productos:
        partes.append(f"- Productos: {', '.join(productos)}.")
    return "\n".join(partes)


def prompt_whisper_memoria(db: Session, empresa_id, usuario_id) -> str | None:
    try:
        mem = obtener_o_crear_memoria(db, empresa_id, usuario_id)
    except Exception:
        logger.debug("memoria_voz no disponible para Whisper", exc_info=True)
        return None
    clientes = _lista_apodos(mem.apodos_clientes)
    productos = _lista_apodos(mem.apodos_productos)
    extra_raw = mem.vocabulario_whisper
    extra = str(extra_raw).strip() if isinstance(extra_raw, str) else ""
    trozos = [t for t in clientes + productos if isinstance(t, str) and t.strip()]
    if extra:
        trozos.append(extra)
    if not trozos:
        return None
    texto = ", ".join(trozos)[:_LIMITE_WHISPER_CHARS]
    return f"Nombres propios y productos del negocio: {texto}."


def _append_unico(actual: list[str], valor: str) -> list[str]:
    v = (valor or "").strip()
    if not v:
        return actual
    baja = v.casefold()
    if any(x.casefold() == baja for x in actual):
        return actual
    out = actual + [v]
    return out[-_LIMITE_APODOS:]


def registrar_aprendizaje_exito(
    db: Session,
    empresa_id,
    usuario_id,
    herramienta: str,
    args: dict[str, Any] | None,
) -> None:
    """Tras acción confirmada y exitosa, guarda nombres para próximos turnos."""
    if not args:
        return
    mem = obtener_o_crear_memoria(db, empresa_id, usuario_id)
    clientes = _lista_apodos(mem.apodos_clientes)
    productos = _lista_apodos(mem.apodos_productos)
    h = (herramienta or "").strip()
    a = dict(args)

    if h in ("registrar_cliente", "crear_pedido", "registrar_cobro"):
        nombre = str(
            a.get("nombre") or a.get("cliente_nombre") or a.get("nombre_cliente") or ""
        ).strip()
        if nombre:
            clientes = _append_unico(clientes, nombre)

    if h == "crear_pedido":
        for item in a.get("productos") or []:
            if isinstance(item, dict):
                pn = str(item.get("nombre") or "").strip()
                if pn:
                    productos = _append_unico(productos, pn)

    if h == "registrar_producto_inventario":
        pn = str(a.get("nombre") or "").strip()
        if pn:
            productos = _append_unico(productos, pn)

    mem.apodos_clientes = clientes
    mem.apodos_productos = productos
    mem.updated_at = datetime.utcnow()
    try:
        db.commit()
    except Exception:
        logger.exception("No se pudo persistir memoria_voz")
        db.rollback()
