"""Ejecuta herramientas del asistente de voz sobre PocketBase (ORM)."""
from __future__ import annotations

import logging
import re
import unicodedata
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.tenant import obtener_empresa_tenant
from app.models.core import (
    CategoriaMovimientoFinanciero,
    Cliente,
    Cobro,
    EstadoVenta,
    FrecuenciaPago,
    MetodoPagoSalida,
    MonedaGasto,
    MonedaPago,
    Producto,
    Proveedor,
    RolUsuario,
    TipoCliente,
    TipoMovimientoFinanciero,
    TipoTasaUsd,
    TipoVisitaRuta,
    Usuario,
    Venta,
)
from app.services.ai_llm_tools import mensaje_permiso_denegado
from app.services.ai_product_context import invalidar_cache_inventario
from app.services.finanzas import registrar_movimiento
from app.services.ai_voice_n8n import solicitar_reporte_n8n
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
from app.services.inventario import (
    calcular_total_detalles,
    procesar_detalles_venta,
    stock_disponible,
)
from app.services.rutas import asignar_dia_orden, dia_actual, siguiente_orden_secuencial
from app.services.tasas_cambio import obtener_ultima_tasa

logger = logging.getLogger(__name__)

VoiceResult = tuple[bool, str, dict[str, Any], tuple[bool, str | None]]


class VoiceUserError(Exception):
    """Error de negocio del asistente de voz (mensaje para el usuario, no 500)."""

    def __init__(self, message: str, detalle: dict[str, Any] | None = None):
        self.message = message
        self.detalle = detalle or {}
        super().__init__(message)


def _fold_texto(valor: str) -> str:
    """Minúsculas sin acentos para comparar nombres de cliente/producto."""
    s = (valor or "").strip().casefold()
    descompuesto = unicodedata.normalize("NFKD", s)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def _respuesta_fallo(mensaje: str, detalle: dict[str, Any] | None = None) -> VoiceResult:
    return False, mensaje, detalle or {}, (False, None)


def _tasas_default(db: Session, empresa_id) -> tuple[float, float]:
    tasa = obtener_ultima_tasa(db, empresa_id)
    if not tasa:
        return 1.0, 0.0
    usd = float(tasa.usd_bcv_bs or tasa.usd_bs or 1.0)
    eur = float(tasa.eur_bs or 0.0)
    return usd, eur


def _ids_clientes_con_deuda(db: Session, empresa_id) -> set:
    estados = (EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL, EstadoVenta.POR_VERIFICAR)
    filas = (
        db.query(Venta.cliente_id)
        .filter(Venta.empresa_id == empresa_id, Venta.estado.in_(estados))
        .distinct()
        .all()
    )
    return {f[0] for f in filas if f[0] is not None}


def _candidatos_cliente(
    db: Session,
    empresa_id,
    nombre: str,
    telefono: str | None,
    *,
    solo_con_deuda: bool = False,
) -> list[Cliente]:
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
        return []
    candidatos = q.filter(or_(*filtros)).order_by(Cliente.nombre.asc()).all()
    if solo_con_deuda:
        con_deuda = _ids_clientes_con_deuda(db, empresa_id)
        candidatos = [c for c in candidatos if c.id in con_deuda]
    return candidatos


def _elegir_cliente_entre_candidatos(
    candidatos: list[Cliente],
    nombre_buscado: str,
) -> tuple[Cliente | None, str | None]:
    nombre = (nombre_buscado or "").strip()
    if not candidatos:
        if nombre:
            return None, (
                f"No encontré al cliente «{nombre}». "
                "¿Deseas registrarlo? Di por ejemplo: registrar cliente {nombre}."
            )
        return None, "Indica el nombre o teléfono del cliente."

    if len(candidatos) == 1:
        return candidatos[0], None

    buscado = _fold_texto(nombre)
    exactos = [c for c in candidatos if _fold_texto(c.nombre or "") == buscado]
    if len(exactos) == 1:
        return exactos[0], None
    if len(exactos) > 1:
        ejemplos = ", ".join(c.nombre for c in exactos[:4])
        return None, (
            f"Hay varios clientes llamados «{nombre}» ({ejemplos}). "
            "Sé más específico: apellido completo o teléfono."
        )

    if buscado:
        contiene = [c for c in candidatos if buscado in _fold_texto(c.nombre or "")]
        if len(contiene) == 1:
            return contiene[0], None

    ejemplos = ", ".join(c.nombre for c in candidatos[:4])
    return None, (
        f"Encontré varios clientes parecidos a «{nombre}» ({ejemplos}). "
        "Indica el nombre completo o el teléfono."
    )


