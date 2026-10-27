"""Pago de nómina flexible por empleado (Venezuela / Colombia)."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.db import get_db
from app.core.deps import require_dueno
from app.models.core import PagoEmpleadoNomina, Usuario
from app.schemas.core import (
    NominaCalcularRequest,
    NominaCalcularResponse,
    NominaPagoEmpleadoResponse,
    NominaProcesarRequest,
    TasasNominaResponse,
)
from app.services.nomina_pago import calcular_nomina, obtener_tasas_nomina, procesar_pago_nomina

logger = logging.getLogger(__name__)

router = APIRouter()


def _serializar_pago(p: PagoEmpleadoNomina, nombre: str) -> NominaPagoEmpleadoResponse:
    estado = p.estado.value if hasattr(p.estado, "value") else str(p.estado)
    return NominaPagoEmpleadoResponse(
        id=str(p.id),
        usuario_id=str(p.usuario_id),
        empleado_nombre=nombre,
        pais=p.pais,
        moneda_principal=p.moneda_principal,
        tipo_pago=p.tipo_pago,
        fecha_pago=p.fecha_pago,
        salario_base=float(p.salario_base),
        total_comisiones=float(p.total_comisiones),
        total_bonos=float(p.total_bonos),
        total_pagar_usd=float(p.total_pagar_usd),
        total_pagar_local=float(p.total_pagar_local),
        tasa_cambio_aplicada=float(p.tasa_cambio_aplicada) if p.tasa_cambio_aplicada else None,
        detalles_pago=p.detalles_pago,
        estado=estado,
        movimiento_financiero_id=str(p.movimiento_financiero_id) if p.movimiento_financiero_id else None,
        notas=p.notas,
        fecha_creacion=p.fecha_creacion,
    )


@router.get("/tasas", response_model=TasasNominaResponse)
def tasas_nomina(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    t = obtener_tasas_nomina(db, dueno.empresa_id)
    return TasasNominaResponse(
        USD_TO_VES=float(t.get("USD_TO_VES", 0)),
        USD_TO_COP=float(t.get("USD_TO_COP", 0)),
        origen=str(t.get("origen", "defecto")),
        fecha_referencia=str(t.get("fecha_referencia")) if t.get("fecha_referencia") else None,
    )


@router.post("/calcular", response_model=NominaCalcularResponse)
def calcular_nomina_endpoint(
    body: NominaCalcularRequest,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    try:
        return calcular_nomina(
            db,
            dueno.empresa_id,
            usuario_id=str(body.usuario_id),
            pais=body.pais,
            tipo_pago=body.tipo_pago,
            fecha_pago=body.fecha_pago,
            salario_base=body.salario_base,
            total_bonos=body.total_bonos,
            porcentaje_cobro=body.porcentaje_cobro,
            detalles_pago=body.detalles_pago,
            datos_extra=body.datos_extra,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Error calculando nómina usuario=%s", body.usuario_id)
        raise HTTPException(
            status_code=400,
            detail="No se pudo calcular la nómina. Verifica los datos.",
        ) from exc


@router.post("/procesar", response_model=NominaPagoEmpleadoResponse)
def procesar_nomina_endpoint(
    body: NominaProcesarRequest,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    try:
        payload = body.model_dump(exclude_none=True)
        registro = procesar_pago_nomina(db, dueno.empresa_id, dueno.id, payload)
        db.commit()
        db.refresh(registro)
        emp = db.query(Usuario).filter(Usuario.id == registro.usuario_id).first()
        nombre = emp.nombre if emp else "Empleado"
        return _serializar_pago(registro, nombre)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Error procesando nómina usuario=%s", body.usuario_id)
        raise HTTPException(
            status_code=400,
            detail="No se pudo registrar el pago de nómina. Verifica los datos.",
        ) from exc


@router.get("/historial", response_model=list[NominaPagoEmpleadoResponse])
def historial_pagos_nomina(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
    limite: int = 50,
):
    limite = min(max(limite, 1), 200)
    filas = (
        db.query(PagoEmpleadoNomina)
        .options(joinedload(PagoEmpleadoNomina.usuario))
        .filter(PagoEmpleadoNomina.empresa_id == dueno.empresa_id)
        .order_by(PagoEmpleadoNomina.fecha_pago.desc(), PagoEmpleadoNomina.fecha_creacion.desc())
        .limit(limite)
        .all()
    )
    out: list[NominaPagoEmpleadoResponse] = []
    for p in filas:
        nombre = p.usuario.nombre if p.usuario else "Empleado"
        out.append(_serializar_pago(p, nombre))
    return out
