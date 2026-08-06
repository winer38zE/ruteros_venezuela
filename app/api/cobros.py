from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import obtener_usuario_opcional, require_cobrador_o_dueno
from app.models.core import (
    Cobro, Cliente, Empresa, Venta, Usuario,
    MonedaPago, EstadoVenta, RolUsuario,
)
from app.schemas.core import CobroCreate, CobroResponse, VentaPendienteResponse
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid
from app.services.contabilidad import generar_asiento_cobro

router = APIRouter()


def _actualizar_estado_venta(db: Session, venta: Venta) -> None:
    total_cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
    total_venta = Decimal(str(venta.total_usd))

    if total_cobrado >= total_venta:
        venta.estado = EstadoVenta.PAGADA
    elif total_cobrado > 0:
        venta.estado = EstadoVenta.PARCIAL
    else:
        venta.estado = EstadoVenta.PENDIENTE


def _resolver_cobrador(
    db: Session,
    empresa_id,
    cobrador_id=None,
    usuario_header: Optional[Usuario] = None,
) -> Usuario:
    if usuario_header:
        if usuario_header.empresa_id != empresa_id:
            raise HTTPException(status_code=400, detail="Usuario no pertenece a la empresa")
        if usuario_header.rol not in (RolUsuario.COBRADOR, RolUsuario.DUENO):
            raise HTTPException(status_code=403, detail="Solo COBRADOR o DUEÑO puede registrar cobros")
        return usuario_header

    if cobrador_id:
        cobrador = (
            db.query(Usuario)
            .filter(Usuario.id == cobrador_id, Usuario.empresa_id == empresa_id)
            .first()
        )
        if not cobrador:
            raise HTTPException(status_code=400, detail="El cobrador indicado no existe")
        return cobrador

    cobrador = (
        db.query(Usuario)
        .filter(Usuario.empresa_id == empresa_id, Usuario.rol == RolUsuario.COBRADOR)
        .first()
    )
    if not cobrador:
        cobrador = db.query(Usuario).filter(Usuario.empresa_id == empresa_id).first()
    if not cobrador:
        raise HTTPException(status_code=400, detail="Debes crear al menos un cobrador")
    return cobrador


@router.get("/ventas-pendientes", response_model=List[VentaPendienteResponse])
def listar_ventas_pendientes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_dueno),
):
    ventas = (
        db.query(Venta)
        .options(joinedload(Venta.cobros), joinedload(Venta.cliente))
        .filter(
            Venta.empresa_id == usuario.empresa_id,
            Venta.estado.in_([EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL]),
        )
        .order_by(Venta.fecha.desc())
        .all()
    )
    resultado = []
    for v in ventas:
        cobrado = sum(Decimal(str(c.monto_usd)) for c in v.cobros)
        saldo = Decimal(str(v.total_usd)) - cobrado
        if saldo > 0:
            cliente_nombre = v.cliente.nombre if v.cliente else "—"
            resultado.append(
                VentaPendienteResponse(
                    id=v.id,
                    cliente_id=v.cliente_id,
                    cliente_nombre=cliente_nombre,
                    total_usd=float(v.total_usd),
                    cobrado_usd=float(cobrado),
                    saldo_pendiente_usd=float(saldo),
                    estado=v.estado.value,
                )
            )
    return resultado


@router.get("/mis-cobros", response_model=List[CobroResponse])
def listar_mis_cobros(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_dueno),
):
    q = db.query(Cobro).filter(Cobro.empresa_id == usuario.empresa_id)
    if usuario.rol == RolUsuario.COBRADOR:
        q = q.filter(Cobro.cobrador_id == usuario.id)
    return q.order_by(Cobro.fecha.desc()).all()


@router.post("/", response_model=CobroResponse)
def registrar_cobro(
    cobro: CobroCreate,
    db: Session = Depends(get_db),
    usuario_header: Optional[Usuario] = Depends(obtener_usuario_opcional),
):
    empresa_actual = db.query(Empresa).first()
    if not empresa_actual:
        raise HTTPException(status_code=400, detail="Debes crear una empresa primero")

    venta = db.query(Venta).filter(Venta.id == cobro.venta_id).first()
    if not venta:
        raise HTTPException(status_code=400, detail="La venta indicada no existe")
    if venta.empresa_id != empresa_actual.id:
        raise HTTPException(status_code=400, detail="La venta no pertenece a la empresa actual")

    cobrador = _resolver_cobrador(
        db, empresa_actual.id, cobro.cobrador_id, usuario_header
    )

    # Validar que no se cobre más del saldo pendiente
    db.refresh(venta)
    cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
    saldo = Decimal(str(venta.total_usd)) - cobrado
    monto = Decimal(str(cobro.monto_usd))
    if monto > saldo + Decimal("0.01"):
        raise HTTPException(
            status_code=400,
            detail=f"Monto excede saldo pendiente (${float(saldo):.2f})",
        )

    try:
        moneda = MonedaPago(cobro.moneda_pago)
    except ValueError:
        raise HTTPException(status_code=400, detail="Moneda de pago inválida")

    cobro_id = uuid.UUID(cobro.id) if cobro.id else uuid.uuid4()

    nuevo_cobro = Cobro(
        id=cobro_id,
        empresa_id=empresa_actual.id,
        venta_id=venta.id,
        cobrador_id=cobrador.id,
        fecha=cobro.fecha or datetime.utcnow(),
        monto_usd=cobro.monto_usd,
        moneda_pago=moneda,
        tasa_usd_aplicada=cobro.tasa_usd_aplicada,
        tasa_eur_aplicada=cobro.tasa_eur_aplicada,
    )

    db.add(nuevo_cobro)
    db.flush()
    db.refresh(venta)
    _actualizar_estado_venta(db, venta)
    generar_asiento_cobro(db, nuevo_cobro)
    db.commit()
    db.refresh(nuevo_cobro)

    return nuevo_cobro


@router.get("/", response_model=List[CobroResponse])
def listar_cobros(db: Session = Depends(get_db)):
    return db.query(Cobro).all()
