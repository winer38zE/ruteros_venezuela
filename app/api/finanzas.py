from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import require_dueno
from app.models.core import MovimientoFinanciero, PagoNomina, Usuario
from app.schemas.core import (
    ConfiguracionNominaUpdate,
    ConfiguracionNominaResponse,
    MovimientoFinancieroCreate,
    MovimientoFinancieroResponse,
    ResumenFinancieroResponse,
    NominaCalculadaResponse,
    AprobarPagoNominaRequest,
    PeriodoNominaResponse,
    PagoNominaResponse,
    GenerarCorteNominaRequest,
    MarcarPagoNominaRealizadoRequest,
)
from app.services.finanzas import (
    _obtener_config_nomina,
    calcular_resumen_financiero,
    calcular_nomina,
    registrar_movimiento,
    aprobar_pago_nomina,
)
from app.services.nomina import (
    generar_corte_nomina,
    marcar_pago_nomina_realizado,
    periodo_nomina_actual,
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


def _serializar_pago_nomina(p: PagoNomina) -> dict:
    nombre = p.usuario.nombre if p.usuario else ""
    rol = p.rol.value if hasattr(p.rol, "value") else str(p.rol)
    estado = p.estado.value if hasattr(p.estado, "value") else str(p.estado)
    return {
        "id": p.id,
        "empresa_id": p.empresa_id,
        "usuario_id": p.usuario_id,
        "empleado_nombre": nombre,
        "rol": rol,
        "periodo_desde": p.periodo_desde,
        "periodo_hasta": p.periodo_hasta,
        "num_ventas": p.num_ventas,
        "total_cobrado_usd": float(p.total_cobrado_usd),
        "sueldo_base_usd": float(p.sueldo_base_usd),
        "comision_usd": float(p.comision_usd),
        "total_calculado_usd": float(p.total_calculado_usd),
        "estado": estado,
        "movimiento_financiero_id": p.movimiento_financiero_id,
        "fecha_pago": p.fecha_pago,
        "notas": p.notas,
        "fecha_creacion": p.fecha_creacion,
    }


@router.get("/nomina/periodo-actual", response_model=PeriodoNominaResponse)
def periodo_actual_nomina(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    inicio, fin, cfg = periodo_nomina_actual(db, dueno.empresa_id)
    db.commit()
    return {
        "periodo_desde": inicio,
        "periodo_hasta": fin,
        "dias_periodo": int(cfg.dias_periodo_nomina or 8),
    }


@router.get("/nomina/cortes", response_model=List[PagoNominaResponse])
def listar_cortes_nomina(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    items = (
        db.query(PagoNomina)
        .options(joinedload(PagoNomina.usuario))
        .filter(PagoNomina.empresa_id == dueno.empresa_id)
        .order_by(PagoNomina.periodo_desde.desc(), PagoNomina.fecha_creacion.desc())
        .all()
    )
    return [_serializar_pago_nomina(p) for p in items]


@router.post("/nomina/generar-corte", response_model=List[PagoNominaResponse])
def generar_corte(
    body: GenerarCorteNominaRequest,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    pagos = generar_corte_nomina(
        db,
        dueno.empresa_id,
        body.periodo_desde,
        body.periodo_hasta,
    )
    db.commit()
    for p in pagos:
        db.refresh(p)
        if p.usuario is None:
            p.usuario = db.query(Usuario).filter(Usuario.id == p.usuario_id).first()
    return [_serializar_pago_nomina(p) for p in pagos]


@router.post("/nomina/cortes/{pago_id}/marcar-realizado", response_model=PagoNominaResponse)
def marcar_corte_realizado(
    pago_id: str,
    body: MarcarPagoNominaRealizadoRequest,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    try:
        pago = marcar_pago_nomina_realizado(
            db,
            dueno.empresa_id,
            dueno.id,
            pago_id,
            body.notas,
        )
        db.commit()
        db.refresh(pago)
        if pago.usuario is None:
            pago.usuario = db.query(Usuario).filter(Usuario.id == pago.usuario_id).first()
        return _serializar_pago_nomina(pago)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
