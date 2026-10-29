"""Perfil de la empresa y memoria factual de cada cliente, aislados por tenant."""
from __future__ import annotations

import logging
import unicodedata
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.pb_orm.ids import nuevo_id_pocketbase
from app.models.core import Cliente, Empresa, RolUsuario
from app.services.ai_voice_models import MemoriaCliente, PerfilEmpresa

logger = logging.getLogger(__name__)

BORRADOR_ED_NET_PRO = {
    "descripcion": (
        "ED NET PRO vende y cobra en ruta. Este texto es un borrador: "
        "edítalo en la colección perfil_empresa."
    ),
    "productos_servicios": "Los productos y servicios que figuran en el inventario de la empresa.",
    "tono": "Claro, breve y cercano, en español latinoamericano.",
    "glosario": "fiado: venta a crédito. abono: pago parcial de una deuda. ruta: recorrido de clientes del día.",
    "reglas": (
        "No inventes precios, deudas ni datos del cliente. "
        "Pide un solo dato cuando falte. Confirma antes de guardar."
    ),
}


def _fold(texto: str) -> str:
    s = (texto or "").strip().casefold()
    plano = unicodedata.normalize("NFKD", s)
    return "".join(c for c in plano if not unicodedata.combining(c))


def _es_ed_net(nombre: str | None) -> bool:
    return "ed net" in _fold(nombre or "")


