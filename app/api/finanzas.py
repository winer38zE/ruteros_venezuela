from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import require_dueno
from app.models.core import MovimientoFinanciero, Usuario
from app.schemas.core import (
    ConfiguracionNominaUpdate,
    ConfiguracionNominaResponse,
    MovimientoFinancieroCreate,
    MovimientoFinancieroResponse,
    ResumenFinancieroResponse,
    NominaCalculadaResponse,
    AprobarPagoNominaRequest,
)
from app.services.finanzas import (
    _obtener_config_nomina,
    calcular_resumen_financiero,
    calcular_nomina,
    registrar_movimiento,
    aprobar_pago_nomina,
)

router = APIRouter()


@router.get("/resumen", response_model=ResumenFinancieroResponse)
def resumen_financiero(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
):
    return calcular_resumen_financiero(db, dueno.empresa_id, fecha_desde, fecha_hasta)


@router.get("/movimientos", response_model=List[MovimientoFinancieroResponse])
def listar_movimientos(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
):
    q = db.query(MovimientoFinanciero).filter(
        MovimientoFinanciero.empresa_id == dueno.empresa_id
    )
    if fecha_desde:
        q = q.filter(MovimientoFinanciero.fecha >= fecha_desde)
    if fecha_hasta:
        q = q.filter(MovimientoFinanciero.fecha <= fecha_hasta)
    return q.order_by(MovimientoFinanciero.fecha.desc()).all()


@router.post("/movimientos", response_model=MovimientoFinancieroResponse)
def crear_movimiento(
    body: MovimientoFinancieroCreate,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    mov = registrar_movimiento(
        db,
        dueno.empresa_id,
        dueno.id,
        body.model_dump(),
    )
    db.commit()
    db.refresh(mov)
    return mov


@router.get("/nomina/config", response_model=ConfiguracionNominaResponse)
def obtener_config_nomina(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    cfg = _obtener_config_nomina(db, dueno.empresa_id)
    db.commit()
    return cfg


@router.put("/nomina/config", response_model=ConfiguracionNominaResponse)
def actualizar_config_nomina(
    body: ConfiguracionNominaUpdate,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    cfg = _obtener_config_nomina(db, dueno.empresa_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(cfg, field, value)
    db.commit()
    db.refresh(cfg)
    return cfg


@router.get("/nomina/calcular", response_model=NominaCalculadaResponse)
def calcular_nomina_endpoint(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
    fecha_desde: Optional[datetime] = Query(None),
    fecha_hasta: Optional[datetime] = Query(None),
):
    return calcular_nomina(db, dueno.empresa_id, fecha_desde, fecha_hasta)


@router.post("/nomina/aprobar-pago", response_model=MovimientoFinancieroResponse)
def aprobar_pago(
    body: AprobarPagoNominaRequest,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    try:
        mov = aprobar_pago_nomina(
            db,
            dueno.empresa_id,
            dueno.id,
            body.empleado_id,
            body.monto_usd,
            body.periodo_desde,
            body.periodo_hasta,
            body.descripcion,
        )
        db.commit()
        db.refresh(mov)
        return mov
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
