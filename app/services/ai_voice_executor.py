"""Ejecuta herramientas del asistente de voz sobre PocketBase (ORM)."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.tenant import obtener_empresa_tenant
from app.models.core import (
    Cliente,
    Cobro,
    EstadoVenta,
    FrecuenciaPago,
    MonedaPago,
    Producto,
    RolUsuario,
    TipoCliente,
    TipoTasaUsd,
    TipoVisitaRuta,
    Usuario,
    Venta,
)
from app.schemas.core import DetalleVentaCreate
from app.services.buro_credito import (
    actualizar_historial_comportamiento,
    normalizar_identificacion,
    registrar_evento_buro,
    sincronizar_score_inicial,
    validar_venta_credito,
)
from app.services.contabilidad import generar_asiento_cobro, generar_asiento_venta
from app.services.evolution_service import enviar_texto
from app.services.inventario import calcular_total_detalles, procesar_detalles_venta
from app.services.rutas import asignar_dia_orden, dia_actual, siguiente_orden_secuencial
from app.services.tasas_cambio import obtener_ultima_tasa

logger = logging.getLogger(__name__)


def _tasas_default(db: Session, empresa_id) -> tuple[float, float]:
    tasa = obtener_ultima_tasa(db, empresa_id)
    if not tasa:
        return 1.0, 0.0
    usd = float(tasa.usd_bcv_bs or tasa.usd_bs or 1.0)
    eur = float(tasa.eur_bs or 0.0)
    return usd, eur


def _buscar_cliente(db: Session, empresa_id, nombre: str, telefono: str | None) -> Cliente | None:
    nombre = (nombre or "").strip()
    tel = re.sub(r"\D", "", telefono or "")
    q = db.query(Cliente).filter(Cliente.empresa_id == empresa_id)
    filtros = []
    if nombre:
        filtros.append(Cliente.nombre.ilike(f"%{nombre}%"))
    if tel:
        filtros.extend(
            [
                Cliente.telefono.ilike(f"%{tel[-10:]}%"),
                Cliente.telefono_secundario.ilike(f"%{tel[-10:]}%"),
            ]
        )
    if not filtros:
        return None
    return q.filter(or_(*filtros)).order_by(Cliente.nombre.asc()).first()


def _buscar_producto(db: Session, empresa_id, nombre: str) -> Producto | None:
    nombre = (nombre or "").strip()
    if not nombre:
        return None
    return (
        db.query(Producto)
        .filter(
            Producto.empresa_id == empresa_id,
            Producto.activo.is_(True),
            Producto.nombre.ilike(f"%{nombre}%"),
        )
        .order_by(Producto.nombre.asc())
        .first()
    )


def _identificacion_desde_voz(ident: str | None, telefono: str | None) -> str:
    if ident and len(ident.strip()) >= 5:
        return normalizar_identificacion(ident)
    digitos = re.sub(r"\D", "", telefono or "")
    if len(digitos) >= 8:
        return normalizar_identificacion(f"V{digitos[-10:]}")
    raise HTTPException(status_code=400, detail="Indica cédula o teléfono válido para el cliente.")


def _whatsapp_confirmar(telefono: str | None, texto: str) -> tuple[bool, str | None]:
    if not telefono:
        return False, "Sin teléfono para WhatsApp."
    try:
        ok, det = enviar_texto(telefono, texto)
        return ok, det
    except Exception as exc:
        logger.exception("WhatsApp asistente voz")
        return False, str(exc)


def ejecutar_herramienta_voz(
    db: Session,
    usuario: Usuario,
    herramienta: str,
    args: dict[str, Any],
) -> tuple[bool, str, dict[str, Any], tuple[bool, str | None]]:
    empresa = obtener_empresa_tenant(db, usuario)

    if herramienta == "registrar_cliente":
        return _registrar_cliente(db, usuario, empresa.id, args)
    if herramienta == "crear_pedido":
        return _crear_pedido(db, usuario, empresa.id, args)
    if herramienta == "registrar_cobro":
        return _registrar_cobro(db, usuario, empresa.id, args)
    raise HTTPException(status_code=400, detail=f"Herramienta desconocida: {herramienta}")


def _registrar_cliente(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> tuple[bool, str, dict[str, Any], tuple[bool, str | None]]:
    nombre = str(args.get("nombre") or "").strip()
    telefono = str(args.get("telefono") or "").strip() or None
    direccion = str(args.get("direccion") or "").strip() or None
    if not nombre:
        raise HTTPException(status_code=400, detail="Falta el nombre del cliente.")

    ident = _identificacion_desde_voz(args.get("identificacion"), telefono)
    existente = db.query(Cliente).filter(Cliente.identificacion == ident).first()
    if existente:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con esa identificación.")

    vendedor_id = usuario.id if usuario.rol == RolUsuario.VENDEDOR else None
    dia_visita = dia_actual() if vendedor_id else None
    orden = (
        siguiente_orden_secuencial(db, vendedor_id, dia_visita, empresa_id)
        if vendedor_id and dia_visita
        else None
    )

    cliente = Cliente(
        nombre=nombre,
        identificacion=ident,
        telefono=telefono,
        direccion=direccion,
        tipo_cliente=TipoCliente.DETAL,
        vendedor_id=vendedor_id,
        tipo_visita_ruta=TipoVisitaRuta.NUEVO if vendedor_id else TipoVisitaRuta.FRECUENTE,
        empresa_id=empresa_id,
    )
    asignar_dia_orden(cliente, dia_visita, orden)
    sincronizar_score_inicial(db, cliente)
    actualizar_historial_comportamiento(db, cliente)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)

    msg_wa = (
        f"*Ruteros* — Hola {cliente.nombre}, quedaste registrado en nuestra ruta.\n"
        f"Dirección: {direccion or '—'}\n"
        "Gracias por confiar en nosotros."
    )
    wa = _whatsapp_confirmar(cliente.telefono, msg_wa)
    detalle = {"cliente_id": str(cliente.id), "nombre": cliente.nombre}
    return True, f"Cliente {cliente.nombre} registrado.", detalle, wa


def _crear_pedido(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> tuple[bool, str, dict[str, Any], tuple[bool, str | None]]:
    if usuario.rol not in (RolUsuario.VENDEDOR, RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        raise HTTPException(status_code=403, detail="Solo vendedores pueden crear pedidos por voz.")

    cliente_nombre = str(args.get("cliente_nombre") or "").strip()
    telefono = str(args.get("telefono") or "").strip() or None
    cliente = _buscar_cliente(db, empresa_id, cliente_nombre, telefono)
    if not cliente:
        raise HTTPException(
            status_code=400,
            detail=f"No encontré al cliente «{cliente_nombre}». Regístralo primero.",
        )

    items_raw = args.get("productos") or []
    if not isinstance(items_raw, list) or not items_raw:
        raise HTTPException(status_code=400, detail="Indica al menos un producto.")

    detalles: list[DetalleVentaCreate] = []
    resumen_lineas: list[str] = []
    for item in items_raw:
        if not isinstance(item, dict):
            continue
        pnombre = str(item.get("nombre") or "").strip()
        cantidad = int(item.get("cantidad") or 1)
        if cantidad < 1:
            cantidad = 1
        producto = _buscar_producto(db, empresa_id, pnombre)
        if not producto:
            raise HTTPException(status_code=400, detail=f"Producto no encontrado: {pnombre}")
        detalles.append(
            DetalleVentaCreate(producto_id=str(producto.id), cantidad=cantidad, tipo_precio="detal")
        )
        resumen_lineas.append(f"• {producto.nombre} x{cantidad}")

    metodo = str(args.get("metodo_pago") or "efectivo").lower()
    if metodo not in ("efectivo", "transferencia", "pago_movil"):
        metodo = "efectivo"

    tasa_usd, tasa_eur = _tasas_default(db, empresa_id)
    tipo_cliente = cliente.tipo_cliente or TipoCliente.DETAL
    total = float(calcular_total_detalles(db, empresa_id, detalles, tipo_cliente))

    validar_venta_credito(cliente, FrecuenciaPago.CONTADO)
    actualizar_historial_comportamiento(db, cliente)

    from app.core.pb_orm.ids import nuevo_id_pocketbase

    venta = Venta(
        id=nuevo_id_pocketbase(),
        empresa_id=empresa_id,
        cliente_id=cliente.id,
        vendedor_id=usuario.id,
        fecha=datetime.utcnow(),
        total_usd=Decimal(str(total)),
        tasa_usd_aplicada=tasa_usd,
        tasa_eur_aplicada=tasa_eur,
        tipo_tasa_usd=TipoTasaUsd.BCV,
        frecuencia_pago=FrecuenciaPago.CONTADO,
        estado=EstadoVenta.PAGADA if metodo == "efectivo" else EstadoVenta.POR_VERIFICAR,
        metodo_pago=metodo,
    )
    db.add(venta)
    db.flush()
    procesar_detalles_venta(
        db, venta, detalles, almacen_id=None, tipo_cliente=tipo_cliente, descontar_inventario=True
    )
    generar_asiento_venta(db, venta)
    registrar_evento_buro(
        db,
        cliente.identificacion,
        "compra",
        f"Pedido por voz ${total:.2f} — {cliente.nombre}.",
    )
    db.commit()
    db.refresh(venta)

    msg_wa = (
        f"*Ruteros* — Pedido confirmado para {cliente.nombre}\n"
        + "\n".join(resumen_lineas)
        + f"\n\n*Total:* ${total:.2f} USD\nMétodo: {metodo.replace('_', ' ')}"
    )
    tel = telefono or cliente.telefono
    wa = _whatsapp_confirmar(tel, msg_wa)
    detalle = {
        "venta_id": str(venta.id),
        "cliente_id": str(cliente.id),
        "total_usd": total,
        "productos": resumen_lineas,
    }
    return True, f"Pedido registrado por ${total:.2f} USD.", detalle, wa


def _map_moneda_pago(metodo: str) -> MonedaPago:
    m = (metodo or "").lower()
    if m in ("transferencia",):
        return MonedaPago.TRANSFERENCIA
    if m in ("pago_movil", "pago movil"):
        return MonedaPago.PAGO_MOVIL
    if m in ("bolivar", "bs", "ves"):
        return MonedaPago.BOLIVAR
    return MonedaPago.DOLAR


def _venta_pendiente_cliente(db: Session, empresa_id, cliente_id) -> Venta | None:
    estados = (EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL, EstadoVenta.POR_VERIFICAR)
    return (
        db.query(Venta)
        .options(joinedload(Venta.cobros))
        .filter(
            Venta.empresa_id == empresa_id,
            Venta.cliente_id == cliente_id,
            Venta.estado.in_(estados),
        )
        .order_by(Venta.fecha.desc())
        .first()
    )


def _registrar_cobro(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> tuple[bool, str, dict[str, Any], tuple[bool, str | None]]:
    if usuario.rol not in (RolUsuario.COBRADOR, RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        raise HTTPException(status_code=403, detail="Solo cobradores pueden registrar cobros por voz.")

    nombre = str(args.get("cliente_nombre") or "").strip()
    telefono = str(args.get("telefono") or "").strip() or None
    monto = float(args.get("monto_usd") or 0)
    if monto <= 0:
        raise HTTPException(status_code=400, detail="Monto de cobro inválido.")

    cliente = _buscar_cliente(db, empresa_id, nombre, telefono)
    if not cliente:
        raise HTTPException(status_code=400, detail=f"No encontré al cliente «{nombre}».")

    venta = _venta_pendiente_cliente(db, empresa_id, cliente.id)
    if not venta:
        raise HTTPException(status_code=400, detail="El cliente no tiene ventas pendientes de cobro.")

    cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
    saldo = Decimal(str(venta.total_usd)) - cobrado
    if Decimal(str(monto)) > saldo + Decimal("0.01"):
        raise HTTPException(
            status_code=400,
            detail=f"El monto excede el saldo pendiente (${float(saldo):.2f}).",
        )

    metodo = str(args.get("metodo_pago") or "efectivo")
    moneda = _map_moneda_pago(metodo)
    es_electronico = moneda in (MonedaPago.TRANSFERENCIA, MonedaPago.PAGO_MOVIL)
    tasa_usd, tasa_eur = _tasas_default(db, empresa_id)

    from app.core.pb_orm.ids import nuevo_id_pocketbase
    from app.services.amortizacion import aplicar_abono_a_cuotas

    cobro = Cobro(
        id=nuevo_id_pocketbase(),
        empresa_id=empresa_id,
        venta_id=venta.id,
        cobrador_id=usuario.id,
        fecha=datetime.utcnow(),
        monto_usd=monto,
        moneda_pago=moneda,
        tasa_usd_aplicada=tasa_usd,
        tasa_eur_aplicada=tasa_eur,
        es_transferencia=es_electronico,
        verificado=not es_electronico or usuario.rol in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR),
    )
    db.add(cobro)
    db.flush()
    db.refresh(venta, attribute_names=["cobros", "cliente", "cuotas"])
    total_cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
    if total_cobrado >= Decimal(str(venta.total_usd)):
        venta.estado = EstadoVenta.PAGADA
    elif total_cobrado > 0:
        venta.estado = EstadoVenta.PARCIAL
    aplicar_abono_a_cuotas(db, venta, Decimal(str(monto)))
    if venta.cliente:
        actualizar_historial_comportamiento(db, venta.cliente)
    generar_asiento_cobro(db, cobro)
    db.commit()
    db.refresh(cobro)

    msg_wa = (
        f"*Ruteros* — Cobro registrado\n"
        f"Cliente: {cliente.nombre}\n"
        f"Monto: ${monto:.2f} USD\n"
        f"Método: {metodo}\n"
        f"Saldo venta: ${float(max(saldo - Decimal(str(monto)), Decimal('0'))):.2f} USD"
    )
    tel = telefono or cliente.telefono
    wa = _whatsapp_confirmar(tel, msg_wa)
    detalle = {
        "cobro_id": str(cobro.id),
        "venta_id": str(venta.id),
        "cliente_id": str(cliente.id),
        "monto_usd": monto,
    }
    return True, f"Cobro de ${monto:.2f} USD registrado.", detalle, wa