def _resolver_cliente(
    db: Session,
    empresa_id,
    nombre: str,
    telefono: str | None,
    *,
    usuario: Usuario | None = None,
) -> tuple[Cliente | None, str | None]:
    solo_deuda = bool(usuario and usuario.rol == RolUsuario.COBRADOR)
    candidatos = _candidatos_cliente(
        db,
        empresa_id,
        nombre,
        telefono,
        solo_con_deuda=solo_deuda,
    )
    return _elegir_cliente_entre_candidatos(candidatos, nombre)


def _candidatos_producto(db: Session, empresa_id, nombre: str) -> list[Producto]:
    nombre = (nombre or "").strip()
    if not nombre:
        return []
    return (
        db.query(Producto)
        .filter(
            Producto.empresa_id == empresa_id,
            Producto.activo.is_(True),
            Producto.nombre.ilike(f"%{nombre}%"),
        )
        .order_by(Producto.nombre.asc())
        .all()
    )


def _elegir_producto_entre_candidatos(
    candidatos: list[Producto],
    nombre_buscado: str,
) -> tuple[Producto | None, str | None]:
    nombre = (nombre_buscado or "").strip()
    if not nombre:
        return None, "Indica el nombre del producto."

    if not candidatos:
        return None, f"No encontré el producto «{nombre}». Revisa el catálogo o el nombre."

    buscado = _fold_texto(nombre)
    exactos = [p for p in candidatos if _fold_texto(p.nombre or "") == buscado]
    if len(exactos) == 1:
        return exactos[0], None
    if len(exactos) > 1:
        nombres = ", ".join(p.nombre for p in exactos[:4])
        return None, f"Hay varios productos llamados «{nombre}» ({nombres}). Sé más específico."

    prefijo = [p for p in candidatos if _fold_texto(p.nombre or "").startswith(buscado)]
    if len(prefijo) == 1:
        return prefijo[0], None

    contiene = [p for p in candidatos if buscado in _fold_texto(p.nombre or "")]
    if len(contiene) == 1:
        return contiene[0], None

    if len(candidatos) == 1:
        return candidatos[0], None

    nombres = ", ".join(p.nombre for p in candidatos[:4])
    return None, (
        f"Encontré varios productos parecidos a «{nombre}» ({nombres}). "
        "Di el nombre completo del producto."
    )


def _resolver_producto(
    db: Session,
    empresa_id,
    nombre: str,
) -> tuple[Producto | None, str | None]:
    candidatos = _candidatos_producto(db, empresa_id, nombre)
    filtrados = [
        p
        for p in candidatos
        if _fold_texto(nombre) in _fold_texto(p.nombre or "")
        or _fold_texto(p.nombre or "").startswith(_fold_texto(nombre))
        or _fold_texto(p.nombre or "") == _fold_texto(nombre)
    ]
    base = filtrados if filtrados else candidatos
    return _elegir_producto_entre_candidatos(base, nombre)


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

    denegado = mensaje_permiso_denegado(usuario.rol, herramienta)
    if denegado:
        return _respuesta_fallo(
            denegado,
            {"codigo": "permiso_denegado", "herramienta": herramienta},
        )

    if herramienta == "registrar_cliente":
        return _registrar_cliente(db, usuario, empresa.id, args)
    if herramienta == "crear_pedido":
        return _crear_pedido(db, usuario, empresa.id, args)
    if herramienta == "registrar_cobro":
        return _registrar_cobro(db, usuario, empresa.id, args)
    if herramienta == "registrar_producto_inventario":
        return _registrar_producto_inventario(db, usuario, empresa.id, args)
    if herramienta == "consultar_inventario":
        return _consultar_inventario(db, empresa.id, args)
    if herramienta == "registrar_gasto":
        return _registrar_gasto(db, usuario, empresa.id, args)
    if herramienta == "registrar_proveedor":
        return _registrar_proveedor(db, usuario, empresa.id, args)
    if herramienta == "crear_factura_proveedor":
        return _crear_factura_proveedor(db, empresa.id, args)
    if herramienta == "consultar_clientes_deuda":
        return _consultar_clientes_deuda(db, usuario, empresa.id, args)
    if herramienta == "solicitar_reporte":
        return _solicitar_reporte_voz(db, usuario, empresa.id, args)
    if herramienta == "consultar_ventas_del_dia":
        return _consultar_ventas_del_dia(db, usuario, empresa.id)
    raise HTTPException(status_code=400, detail=f"Herramienta desconocida: {herramienta}")