def asegurar_borrador_ed_net(db: Session, empresa_id) -> None:
    """Crea el borrador de ED NET PRO si esa empresa aún no tiene perfil."""
    try:
        existe = (
            db.query(PerfilEmpresa).filter(PerfilEmpresa.empresa_id == empresa_id).first()
        )
        if isinstance(existe, PerfilEmpresa):
            return
        empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
        if not isinstance(empresa, Empresa) or not _es_ed_net(empresa.nombre):
            return
        db.add(
            PerfilEmpresa(
                id=nuevo_id_pocketbase(),
                empresa_id=empresa_id,
                updated_at=datetime.utcnow(),
                **BORRADOR_ED_NET_PRO,
            )
        )
        db.commit()
    except Exception:
        logger.debug("No se pudo crear el borrador de perfil_empresa", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass


def bloque_perfil_llm(db: Session, empresa_id) -> str:
    try:
        asegurar_borrador_ed_net(db, empresa_id)
        perfil = (
            db.query(PerfilEmpresa).filter(PerfilEmpresa.empresa_id == empresa_id).first()
        )
    except Exception:
        logger.debug("perfil_empresa no disponible", exc_info=True)
        return ""
    if not isinstance(perfil, PerfilEmpresa):
        return ""
    partes = ["PERFIL DE LA EMPRESA (respétalo; no lo inventes):"]
    if perfil.descripcion:
        partes.append(f"- Negocio: {perfil.descripcion}")
    if perfil.productos_servicios:
        partes.append(f"- Productos y servicios: {perfil.productos_servicios}")
    if perfil.tono:
        partes.append(f"- Tono: {perfil.tono}")
    if perfil.glosario:
        partes.append(f"- Glosario: {perfil.glosario}")
    if perfil.reglas:
        partes.append(f"- Reglas: {perfil.reglas}")
    if len(partes) == 1:
        return ""
    return "\n".join(partes)


def _clientes_visibles(db: Session, usuario) -> list[Cliente]:
    q = db.query(Cliente).filter(Cliente.empresa_id == usuario.empresa_id)
    if getattr(usuario, "rol", None) == RolUsuario.VENDEDOR:
        q = q.filter(Cliente.vendedor_id == usuario.id)
    elif getattr(usuario, "rol", None) == RolUsuario.COBRADOR:
        from app.services.ai_voice_executor import _ids_clientes_con_deuda

        ids = _ids_clientes_con_deuda(db, usuario.empresa_id)
        if not ids:
            return []
        q = q.filter(Cliente.id.in_(ids))
    try:
        filas = q.all()
    except Exception:
        return []
    return [c for c in filas if isinstance(c, Cliente)]


def clientes_mencionados(texto: str, clientes: list[Cliente]) -> list[Cliente]:
    dicho = _fold(texto)
    if not dicho:
        return []
    encontrados: list[Cliente] = []
    for cliente in clientes:
        nombre = _fold(getattr(cliente, "nombre", "") or "")
        if len(nombre) >= 3 and nombre in dicho:
            encontrados.append(cliente)
    return encontrados


def bloque_memoria_cliente_llm(db: Session, usuario, texto: str) -> str:
    """Carga el resumen solo de los clientes de ESTA empresa nombrados en el turno."""
    try:
        mencionados = clientes_mencionados(texto, _clientes_visibles(db, usuario))
    except Exception:
        logger.debug("memoria_cliente no disponible", exc_info=True)
        return ""
    if not mencionados:
        return ""
    lineas = ["MEMORIA DE CLIENTES MENCIONADOS (hechos guardados, no suposiciones):"]
    for cliente in mencionados[:3]:
        try:
            fila = (
                db.query(MemoriaCliente)
                .filter(
                    MemoriaCliente.empresa_id == usuario.empresa_id,
                    MemoriaCliente.cliente_id == cliente.id,
                )
                .first()
            )
        except Exception:
            continue
        if isinstance(fila, MemoriaCliente) and (fila.resumen or "").strip():
            lineas.append(f"- {cliente.nombre}: {fila.resumen.strip()}")
    if len(lineas) == 1:
        return ""
    return "\n".join(lineas)


def resumen_factual(herramienta: str, args: dict[str, Any]) -> str:
    """Arma una frase solo con lo que se confirmó. No completa huecos."""
    h = (herramienta or "").strip()
    a = dict(args or {})
    if h == "crear_pedido":
        partes = []
        for item in a.get("productos") or []:
            if isinstance(item, dict) and str(item.get("nombre") or "").strip():
                cant = int(item.get("cantidad") or 1)
                partes.append(f"{cant} {str(item['nombre']).strip()}")
        if not partes:
            return ""
        return f"Compró {', '.join(partes)}."
    if h == "registrar_cobro":
        monto = a.get("monto_usd")
        if monto is None:
            return ""
        metodo = str(a.get("metodo_pago") or "").replace("_", " ").strip()
        extra = f" por {metodo}" if metodo else ""
        return f"Abonó {monto} dólares{extra}."
    if h == "registrar_cliente":
        nombre = str(a.get("nombre") or "").strip()
        if not nombre:
            return ""
        return f"Cliente registrado: {nombre}."
    return ""


def actualizar_memoria_cliente_confirmada(
    db: Session,
    usuario,
    herramienta: str,
    args: dict[str, Any] | None,
) -> None:
    frase = resumen_factual(herramienta, args or {})
    if not frase:
        return
    try:
        mencionados = clientes_mencionados(
            str((args or {}).get("cliente_nombre") or (args or {}).get("nombre") or ""),
            _clientes_visibles(db, usuario),
        )
        if not mencionados:
            return
        cliente = mencionados[0]
        fila = (
            db.query(MemoriaCliente)
            .filter(
                MemoriaCliente.empresa_id == usuario.empresa_id,
                MemoriaCliente.cliente_id == cliente.id,
            )
            .first()
        )
        if not isinstance(fila, MemoriaCliente):
            fila = MemoriaCliente(
                id=nuevo_id_pocketbase(),
                empresa_id=usuario.empresa_id,
                cliente_id=cliente.id,
                resumen="",
                updated_at=datetime.utcnow(),
            )
            db.add(fila)
        previo = (fila.resumen or "").strip()
        fila.resumen = f"{previo} {frase}".strip()[:500]
        fila.updated_at = datetime.utcnow()
        db.commit()
    except Exception:
        logger.debug("No se pudo actualizar memoria_cliente", exc_info=True)
        try:
            db.rollback()
        except Exception:
            pass
