from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import (
    obtener_usuario_opcional,
    require_vendedor_o_superior,
    require_operaciones,
    require_admin_o_dueno,
    rol_confirma_pago,
)
from app.core.tenant import obtener_empresa_tenant
from app.api.empresas import resolver_cuenta_transferencia
from app.models.core import (
    Venta, Cliente, Usuario, FrecuenciaPago, EstadoVenta, TipoCliente,
    RolUsuario, TipoTasaUsd, Producto, DetalleVenta,
)
from app.schemas.core import (
    VentaCreate,
    VentaResponse,
    DetalleVentaResponse,
    CuotaAmortizacionResponse,
    EnvioReciboResponse,
    WhatsappReporteResponse,
)
from app.services.evolution_service import (
    armar_caption_comprobante,
    enviar_imagen,
    enviar_texto,
    estado_http_whatsapp,
    normalizar_telefono,
    telefono_administrador,
)
from app.services.recibos_email import enviar_recibo_venta, texto_recibo_venta
from app.services.contabilidad import generar_asiento_venta
from app.services.inventario import procesar_detalles_venta, calcular_total_detalles
from app.services.buro_credito import (
    actualizar_historial_comportamiento,
    actualizar_score_por_cobro,
    clasificacion_por_score,
    clasificar_score,
    registrar_evento_buro,
    validar_venta_credito,
)
from app.services.amortizacion import generar_plan_amortizacion, puede_aprobar_venta, serializar_cuota
from datetime import datetime
from typing import List, Optional
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

FRECUENCIA_LABEL = {
    "semanal": "Semanal",
    "quincenal": "Quincenal",
    "mensual": "Mensual",
    "contado": "Contado",
}


def _resolver_cliente(db: Session, empresa_id, cliente_id=None) -> Cliente:
    if cliente_id:
        cliente = (
            db.query(Cliente)
            .filter(Cliente.id == cliente_id, Cliente.empresa_id == empresa_id)
            .first()
        )
        if not cliente:
            raise HTTPException(status_code=400, detail="Cliente no encontrado")
        return cliente
    cliente = db.query(Cliente).filter(Cliente.empresa_id == empresa_id).first()
    if not cliente:
        raise HTTPException(status_code=400, detail="Debes crear al menos un cliente")
    return cliente


