from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import obtener_usuario_opcional, require_vendedor_o_superior, require_operaciones
from app.core.tenant import obtener_empresa_tenant
from app.models.core import (
    Venta, Cliente, Usuario, FrecuenciaPago, EstadoVenta, TipoCliente,
    RolUsuario, TipoTasaUsd, Producto, DetalleVenta,
)
from app.schemas.core import VentaCreate, VentaResponse, CuotaAmortizacionResponse
from app.services.contabilidad import generar_asiento_venta
from app.services.inventario import procesar_detalles_venta, calcular_total_detalles
from app.services.buro_credito import validar_venta_credito
from app.services.amortizacion import generar_plan_amortizacion, puede_aprobar_venta
from datetime import datetime
from typing import List, Optional
import uuid

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


def _venta_a_response(venta: Venta) -> VentaResponse:
    return VentaResponse(
        id=venta.id,
        empresa_id=venta.empresa_id,
        cliente_id=venta.cliente_id,
        vendedor_id=venta.vendedor_id,
        total_usd=float(venta.total_usd),
        estado=venta.estado.value,
        frecuencia_pago=venta.frecuencia_pago.value,
        tipo_tasa_usd=venta.tipo_tasa_usd.value if venta.tipo_tasa_usd else "bcv",
        numero_cuotas=venta.numero_cuotas,
        detalles=venta.detalles or [],
        cuotas=venta.cuotas or [],
    )


@router.post("/", response_model=VentaResponse)
def crear_venta(
    venta: VentaCreate,
    db: Session = Depends(get_db),
    usuario_header: Optional[Usuario] = Depends(obtener_usuario_opcional),
):
    empresa_actual = obtener_empresa_tenant(db)
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

    if not es_borrador:
        validar_venta_credito(cliente_actual, frecuencia)

    tipo_cliente = cliente_actual.tipo_cliente or TipoCliente.DETAL
    total_venta = Decimal(str(venta.total_usd))

    if venta.detalles:
        total_calculado = calcular_total_detalles(
            db, empresa_actual.id, venta.detalles, tipo_cliente
        )
        if abs(total_calculado - total_venta) > Decimal("0.05"):
            total_venta = total_calculado

    if frecuencia == FrecuenciaPago.CONTADO:
        estado_inicial = EstadoVenta.PAGADA
    elif es_borrador:
        estado_inicial = EstadoVenta.BORRADOR
    else:
        estado_inicial = EstadoVenta.PENDIENTE

    venta_id = uuid.UUID(venta.id) if venta.id else uuid.uuid4()
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

    db.commit()
    db.refresh(nueva_venta)
    return _venta_a_response(
        db.query(Venta)
        .options(joinedload(Venta.detalles), joinedload(Venta.cuotas))
        .filter(Venta.id == nueva_venta.id)
        .first()
    )


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
    db.refresh(venta)
    return _venta_a_response(venta)


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
    return sorted(venta.cuotas, key=lambda c: c.numero_cuota)


@router.get("/mis-ventas", response_model=List[VentaResponse])
def listar_mis_ventas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_superior),
):
    q = (
        db.query(Venta)
        .filter(Venta.empresa_id == usuario.empresa_id)
        .options(joinedload(Venta.detalles), joinedload(Venta.cuotas))
    )
    if usuario.rol == RolUsuario.VENDEDOR:
        q = q.filter(Venta.vendedor_id == usuario.id)
    ventas = q.order_by(Venta.fecha.desc()).all()
    return [_venta_a_response(v) for v in ventas]


@router.get("/", response_model=List[VentaResponse])
def listar_ventas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    ventas = (
        db.query(Venta)
        .filter(Venta.empresa_id == usuario.empresa_id)
        .options(joinedload(Venta.detalles), joinedload(Venta.cuotas))
        .order_by(Venta.fecha.desc())
        .all()
    )
    return [_venta_a_response(v) for v in ventas]


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
    return _venta_a_response(venta)
