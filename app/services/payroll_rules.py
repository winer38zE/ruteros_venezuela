"""Resolución de reglas de nómina por país y año."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.models.core import Pais, PayrollRule


def _d(val) -> Decimal:
    if val is None:
        return Decimal("0")
    return Decimal(str(val))


def payment_currencies_for_pais(pais: Pais) -> list[str]:
    raw = getattr(pais, "payment_currencies", None)
    if isinstance(raw, list) and raw:
        return [str(c).upper() for c in raw]
    return [str(pais.moneda_principal).upper()]


def regla_vigente(
    db: Session,
    pais_id,
    ref: date | None = None,
    *,
    moneda_preferida: str | None = None,
) -> PayrollRule | None:
    """Regla más reciente con effective_from <= ref para el año de ref."""
    if not pais_id:
        return None
    ref = ref or date.today()
    year = ref.year
    q = (
        db.query(PayrollRule)
        .filter(
            PayrollRule.pais_id == pais_id,
            PayrollRule.year == year,
            PayrollRule.effective_from <= ref,
            PayrollRule.borrador.is_(False),
        )
        .order_by(PayrollRule.effective_from.desc())
    )
    if moneda_preferida:
        mon = moneda_preferida.strip().upper()
        q = q.filter(PayrollRule.moneda_salario == mon)
    regla = q.first()
    if regla is not None:
        return regla
    if moneda_preferida:
        return None
    return (
        db.query(PayrollRule)
        .filter(
            PayrollRule.pais_id == pais_id,
            PayrollRule.year == year,
            PayrollRule.effective_from <= ref,
            PayrollRule.borrador.is_(False),
        )
        .order_by(PayrollRule.effective_from.desc())
        .first()
    )


def reglas_por_moneda(
    db: Session,
    pais_id,
    ref: date | None = None,
) -> dict[str, PayrollRule]:
    ref = ref or date.today()
    year = ref.year
    filas = (
        db.query(PayrollRule)
        .filter(
            PayrollRule.pais_id == pais_id,
            PayrollRule.year == year,
            PayrollRule.effective_from <= ref,
            PayrollRule.borrador.is_(False),
        )
        .order_by(PayrollRule.effective_from.desc())
        .all()
    )
    out: dict[str, PayrollRule] = {}
    for r in filas:
        mon = str(r.moneda_salario).upper()
        if mon not in out:
            out[mon] = r
    return out


def aplicar_regla_a_pais(pais: Pais, regla: PayrollRule) -> None:
    """Mantiene columnas legacy en ``paises`` alineadas con la regla principal."""
    pais.sueldo_base_legal = regla.salario_minimo_mensual
    pais.porcentaje_comision_venta = regla.porcentaje_comision_venta
    pais.porcentaje_comision_cobro = regla.porcentaje_comision_cobro
    pais.bono_incentivo = regla.bono_incentivo
    if regla.payment_currencies:
        pais.payment_currencies = regla.payment_currencies
    if regla.tasas_cambio_referencia:
        pais.tasas_cambio_referencia = regla.tasas_cambio_referencia


def parametros_nomina_desde_reglas(
    db: Session,
    pais: Pais | None,
    ref: date | None = None,
) -> dict[str, Any]:
    if pais is None:
        return {
            "sueldo_base_legal": 0.0,
            "porcentaje_comision_venta": 0.0,
            "porcentaje_comision_cobro": 0.0,
            "bono_incentivo": 0.0,
            "moneda_salario": "USD",
            "salarios_por_moneda": {},
            "regla_verificada": False,
        }
    ref = ref or date.today()
    por_moneda = reglas_por_moneda(db, pais.id, ref)
    principal = payment_currencies_for_pais(pais)[0]
    regla = por_moneda.get(principal) or regla_vigente(db, pais.id, ref)
    if regla is None:
        return {
            "sueldo_base_legal": float(_d(pais.sueldo_base_legal)),
            "porcentaje_comision_venta": float(_d(pais.porcentaje_comision_venta)),
            "porcentaje_comision_cobro": float(_d(pais.porcentaje_comision_cobro)),
            "bono_incentivo": float(_d(pais.bono_incentivo)),
            "moneda_salario": principal,
            "salarios_por_moneda": {},
            "regla_verificada": False,
        }
    salarios = {
        mon: float(_d(r.salario_minimo_mensual)) for mon, r in por_moneda.items()
    }
    return {
        "sueldo_base_legal": float(_d(regla.salario_minimo_mensual)),
        "porcentaje_comision_venta": float(_d(regla.porcentaje_comision_venta)),
        "porcentaje_comision_cobro": float(_d(regla.porcentaje_comision_cobro)),
        "bono_incentivo": float(_d(regla.bono_incentivo)),
        "moneda_salario": str(regla.moneda_salario).upper(),
        "salarios_por_moneda": salarios,
        "regla_verificada": bool(regla.verified),
    }
