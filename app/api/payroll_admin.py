"""Panel dueño: países (catálogo) y reglas de nómina por año."""
from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import require_dueno
from app.core.db import get_db
from app.models.core import Pais, PayrollRule
from app.schemas.core import (
    CountryAdminResponse,
    CountryAdminUpdate,
    PayrollRuleResponse,
    PayrollRuleUpdate,
)
from app.services.payroll_rules import aplicar_regla_a_pais, payment_currencies_for_pais

router = APIRouter()


def _serializar_pais(p: Pais) -> dict:
    return {
        "id": str(p.id),
        "nombre": p.nombre,
        "codigo_iso": p.codigo_iso,
        "bandera": p.bandera,
        "moneda_principal": p.moneda_principal,
        "simbolo_moneda": p.simbolo_moneda,
        "formato_numero": p.formato_numero,
        "formato_fecha": p.formato_fecha,
        "zona_horaria": p.zona_horaria,
        "prefijo_telefonico": p.prefijo_telefonico,
        "activo": bool(p.activo),
        "payment_currencies": payment_currencies_for_pais(p),
        "tasas_cambio_referencia": p.tasas_cambio_referencia,
    }


@router.get("/countries", response_model=list[CountryAdminResponse])
def listar_paises_admin(
    db: Session = Depends(get_db),
    _: object = Depends(require_dueno),
):
    return [
        _serializar_pais(p)
        for p in db.query(Pais).order_by(Pais.nombre.asc()).all()
    ]


@router.patch("/countries/{pais_id}", response_model=CountryAdminResponse)
def actualizar_pais_admin(
    pais_id: str,
    body: CountryAdminUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_dueno),
):
    pais = db.query(Pais).filter(Pais.id == pais_id).first()
    if pais is None:
        raise HTTPException(status_code=404, detail="País no encontrado")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(pais, k, v)
    db.commit()
    db.refresh(pais)
    return _serializar_pais(pais)


@router.get("/payroll-rules", response_model=list[PayrollRuleResponse])
def listar_reglas_nomina(
    year: int | None = None,
    pais_id: str | None = None,
    db: Session = Depends(get_db),
    _: object = Depends(require_dueno),
):
    q = db.query(PayrollRule).order_by(
        PayrollRule.year.desc(),
        PayrollRule.effective_from.desc(),
    )
    if year is not None:
        q = q.filter(PayrollRule.year == year)
    if pais_id:
        q = q.filter(PayrollRule.pais_id == pais_id)
    return [_serializar_regla(r) for r in q.all()]


def _serializar_regla(r: PayrollRule) -> dict:
    return {
        "id": str(r.id),
        "pais_id": str(r.pais_id),
        "year": r.year,
        "effective_from": r.effective_from.isoformat(),
        "salario_minimo_mensual": float(r.salario_minimo_mensual or 0),
        "moneda_salario": r.moneda_salario,
        "auxilio_transporte": float(r.auxilio_transporte)
        if r.auxilio_transporte is not None
        else None,
        "aportes_empleado": r.aportes_empleado,
        "aportes_empleador": r.aportes_empleador,
        "prestaciones": r.prestaciones,
        "jornada_max_horas_semanales": r.jornada_max_horas_semanales,
        "recargos": r.recargos,
        "porcentaje_comision_venta": float(r.porcentaje_comision_venta or 0),
        "porcentaje_comision_cobro": float(r.porcentaje_comision_cobro or 0),
        "bono_incentivo": float(r.bono_incentivo or 0),
        "payment_currencies": r.payment_currencies,
        "source_url": r.source_url,
        "verified": bool(r.verified),
        "borrador": bool(r.borrador),
    }


@router.put("/payroll-rules/{regla_id}", response_model=PayrollRuleResponse)
def actualizar_regla_nomina(
    regla_id: str,
    body: PayrollRuleUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_dueno),
):
    regla = db.query(PayrollRule).filter(PayrollRule.id == regla_id).first()
    if regla is None:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    data = body.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(regla, k, v)
    pais = db.query(Pais).filter(Pais.id == regla.pais_id).first()
    if pais is not None and not regla.borrador:
        if str(regla.moneda_salario).upper() == str(pais.moneda_principal).upper():
            aplicar_regla_a_pais(pais, regla)
    db.commit()
    db.refresh(regla)
    return _serializar_regla(regla)


@router.post("/payroll-rules/duplicar-anio", response_model=list[PayrollRuleResponse])
def duplicar_reglas_anio_nuevo(
    desde_year: int = Query(..., ge=2000),
    hacia_year: int = Query(..., ge=2000),
    db: Session = Depends(get_db),
    _: object = Depends(require_dueno),
):
    if hacia_year <= desde_year:
        raise HTTPException(
            status_code=400,
            detail="El año destino debe ser posterior al origen.",
        )
    origen = (
        db.query(PayrollRule)
        .filter(PayrollRule.year == desde_year, PayrollRule.borrador.is_(False))
        .all()
    )
    if not origen:
        raise HTTPException(status_code=404, detail="No hay reglas en el año origen.")
    creadas: list[PayrollRule] = []
    for r in origen:
        existe = (
            db.query(PayrollRule)
            .filter(
                PayrollRule.pais_id == r.pais_id,
                PayrollRule.year == hacia_year,
                PayrollRule.effective_from == date(hacia_year, 1, 1),
                PayrollRule.moneda_salario == r.moneda_salario,
            )
            .first()
        )
        if existe:
            continue
        copia = PayrollRule(
            pais_id=r.pais_id,
            year=hacia_year,
            effective_from=date(hacia_year, 1, 1),
            salario_minimo_mensual=r.salario_minimo_mensual,
            moneda_salario=r.moneda_salario,
            auxilio_transporte=r.auxilio_transporte,
            aportes_empleado=r.aportes_empleado,
            aportes_empleador=r.aportes_empleador,
            prestaciones=r.prestaciones,
            jornada_max_horas_semanales=r.jornada_max_horas_semanales,
            recargos=r.recargos,
            porcentaje_comision_venta=r.porcentaje_comision_venta,
            porcentaje_comision_cobro=r.porcentaje_comision_cobro,
            bono_incentivo=r.bono_incentivo,
            payment_currencies=r.payment_currencies,
            tasas_cambio_referencia=r.tasas_cambio_referencia,
            source_url=r.source_url,
            verified=False,
            borrador=True,
        )
        db.add(copia)
        creadas.append(copia)
    db.commit()
    for c in creadas:
        db.refresh(c)
    return [_serializar_regla(c) for c in creadas]
