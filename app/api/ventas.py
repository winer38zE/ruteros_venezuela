from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import obtener_usuario_opcional, require_vendedor_o_dueno
from app.models.core import (
    Venta, Empresa, Cliente, Usuario, FrecuenciaPago, EstadoVenta, TipoCliente,
    RolUsuario,
)
from app.schemas.core import VentaCreate, VentaResponse
from app.services.contabilidad import generar_asiento_venta
from app.services.inventario import procesar_detalles_venta, calcular_total_detalles
from app.services.buro_credito import validar_venta_credito
from datetime import datetime
from typing import List, Optional
import uuid

router = APIRouter()


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
        if usuario_header.rol not in (RolUsuario.VENDEDOR, RolUsuario.DUENO):
            raise HTTPException(status_code=403, detail="Solo VENDEDOR o DUEÑO puede registrar ventas")
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


@router.post("/", response_model=VentaResponse)
def crear_venta(
    venta: VentaCreate,
    db: Session = Depends(get_db),
    usuario_header: Optional[Usuario] = Depends(obtener_usuario_opcional),
):
    empresa_actual = db.query(Empresa).first()
    if not empresa_actual:
        raise HTTPException(status_code=400, detail="Debes crear una empresa primero")

    cliente_actual = _resolver_cliente(db, empresa_actual.id, venta.cliente_id)
    vendedor_actual = _resolver_vendedor(db, empresa_actual.id, usuario_header)

    try:
        frecuencia = FrecuenciaPago(venta.frecuencia_pago)
    except ValueError:
        raise HTTPException(status_code=400, detail="Frecuencia de pago inválida")

    validar_venta_credito(cliente_actual, frecuencia)

    tipo_cliente = cliente_actual.tipo_cliente or TipoCliente.DETAL
    total_venta = Decimal(str(venta.total_usd))

    if venta.detalles:
        total_calculado = calcular_total_detalles(
            db, empresa_actual.id, venta.detalles, tipo_cliente
        )
        if abs(total_calculado - total_venta) > Decimal("0.05"):
            total_venta = total_calculado

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
        frecuencia_pago=frecuencia,
        estado=EstadoVenta.PENDIENTE,
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
        )

    generar_asiento_venta(db, nueva_venta)
    db.commit()
    db.refresh(nueva_venta)
    return nueva_venta


@router.get("/mis-ventas", response_model=List[VentaResponse])
def listar_mis_ventas(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_vendedor_o_dueno),
):
    q = (
        db.query(Venta)
        .filter(Venta.empresa_id == usuario.empresa_id)
        .options(joinedload(Venta.detalles))
    )
    if usuario.rol == RolUsuario.VENDEDOR:
        q = q.filter(Venta.vendedor_id == usuario.id)
    return q.order_by(Venta.fecha.desc()).all()


@router.get("/", response_model=List[VentaResponse])
def listar_ventas(db: Session = Depends(get_db)):
    return (
        db.query(Venta)
        .options(joinedload(Venta.detalles))
        .order_by(Venta.fecha.desc())
        .all()
    )


@router.get("/{venta_id}", response_model=VentaResponse)
def obtener_venta(venta_id: uuid.UUID, db: Session = Depends(get_db)):
    venta = (
        db.query(Venta)
        .options(joinedload(Venta.detalles))
        .filter(Venta.id == venta_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=400, detail="Venta no encontrada")
    return venta
