from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.core import (
    Cobro, Empresa, Venta, Usuario,
    MonedaPago, EstadoVenta,
)
from app.schemas.core import CobroCreate, CobroResponse
from typing import List
from datetime import datetime
from decimal import Decimal
import uuid

router = APIRouter()


def _actualizar_estado_venta(db: Session, venta: Venta) -> None:
    total_cobrado = sum(
        Decimal(str(c.monto_usd)) for c in venta.cobros
    )
    total_venta = Decimal(str(venta.total_usd))

    if total_cobrado >= total_venta:
        venta.estado = EstadoVenta.PAGADA
    elif total_cobrado > 0:
        venta.estado = EstadoVenta.PARCIAL
    else:
        venta.estado = EstadoVenta.PENDIENTE


@router.post("/", response_model=CobroResponse)
def registrar_cobro(cobro: CobroCreate, db: Session = Depends(get_db)):
    empresa_actual = db.query(Empresa).first()
    if not empresa_actual:
        raise HTTPException(status_code=400, detail="Debes crear una empresa primero")

    venta = db.query(Venta).filter(Venta.id == cobro.venta_id).first()
    if not venta:
        raise HTTPException(status_code=400, detail="La venta indicada no existe")
    if venta.empresa_id != empresa_actual.id:
        raise HTTPException(
            status_code=400,
            detail="La venta no pertenece a la empresa actual",
        )

    if cobro.cobrador_id:
        cobrador = (
            db.query(Usuario)
            .filter(
                Usuario.id == cobro.cobrador_id,
                Usuario.empresa_id == empresa_actual.id,
            )
            .first()
        )
        if not cobrador:
            raise HTTPException(status_code=400, detail="El cobrador indicado no existe")
    else:
        cobrador = db.query(Usuario).filter(
            Usuario.empresa_id == empresa_actual.id
        ).first()
        if not cobrador:
            raise HTTPException(
                status_code=400,
                detail="Debes crear al menos un usuario (cobrador) primero",
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
    db.commit()
    db.refresh(nuevo_cobro)

    return nuevo_cobro


@router.get("/", response_model=List[CobroResponse])
def listar_cobros(db: Session = Depends(get_db)):
    return db.query(Cobro).all()
