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


def _serializar_movimiento(m: MovimientoFinanciero) -> dict:
    return {
        "id": m.id,
        "empresa_id": m.empresa_id,
        "tipo": m.tipo.value if hasattr(m.tipo, "value") else m.tipo,
        "categoria": m.categoria.value if hasattr(m.categoria, "value") else m.categoria,
        "monto_usd": float(m.monto_usd),
        "monto_original": float(m.monto_original) if m.monto_original is not None else None,
        "moneda": m.moneda.value if m.moneda and hasattr(m.moneda, "value") else (m.moneda or "usd"),
        "metodo_pago": m.metodo_pago.value if m.metodo_pago and hasattr(m.metodo_pago, "value") else m.metodo_pago,
        "tasa_aplicada": float(m.tasa_aplicada) if m.tasa_aplicada is not None else None,
        "descripcion": m.descripcion,
        "fecha": m.fecha,
        "registrado_por_id": m.registrado_por_id,
        "empleado_id": m.empleado_id,
        "proveedor_id": m.proveedor_id,
        "tiene_comprobante": bool(m.comprobante_base64),
        "aprobado": m.aprobado,
        "fecha_creacion": m.fecha_creacion,
    }


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
    items = q.order_by(MovimientoFinanciero.fecha.desc()).all()
    return [_serializar_movimiento(m) for m in items]


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
    return _serializar_movimiento(mov)


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
        return _serializar_movimiento(mov)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