def _resolver_vendedor(
    db: Session,
    empresa_id,
    usuario_header: Optional[Usuario],
) -> Usuario:
    if usuario_header:
        if usuario_header.empresa_id != empresa_id:
            raise HTTPException(status_code=400, detail="Usuario no pertenece a la empresa")
        if usuario_header.rol not in (RolUsuario.VENDEDOR, RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
            raise HTTPException(status_code=403, detail="Solo VENDEDOR, ADMINISTRADOR o DUEÑO puede registrar ventas")
        return usuario_header
    vendedor = (
        db.query(Usuario)
        .filter(Usuario.empresa_id == empresa_id, Usuario.rol == RolUsuario.VENDEDOR)
        .first()
    )
    if not vendedor:
        vendedor = db.query(Usuario).filter(Usuario.empresa_id == empresa_id).first()
    if not vendedor:
        raise HTTPException(status_code=400, detail="Debes crear al menos un vendedor")
    return vendedor


def _rel_lista(obj, nombre: str) -> list:
    insp = sa_inspect(obj)
    if nombre in insp.unloaded:
        return []
    return list(getattr(obj, nombre, None) or [])


def _rel_uno(obj, nombre: str):
    insp = sa_inspect(obj)
    if nombre in insp.unloaded:
        return None
    return getattr(obj, nombre, None)


def partir_nombre_cliente(nombre: str | None) -> tuple[str, str]:
    """El alta guarda nombre y apellido juntos en `nombre`."""
    partes = (nombre or "").strip().split()
    if not partes:
        return "", ""
    if len(partes) == 1:
        return partes[0], ""
    return " ".join(partes[:-1]), partes[-1]


def _venta_a_response(db: Session, venta: Venta) -> VentaResponse:
    frecuencia = venta.frecuencia_pago or FrecuenciaPago.CONTADO
    if not isinstance(frecuencia, FrecuenciaPago):
        try:
            frecuencia = FrecuenciaPago(str(frecuencia))
        except ValueError:
            frecuencia = FrecuenciaPago.CONTADO
    cuotas_enriquecidas = [
        CuotaAmortizacionResponse(**serializar_cuota(c, frecuencia))
        for c in sorted(_rel_lista(venta, "cuotas"), key=lambda x: x.numero_cuota or 0)
    ]
    detalles = []
    nombres = []
    for d in _rel_lista(venta, "detalles"):
        candidatos = db.query(Producto).filter(Producto.id == d.producto_id).all() if d.producto_id else []
        prod = next((p for p in candidatos if str(p.id) == str(d.producto_id)), None)
        nombre = prod.nombre if prod else None
        if nombre:
            nombres.append(f"{nombre} x{d.cantidad}")
        detalles.append(
            DetalleVentaResponse(
                id=d.id,
                producto_id=d.producto_id,
                cantidad=d.cantidad,
                precio_unitario_usd=float(d.precio_unitario_usd or 0),
                producto_nombre=nombre,
            )
        )
    cliente = _rel_uno(venta, "cliente")
    nombre_cli, apellido_cli = partir_nombre_cliente(cliente.nombre if cliente else None)
    cobrado = sum(
        (Decimal(str(c.monto_usd)) for c in _rel_lista(venta, "cobros") if c.monto_usd is not None),
        Decimal("0"),
    )
    saldo = float(Decimal(str(venta.total_usd or 0)) - cobrado)
    estado = venta.estado.value if isinstance(venta.estado, EstadoVenta) else str(venta.estado or "")
    return VentaResponse(
        id=venta.id,
        empresa_id=venta.empresa_id,
        cliente_id=venta.cliente_id,
        vendedor_id=venta.vendedor_id,
        total_usd=float(venta.total_usd or 0),
        estado=estado,
        frecuencia_pago=frecuencia.value,
        tipo_tasa_usd=venta.tipo_tasa_usd.value if getattr(venta, "tipo_tasa_usd", None) else "bcv",
        numero_cuotas=venta.numero_cuotas,
        metodo_pago=venta.metodo_pago or "efectivo",
        referencia_pago=venta.referencia_pago,
        tiene_comprobante=bool(venta.comprobante_base64),
        cuenta_bancaria_id=venta.cuenta_bancaria_id,
        detalles=detalles,
        cuotas=cuotas_enriquecidas,
        fecha=venta.fecha,
        cliente_nombre=nombre_cli,
        cliente_apellido=apellido_cli,
        cliente_telefono=cliente.telefono if cliente else None,
        cliente_email=cliente.email if cliente else None,
        saldo_pendiente_usd=saldo,
        productos_resumen=", ".join(nombres) if nombres else "—",
    )


def _filtrar_por_cliente(ventas: list[Venta], q: str | None) -> list[Venta]:
    texto = (q or "").strip().casefold()
    if not texto:
        return ventas
    salida = []
    for venta in ventas:
        cliente = _rel_uno(venta, "cliente")
        if cliente is None:
            continue
        nombre = (cliente.nombre or "").casefold()
        telefono = (cliente.telefono or "").casefold()
        if texto in nombre or texto in telefono:
            salida.append(venta)
    return salida


def _actualizar_ubicacion_cliente(cliente: Cliente, venta: VentaCreate) -> None:
    if venta.latitud_residencia is not None:
        cliente.latitud_residencia = venta.latitud_residencia
    if venta.longitud_residencia is not None:
        cliente.longitud_residencia = venta.longitud_residencia
    if venta.latitud_trabajo is not None:
        cliente.latitud_trabajo = venta.latitud_trabajo
    if venta.longitud_trabajo is not None:
        cliente.longitud_trabajo = venta.longitud_trabajo


@router.post("/", response_model=VentaResponse)
def crear_venta(
    venta: VentaCreate,
    db: Session = Depends(get_db),
    usuario_header: Usuario = Depends(require_vendedor_o_superior),
):
    empresa_actual = obtener_empresa_tenant(db, usuario_header)
    cliente_actual = _resolver_cliente(db, empresa_actual.id, venta.cliente_id)
    vendedor_actual = _resolver_vendedor(db, empresa_actual.id, usuario_header)

    try:
        frecuencia = FrecuenciaPago(venta.frecuencia_pago)
    except ValueError:
        raise HTTPException(status_code=400, detail="Frecuencia de pago inválida")

    try:
        tipo_tasa = TipoTasaUsd(venta.tipo_tasa_usd or "bcv")
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo de tasa USD inválido")

    es_borrador = venta.es_borrador and vendedor_actual.rol == RolUsuario.VENDEDOR
    metodo = (venta.metodo_pago or "efectivo").strip().lower()
    if metodo not in ("efectivo", "transferencia", "pago_movil"):
        raise HTTPException(status_code=400, detail="Método de pago inválido")
    cuenta_destino = None
    if metodo in ("transferencia", "pago_movil"):
        cuenta_destino = resolver_cuenta_transferencia(
            db, empresa_actual.id, venta.cuenta_bancaria_id, canal=metodo
        )

    if not es_borrador:
        actualizar_historial_comportamiento(db, cliente_actual)
    validar_venta_credito(cliente_actual, frecuencia)

    _actualizar_ubicacion_cliente(cliente_actual, venta)

    tipo_cliente = cliente_actual.tipo_cliente or TipoCliente.DETAL
    total_venta = Decimal(str(venta.total_usd))

    if venta.detalles:
        total_calculado = calcular_total_detalles(
            db, empresa_actual.id, venta.detalles, tipo_cliente
        )
        if abs(total_calculado - total_venta) > Decimal("0.05"):
            total_venta = total_calculado

    if es_borrador:
        estado_inicial = EstadoVenta.BORRADOR
    elif frecuencia == FrecuenciaPago.CONTADO:
        if metodo in ("transferencia", "pago_movil") and not rol_confirma_pago(vendedor_actual):
            estado_inicial = EstadoVenta.POR_VERIFICAR
        else:
            estado_inicial = EstadoVenta.PAGADA
    else:
        estado_inicial = EstadoVenta.PENDIENTE

    from app.core.pb_orm.ids import id_pocketbase_desde_cualquiera, nuevo_id_pocketbase

    venta_id = id_pocketbase_desde_cualquiera(venta.id) if venta.id else nuevo_id_pocketbase()
    nueva_venta = Venta(
        id=venta_id,
        empresa_id=empresa_actual.id,
        cliente_id=cliente_actual.id,
        vendedor_id=vendedor_actual.id,
        fecha=datetime.utcnow(),
        total_usd=total_venta,
        tasa_usd_aplicada=venta.tasa_usd_aplicada,
        tasa_eur_aplicada=venta.tasa_eur_aplicada,
        tipo_tasa_usd=tipo_tasa,
        numero_cuotas=venta.numero_cuotas,
        frecuencia_pago=frecuencia,
        estado=estado_inicial,
        metodo_pago=metodo,
        referencia_pago=(venta.referencia_pago or "").strip() or None,
        comprobante_base64=venta.comprobante_base64,
        cuenta_bancaria_id=cuenta_destino.id if cuenta_destino else None,
    )

    db.add(nueva_venta)
    db.flush()

    if venta.detalles:
        procesar_detalles_venta(
            db,
            nueva_venta,
            venta.detalles,
            venta.almacen_id,
            tipo_cliente,
            descontar_inventario=not es_borrador,
        )

    if frecuencia != FrecuenciaPago.CONTADO and not es_borrador:
        generar_plan_amortizacion(db, nueva_venta, venta.numero_cuotas)

    if not es_borrador:
        generar_asiento_venta(db, nueva_venta)
        actualizar_historial_comportamiento(db, cliente_actual)
        registrar_evento_buro(
            db,
            cliente_actual.identificacion,
            "compra",
            (
                f"Compra registrada por ${float(total_venta):.2f}. "
                f"Compras: {cliente_actual.total_compras}. "
                f"Pagos: {cliente_actual.total_pagos}. "
                f"Crédito: {cliente_actual.clasificacion_credito}."
            ),
        )

    db.commit()
    db.refresh(nueva_venta)
    venta_final = (
        db.query(Venta)
        .options(
            joinedload(Venta.detalles),
            joinedload(Venta.cuotas),
            joinedload(Venta.cliente),
            joinedload(Venta.cobros),
        )
        .filter(Venta.id == nueva_venta.id)
        .first()
    )
    if not es_borrador and venta_final:
        try:
            enviar_recibo_venta(db, venta_final)
        except Exception:
            logger.exception("No se pudo enviar comprobante de venta por correo")
    return _venta_a_response(db, venta_final)


@router.post("/{venta_id}/aprobar", response_model=VentaResponse)
def aprobar_venta_borrador(
    venta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    venta = (
        db.query(Venta)
        .options(joinedload(Venta.detalles), joinedload(Venta.cliente))
        .filter(Venta.id == venta_id, Venta.empresa_id == usuario.empresa_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    if not puede_aprobar_venta(venta):
        raise HTTPException(status_code=400, detail="La venta no está en borrador")

    validar_venta_credito(venta.cliente, venta.frecuencia_pago)
    if (venta.metodo_pago or "efectivo") in ("transferencia", "pago_movil") and venta.frecuencia_pago == FrecuenciaPago.CONTADO:
        venta.estado = EstadoVenta.PAGADA
    else:
        venta.estado = EstadoVenta.PENDIENTE

    if venta.detalles:
        from app.services.inventario import descontar_stock
        for d in venta.detalles:
            descontar_stock(
                db, venta.empresa_id, d.producto_id, d.cantidad, None,
                referencia_tipo="venta", referencia_id=venta.id,
            )

    if venta.frecuencia_pago != FrecuenciaPago.CONTADO:
        generar_plan_amortizacion(db, venta, venta.numero_cuotas)

    generar_asiento_venta(db, venta)
    db.commit()
    venta_final = (
        db.query(Venta)
        .options(
            joinedload(Venta.detalles),
            joinedload(Venta.cuotas),
            joinedload(Venta.cliente),
            joinedload(Venta.cobros),
        )
        .filter(Venta.id == venta.id)
        .first()
    )
    if venta_final:
        try:
            enviar_recibo_venta(db, venta_final)
        except Exception:
            logger.exception("No se pudo enviar comprobante de venta por correo")
    return _venta_a_response(db, venta_final)


@router.post("/{venta_id}/verificar", response_model=VentaResponse)
def verificar_pago_transferencia(
    venta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    venta = (
        db.query(Venta)
        .options(
            joinedload(Venta.detalles),
            joinedload(Venta.cuotas),
            joinedload(Venta.cliente),
            joinedload(Venta.cobros),
        )
        .filter(Venta.id == venta_id, Venta.empresa_id == usuario.empresa_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    if venta.estado != EstadoVenta.POR_VERIFICAR:
        raise HTTPException(status_code=400, detail="La venta no está pendiente de verificación")

    for cobro in list(venta.cobros or []):
        if cobro.verificado is False and venta.frecuencia_pago != FrecuenciaPago.CONTADO:
            cobro.verificado = True
            if venta.cliente:
                actualizar_score_por_cobro(db, venta, cobro)
        else:
            cobro.verificado = True

    venta.estado = EstadoVenta.PAGADA
    if venta.cliente:
        actualizar_historial_comportamiento(db, venta.cliente)
    db.commit()
    db.refresh(venta)
    return _venta_a_response(db, venta)


@router.get("/{venta_id}/amortizacion", response_model=List[CuotaAmortizacionResponse])
def obtener_amortizacion(
    venta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_superior),
):
    venta = (
        db.query(Venta)
        .options(joinedload(Venta.cuotas))
        .filter(Venta.id == venta_id, Venta.empresa_id == usuario.empresa_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    frecuencia = venta.frecuencia_pago or FrecuenciaPago.CONTADO
    return [
        CuotaAmortizacionResponse(**serializar_cuota(c, frecuencia))
        for c in sorted(venta.cuotas, key=lambda x: x.numero_cuota)
    ]


@router.post("/{venta_id}/enviar-recibo", response_model=EnvioReciboResponse)
def enviar_recibo_venta_manual(
    venta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_superior),
):
    venta = (
        db.query(Venta)
        .options(
            joinedload(Venta.detalles),
            joinedload(Venta.cuotas),
            joinedload(Venta.cliente),
            joinedload(Venta.cobros),
        )
        .filter(Venta.id == venta_id, Venta.empresa_id == usuario.empresa_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    exito, mensaje = enviar_recibo_venta(db, venta)
    email = venta.cliente.email if venta.cliente else None
    if not exito:
        raise HTTPException(status_code=400, detail=mensaje)
    return EnvioReciboResponse(exito=exito, mensaje=mensaje, email=email)


@router.post("/{venta_id}/comprobante/whatsapp", response_model=WhatsappReporteResponse)
def enviar_comprobante_venta_whatsapp(
    venta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_superior),
):
    """Envía la foto del comprobante de la venta al WhatsApp del administrador."""
    venta = (
        db.query(Venta)
        .options(joinedload(Venta.cliente))
        .filter(Venta.id == venta_id, Venta.empresa_id == usuario.empresa_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    if venta.metodo_pago not in ("transferencia", "pago_movil"):
        raise HTTPException(
            status_code=400,
            detail="Esta venta no es por transferencia ni pago móvil",
        )
    if not venta.comprobante_base64:
        raise HTTPException(
            status_code=400,
            detail="Adjunte la foto del comprobante para enviarla por WhatsApp",
        )

    try:
        telefono = telefono_administrador(db, usuario.empresa_id)
        destino = normalizar_telefono(telefono)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    cliente = venta.cliente.nombre if venta.cliente else "Cliente"
    caption = armar_caption_comprobante(
        cliente,
        f"${float(venta.total_usd):.2f} USD",
        venta.referencia_pago,
        venta.metodo_pago,
    )
    ok, mensaje = enviar_imagen(
        destino,
        None,
        caption,
        imagen_base64=venta.comprobante_base64,
    )
    if not ok:
        raise HTTPException(status_code=estado_http_whatsapp(mensaje), detail=mensaje)
    return WhatsappReporteResponse(enviado=True, telefono=destino, mensaje=mensaje)


@router.post("/{venta_id}/recibo/whatsapp", response_model=WhatsappReporteResponse)
def enviar_recibo_venta_por_whatsapp(
    venta_id: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_superior),
):
    """Si el cliente no tiene correo, el recibo sale por WhatsApp a su teléfono."""
    candidatas = (
        db.query(Venta)
        .options(
            joinedload(Venta.detalles),
            joinedload(Venta.cliente),
            joinedload(Venta.cobros),
        )
        .filter(Venta.id == venta_id, Venta.empresa_id == usuario.empresa_id)
        .all()
    )
    venta = next((v for v in candidatas if str(v.id) == str(venta_id)), None)
    if not venta or str(venta.empresa_id) != str(usuario.empresa_id):
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    telefono = (venta.cliente.telefono or "").strip() if venta.cliente else ""
    if not telefono:
        raise HTTPException(
            status_code=400,
            detail="El cliente no tiene teléfono para enviar el recibo por WhatsApp",
        )
    ok, mensaje = enviar_texto(telefono, texto_recibo_venta(db, venta))
    if not ok:
        raise HTTPException(status_code=400, detail=mensaje)
    try:
        destino = normalizar_telefono(telefono)
    except ValueError:
        destino = telefono
    return WhatsappReporteResponse(enviado=True, telefono=destino, mensaje=mensaje)


def _opciones_venta():
    return (
        joinedload(Venta.detalles),
        joinedload(Venta.cuotas),
        joinedload(Venta.cliente),
        joinedload(Venta.cobros),
    )


@router.get("/mis-ventas", response_model=List[VentaResponse])
def listar_mis_ventas(
    q: Optional[str] = Query(default=None, description="Nombre o teléfono del cliente"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_superior),
):
    consulta = (
        db.query(Venta)
        .filter(Venta.empresa_id == usuario.empresa_id)
        .options(*_opciones_venta())
    )
    if usuario.rol == RolUsuario.VENDEDOR:
        consulta = consulta.filter(Venta.vendedor_id == usuario.id)
    ventas = [
        v for v in consulta.order_by(Venta.fecha.desc()).all()
        if str(v.empresa_id) == str(usuario.empresa_id)
    ]
    if usuario.rol == RolUsuario.VENDEDOR:
        ventas = [v for v in ventas if str(v.vendedor_id) == str(usuario.id)]
    return [_venta_a_response(db, v) for v in _filtrar_por_cliente(ventas, q)]


@router.get("/", response_model=List[VentaResponse])
def listar_ventas(
    q: Optional[str] = Query(default=None, description="Nombre o teléfono del cliente"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    ventas = [
        v
        for v in (
            db.query(Venta)
            .filter(Venta.empresa_id == usuario.empresa_id)
            .options(*_opciones_venta())
            .order_by(Venta.fecha.desc())
            .all()
        )
        if str(v.empresa_id) == str(usuario.empresa_id)
    ]
    return [_venta_a_response(db, v) for v in _filtrar_por_cliente(ventas, q)]


@router.get("/{venta_id}", response_model=VentaResponse)
def obtener_venta(
    venta_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_superior),
):
    venta = (
        db.query(Venta)
        .options(joinedload(Venta.detalles), joinedload(Venta.cuotas))
        .filter(Venta.id == venta_id, Venta.empresa_id == usuario.empresa_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return _venta_a_response(db, venta)