def _registrar_cliente(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> tuple[bool, str, dict[str, Any], tuple[bool, str | None]]:
    from app.services.esquema_formulario import faltantes_cliente, pregunta_del_campo

    nombre = str(args.get("nombre") or "").strip()
    apellido = str(args.get("apellido") or "").strip()
    if apellido and apellido.casefold() not in nombre.casefold():
        nombre = f"{nombre} {apellido}".strip()
    telefono = str(args.get("telefono") or "").strip() or None
    direccion = str(args.get("direccion") or "").strip() or None
    whatsapp = str(args.get("whatsapp") or "").strip() or None
    faltan = faltantes_cliente({**args, "nombre": nombre})
    if faltan:
        return _respuesta_fallo(
            pregunta_del_campo("registrar_cliente", faltan[0]),
            {"codigo": "cliente_incompleto", "campo": faltan[0]},
        )

    ident = normalizar_identificacion(str(args.get("identificacion") or ""))
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
        telefono_secundario=whatsapp,
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
    if usuario.rol not in (RolUsuario.VENDEDOR, RolUsuario.DUENO):
        raise HTTPException(status_code=403, detail="Solo vendedores pueden crear pedidos por voz.")

    cliente_nombre = str(args.get("cliente_nombre") or "").strip()
    telefono = str(args.get("telefono") or "").strip() or None
    cliente, err_cliente = _resolver_cliente(
        db, empresa_id, cliente_nombre, telefono, usuario=usuario
    )
    if err_cliente or not cliente:
        return _respuesta_fallo(
            err_cliente or f"No encontré al cliente «{cliente_nombre}».",
            {
                "codigo": "cliente_no_encontrado",
                "cliente_nombre": cliente_nombre,
                "sugerencia": "registrar_cliente",
            },
        )

    items_raw = args.get("productos") or []
    if not isinstance(items_raw, list) or not items_raw:
        return _respuesta_fallo("Indica al menos un producto en el pedido.")

    detalles: list[DetalleVentaCreate] = []
    resumen_lineas: list[str] = []
    for item in items_raw:
        if not isinstance(item, dict):
            continue
        pnombre = str(item.get("nombre") or "").strip()
        cantidad = int(item.get("cantidad") or 1)
        if cantidad < 1:
            cantidad = 1
        producto, err_producto = _resolver_producto(db, empresa_id, pnombre)
        if err_producto or not producto:
            return _respuesta_fallo(
                err_producto or f"No encontré el producto «{pnombre}».",
                {"codigo": "producto_no_encontrado", "producto_nombre": pnombre},
            )
        disponible = stock_disponible(db, producto)
        if cantidad > disponible:
            return _respuesta_fallo(
                f"No hay suficiente stock de {producto.nombre} "
                f"(pediste {cantidad}, disponible {disponible}).",
                {
                    "codigo": "stock_insuficiente",
                    "producto_id": str(producto.id),
                    "producto_nombre": producto.nombre,
                    "cantidad_pedida": cantidad,
                    "stock_disponible": disponible,
                },
            )
        detalles.append(
            DetalleVentaCreate(producto_id=str(producto.id), cantidad=cantidad, tipo_precio="detal")
        )
        resumen_lineas.append(f"• {producto.nombre} x{cantidad}")

    if not detalles:
        return _respuesta_fallo("No pude procesar los productos del pedido. Repite los nombres.")

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
    if usuario.rol not in (RolUsuario.COBRADOR, RolUsuario.DUENO):
        raise HTTPException(status_code=403, detail="Solo cobradores pueden registrar cobros por voz.")

    nombre = str(args.get("cliente_nombre") or "").strip()
    telefono = str(args.get("telefono") or "").strip() or None
    monto = float(args.get("monto_usd") or 0)
    if monto <= 0:
        raise HTTPException(status_code=400, detail="Monto de cobro inválido.")

    cliente, err_cliente = _resolver_cliente(
        db, empresa_id, nombre, telefono, usuario=usuario
    )
    if err_cliente or not cliente:
        return _respuesta_fallo(
            err_cliente or f"No encontré al cliente «{nombre}».",
            {"codigo": "cliente_no_encontrado", "cliente_nombre": nombre},
        )

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


def _candidatos_proveedor(db: Session, empresa_id, nombre: str) -> list[Proveedor]:
    nombre = (nombre or "").strip()
    if not nombre:
        return []
    return (
        db.query(Proveedor)
        .filter(
            Proveedor.empresa_id == empresa_id,
            Proveedor.activo.is_(True),
            Proveedor.nombre.ilike(f"%{nombre}%"),
        )
        .order_by(Proveedor.nombre.asc())
        .all()
    )


def _resolver_proveedor(
    db: Session,
    empresa_id,
    nombre: str,
) -> tuple[Proveedor | None, str | None]:
    candidatos = _candidatos_proveedor(db, empresa_id, nombre)
    if not candidatos:
        return None, f"No encontré al proveedor «{nombre}»."
    buscado = _fold_texto(nombre)
    exactos = [p for p in candidatos if _fold_texto(p.nombre or "") == buscado]
    if len(exactos) == 1:
        return exactos[0], None
    if len(candidatos) == 1:
        return candidatos[0], None
    nombres = ", ".join(p.nombre for p in candidatos[:4])
    return None, f"Hay varios proveedores parecidos ({nombres}). Sé más específico."


def _candidatos_empleado(db: Session, empresa_id, nombre: str) -> list[Usuario]:
    nombre = (nombre or "").strip()
    if not nombre:
        return []
    return (
        db.query(Usuario)
        .filter(
            Usuario.empresa_id == empresa_id,
            Usuario.activo.is_(True),
            Usuario.nombre.ilike(f"%{nombre}%"),
        )
        .order_by(Usuario.nombre.asc())
        .all()
    )


def _resolver_empleado(
    db: Session,
    empresa_id,
    nombre: str,
) -> tuple[Usuario | None, str | None]:
    candidatos = _candidatos_empleado(db, empresa_id, nombre)
    if not candidatos:
        return None, f"No encontré al empleado «{nombre}»."
    buscado = _fold_texto(nombre)
    exactos = [u for u in candidatos if _fold_texto(u.nombre or "") == buscado]
    if len(exactos) == 1:
        return exactos[0], None
    if len(candidatos) == 1:
        return candidatos[0], None
    nombres = ", ".join(u.nombre for u in candidatos[:4])
    return None, f"Hay varios empleados parecidos ({nombres}). Di el nombre completo."


def _map_categoria_gasto(categoria: str) -> CategoriaMovimientoFinanciero:
    c = _fold_texto(categoria or "")
    if any(k in c for k in ("combust", "gasol", "moto", "motor")):
        return CategoriaMovimientoFinanciero.GASTO_MOTO
    if "servic" in c:
        return CategoriaMovimientoFinanciero.SERVICIOS_OPERATIVOS
    return CategoriaMovimientoFinanciero.OPERACION_GENERAL


def _map_metodo_salida(metodo: str) -> MetodoPagoSalida:
    m = (metodo or "efectivo").lower().replace(" ", "_")
    try:
        return MetodoPagoSalida(m)
    except ValueError:
        return MetodoPagoSalida.EFECTIVO


def _registrar_producto_inventario(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> VoiceResult:
    nombre = str(args.get("nombre") or "").strip()
    precio = float(args.get("precio_venta") or 0)
    stock = float(args.get("stock_inicial") or 0)
    categoria = str(args.get("categoria") or "").strip() or None
    if not nombre:
        return _respuesta_fallo("Indica el nombre del producto.")
    if precio <= 0:
        return _respuesta_fallo("Indica el precio de venta en dólares.")
    if stock < 0:
        return _respuesta_fallo("El stock inicial no puede ser negativo.")

    dup = (
        db.query(Producto)
        .filter(Producto.empresa_id == empresa_id, Producto.nombre.ilike(nombre))
        .first()
    )
    if dup:
        return _respuesta_fallo(f"Ya existe un producto llamado «{dup.nombre}».")

    producto = Producto(
        nombre=nombre,
        categoria=categoria,
        precio_usd=precio,
        costo_usd=0,
        stock=int(stock),
        stock_minimo=0,
        empresa_id=empresa_id,
        activo=True,
    )
    db.add(producto)
    db.commit()
    db.refresh(producto)
    invalidar_cache_inventario(empresa_id)
    detalle = {
        "producto_id": str(producto.id),
        "nombre": producto.nombre,
        "stock": int(producto.stock or 0),
        "precio_usd": float(producto.precio_usd),
    }
    return (
        True,
        f"Producto «{producto.nombre}» registrado con {int(stock)} unidades a ${precio:.2f} USD.",
        detalle,
        (False, None),
    )


def _consultar_inventario(
    db: Session,
    empresa_id,
    args: dict[str, Any],
) -> VoiceResult:
    filtro_nombre = str(args.get("nombre_producto") or "").strip()
    q = db.query(Producto).filter(
        Producto.empresa_id == empresa_id,
        Producto.activo.is_(True),
    )
    if filtro_nombre:
        producto, err = _resolver_producto(db, empresa_id, filtro_nombre)
        if err or not producto:
            return _respuesta_fallo(err or "Producto no encontrado.")
        disp = stock_disponible(db, producto)
        detalle = {
            "producto_id": str(producto.id),
            "nombre": producto.nombre,
            "stock_disponible": disp,
        }
        return (
            True,
            f"Quedan {disp} unidades de «{producto.nombre}».",
            detalle,
            (False, None),
        )

    productos = q.order_by(Producto.nombre.asc()).limit(8).all()
    total = q.count()
    if total == 0:
        return _respuesta_fallo("No hay productos activos en inventario.")
    lineas = []
    detalle_items: list[dict[str, Any]] = []
    for p in productos:
        disp = stock_disponible(db, p)
        lineas.append(f"{p.nombre}: {disp}")
        detalle_items.append({"nombre": p.nombre, "stock_disponible": disp})
    extra = f" (mostrando {len(productos)} de {total})" if total > len(productos) else ""
    msg = "Inventario" + extra + ": " + "; ".join(lineas) + "."
    return True, msg, {"items": detalle_items, "total_productos": total}, (False, None)


def _registrar_gasto(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> VoiceResult:
    monto = float(args.get("monto") or 0)
    descripcion = str(args.get("descripcion") or "").strip()
    categoria = str(args.get("categoria_gasto") or "general").strip()
    metodo = str(args.get("metodo_pago") or "efectivo")
    if monto <= 0:
        return _respuesta_fallo("Indica un monto válido para el gasto.")
    if not descripcion:
        return _respuesta_fallo("Indica una descripción del gasto.")

    mov = registrar_movimiento(
        db,
        empresa_id,
        usuario.id,
        {
            "tipo": TipoMovimientoFinanciero.SALIDA.value,
            "categoria": _map_categoria_gasto(categoria).value,
            "monto": monto,
            "moneda": MonedaGasto.USD.value,
            "metodo_pago": _map_metodo_salida(metodo).value,
            "descripcion": descripcion,
            "aprobado": usuario.rol in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR),
        },
    )
    db.commit()
    db.refresh(mov)
    detalle = {"movimiento_id": str(mov.id), "monto_usd": float(mov.monto_usd)}
    return (
        True,
        f"Gasto registrado: ${monto:.2f} USD — {descripcion}.",
        detalle,
        (False, None),
    )


def _registrar_proveedor(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> VoiceResult:
    nombre = str(args.get("nombre") or "").strip()
    telefono = str(args.get("telefono") or "").strip() or None
    direccion = str(args.get("direccion") or "").strip() or None
    condicion = str(args.get("condicion_pago") or "").strip()
    if not nombre:
        return _respuesta_fallo("Indica el nombre del proveedor.")

    notas_partes: list[str] = []
    if direccion:
        notas_partes.append(f"Dirección: {direccion}")
    if condicion:
        notas_partes.append(f"Condición de pago: {condicion}")
    notas = "\n".join(notas_partes) if notas_partes else None

    existente = (
        db.query(Proveedor)
        .filter(Proveedor.empresa_id == empresa_id, Proveedor.nombre.ilike(nombre))
        .first()
    )
    if existente and existente.activo:
        return _respuesta_fallo(f"Ya existe el proveedor «{existente.nombre}».")

    prov = Proveedor(
        empresa_id=empresa_id,
        nombre=nombre,
        telefono=telefono,
        notas=notas,
    )
    db.add(prov)
    db.commit()
    db.refresh(prov)
    detalle = {"proveedor_id": str(prov.id), "nombre": prov.nombre}
    return True, f"Proveedor «{prov.nombre}» registrado.", detalle, (False, None)


def _crear_factura_proveedor(
    db: Session,
    empresa_id,
    args: dict[str, Any],
) -> VoiceResult:
    nombre = str(args.get("proveedor_nombre") or "").strip()
    monto = float(args.get("monto") or 0)
    vencimiento = str(args.get("fecha_vencimiento") or "").strip() or None
    if monto <= 0:
        return _respuesta_fallo("Indica el monto de la factura en dólares.")
    prov, err = _resolver_proveedor(db, empresa_id, nombre)
    if err or not prov:
        return _respuesta_fallo(err or "Proveedor no encontrado.")

    prov.saldo_deuda_usd = Decimal(str(prov.saldo_deuda_usd or 0)) + Decimal(str(monto))
    nota = f"Factura por voz ${monto:.2f} USD"
    if vencimiento:
        nota += f", vence {vencimiento[:10]}"
    if prov.notas:
        prov.notas = f"{prov.notas}\n{nota}"
    else:
        prov.notas = nota
    db.commit()
    db.refresh(prov)
    detalle = {
        "proveedor_id": str(prov.id),
        "monto_usd": monto,
        "saldo_deuda_usd": float(prov.saldo_deuda_usd or 0),
        "fecha_vencimiento": vencimiento,
    }
    msg = (
        f"Factura de ${monto:.2f} USD registrada para «{prov.nombre}». "
        f"Saldo deuda: ${float(prov.saldo_deuda_usd):.2f} USD."
    )
    return True, msg, detalle, (False, None)


def estimar_total_pedido_voz(
    db: Session,
    empresa_id,
    args: dict[str, Any],
    usuario: Usuario,
) -> float | None:
    """Estima total USD para mensaje de confirmación (sin persistir)."""
    from app.models.core import TipoCliente

    cliente_nombre = str(args.get("cliente_nombre") or "").strip()
    telefono = str(args.get("telefono") or "").strip() or None
    cliente, err = _resolver_cliente(
        db, empresa_id, cliente_nombre, telefono, usuario=usuario
    )
    if err or not cliente:
        return None
    items_raw = args.get("productos") or []
    detalles: list[DetalleVentaCreate] = []
    for item in items_raw:
        if not isinstance(item, dict):
            continue
        pnombre = str(item.get("nombre") or "").strip()
        cantidad = int(item.get("cantidad") or 1)
        producto, err_producto = _resolver_producto(db, empresa_id, pnombre)
        if err_producto or not producto:
            return None
        detalles.append(
            DetalleVentaCreate(producto_id=str(producto.id), cantidad=cantidad, tipo_precio="detal")
        )
    if not detalles:
        return None
    tipo_cliente = cliente.tipo_cliente or TipoCliente.DETAL
    return float(calcular_total_detalles(db, empresa_id, detalles, tipo_cliente))


def _saldo_pendiente_venta(venta: Venta) -> Decimal:
    cobrado = sum(Decimal(str(c.monto_usd)) for c in (venta.cobros or []))
    return Decimal(str(venta.total_usd or 0)) - cobrado


def _consultar_clientes_deuda(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> VoiceResult:
    if usuario.rol not in (RolUsuario.COBRADOR, RolUsuario.DUENO):
        raise HTTPException(status_code=403, detail="Consulta de cartera no disponible.")

    filtro = str(args.get("nombre_cliente") or "").strip()
    estados = (EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL, EstadoVenta.POR_VERIFICAR)
    q = (
        db.query(Venta)
        .options(joinedload(Venta.cliente), joinedload(Venta.cobros))
        .filter(Venta.empresa_id == empresa_id, Venta.estado.in_(estados))
    )
    ventas = q.all()
    por_cliente: dict[str, tuple[str, Decimal]] = {}
    for v in ventas:
        if not v.cliente:
            continue
        saldo = _saldo_pendiente_venta(v)
        if saldo <= Decimal("0.01"):
            continue
        cid = str(v.cliente.id)
        nombre = v.cliente.nombre or "Cliente"
        prev = por_cliente.get(cid)
        por_cliente[cid] = (nombre, (prev[1] if prev else Decimal("0")) + saldo)

    filas = sorted(por_cliente.values(), key=lambda x: x[0].lower())
    if filtro:
        f = _fold_texto(filtro)
        filas = [(n, s) for n, s in filas if f in _fold_texto(n)]

    if not filas:
        msg = "No hay clientes con deuda pendiente."
        if filtro:
            msg = f"No encontré clientes con deuda que coincidan con «{filtro}»."
        return True, msg, {"clientes": []}, (False, None)

    resumen = "; ".join(f"{n} (${float(s):.2f})" for n, s in filas[:8])
    extra = f" y {len(filas) - 8} más" if len(filas) > 8 else ""
    msg = f"Clientes con deuda: {resumen}{extra}."
    detalle = {
        "clientes": [{"nombre": n, "saldo_usd": float(s)} for n, s in filas[:20]],
        "total_clientes": len(filas),
    }
    return True, msg, detalle, (False, None)


def _contacto_dueno_reporte(
    db: Session,
    empresa_id,
    canal: str,
) -> tuple[str | None, str | None]:
    dueno = (
        db.query(Usuario)
        .filter(
            Usuario.empresa_id == empresa_id,
            Usuario.rol == RolUsuario.DUENO,
            Usuario.activo.is_(True),
        )
        .order_by(Usuario.fecha_creacion.asc())
        .first()
    )
    if not dueno:
        return None, "No hay un dueño activo registrado en la empresa."
    if canal == "whatsapp":
        tel = (dueno.telefono or "").strip()
        if not tel:
            return None, "El dueño no tiene teléfono registrado para WhatsApp."
        return tel, None
    if canal == "correo":
        user = (dueno.username or "").strip()
        if "@" in user:
            return user, None
        return None, "El dueño no tiene correo registrado."
    return None, "Canal de reporte inválido."


def _solicitar_reporte_voz(
    db: Session,
    usuario: Usuario,
    empresa_id,
    args: dict[str, Any],
) -> VoiceResult:
    if usuario.rol != RolUsuario.DUENO:
        raise HTTPException(status_code=403, detail="Solo el dueño puede solicitar reportes.")

    tipo = str(args.get("tipo") or "").strip().lower()
    canal = str(args.get("canal") or "").strip().lower()
    tipos_ok = ("ventas_hoy", "cobros_hoy", "inventario_bajo")
    if tipo not in tipos_ok:
        return _respuesta_fallo(f"Tipo de reporte inválido. Usa: {', '.join(tipos_ok)}.")
    if canal not in ("whatsapp", "correo"):
        return _respuesta_fallo("Canal inválido. Di whatsapp o correo.")

    destino, err = _contacto_dueno_reporte(db, empresa_id, canal)
    if err or not destino:
        return _respuesta_fallo(err or "No pude obtener el contacto del dueño.")

    ok, det = solicitar_reporte_n8n(
        empresa_id=str(empresa_id),
        usuario_id=str(usuario.id),
        tipo=tipo,
        canal=canal,
        destino=destino,
    )
    if not ok:
        return _respuesta_fallo(
            "No se pudo solicitar el reporte. Intenta más tarde.",
            {"codigo": "n8n_fallido", "detalle": det},
        )
    msg = f"Reporte {tipo.replace('_', ' ')} solicitado por {canal}. Lo recibirás en breve."
    return True, msg, {"tipo": tipo, "canal": canal}, (False, None)


def _consultar_ventas_del_dia(
    db: Session,
    usuario: Usuario,
    empresa_id,
) -> VoiceResult:
    hoy = date.today()
    inicio = datetime.combine(hoy, time.min)
    fin = datetime.combine(hoy, time.max)
    q = db.query(Venta).filter(
        Venta.empresa_id == empresa_id,
        Venta.fecha >= inicio,
        Venta.fecha <= fin,
    )
    if usuario.rol == RolUsuario.VENDEDOR:
        q = q.filter(Venta.vendedor_id == usuario.id)
    ventas = q.all()
    total = sum(float(v.total_usd or 0) for v in ventas)
    n = len(ventas)
    if usuario.rol == RolUsuario.VENDEDOR:
        msg = f"Hoy vendiste ${total:.2f} USD en {n} venta(s)."
    else:
        msg = f"Hoy se vendió ${total:.2f} USD en {n} venta(s) en la empresa."
    detalle = {"total_usd": total, "num_ventas": n, "fecha": hoy.isoformat()}
    return True, msg, detalle, (False, None)
