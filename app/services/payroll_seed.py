"""Sembrado idempotente de reglas payroll_rules 2026."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.data.countries_catalog_meta import COUNTRY_META
from app.data.payroll_seed_2026 import PAYROLL_SEED_2026
from app.models.core import Pais, PayrollRule
from app.services.paises_seed import obtener_pais_por_iso
from app.services.payroll_rules import aplicar_regla_a_pais

logger = logging.getLogger(__name__)


def _clave_regla(pais_id, year: int, effective_from, moneda: str) -> tuple:
    return (str(pais_id), year, effective_from.isoformat(), moneda.upper())


def asegurar_meta_paises(db: Session) -> None:
    for iso, meta in COUNTRY_META.items():
        pais = obtener_pais_por_iso(db, iso)
        if pais is None:
            continue
        pais.bandera = meta.get("bandera")
        pais.prefijo_telefonico = meta.get("prefijo_telefonico")
        pais.formato_numero = meta.get("formato_numero")
        pais.formato_fecha = meta.get("formato_fecha")
        if meta.get("payment_currencies"):
            pais.payment_currencies = meta["payment_currencies"]
        if meta.get("tasas_cambio_referencia"):
            pais.tasas_cambio_referencia = meta["tasas_cambio_referencia"]
    db.flush()


def asegurar_payroll_rules_2026(db: Session) -> list[PayrollRule]:
    asegurar_meta_paises(db)
    existentes = {
        _clave_regla(r.pais_id, r.year, r.effective_from, r.moneda_salario): r
        for r in db.query(PayrollRule).filter(PayrollRule.year == 2026).all()
    }
    guardadas: list[PayrollRule] = []
    regla_principal_por_pais: dict[str, PayrollRule] = {}

    for entrada in PAYROLL_SEED_2026:
        iso = entrada["codigo_iso"].upper()
        pais = obtener_pais_por_iso(db, iso)
        if pais is None:
            logger.warning("Payroll seed: país %s no existe, se omite.", iso)
            continue
        moneda = str(entrada["moneda_salario"]).upper()
        clave = _clave_regla(pais.id, entrada["year"], entrada["effective_from"], moneda)
        regla = existentes.get(clave)
        if regla is None:
            regla = PayrollRule(
                pais_id=pais.id,
                year=entrada["year"],
                effective_from=entrada["effective_from"],
                moneda_salario=moneda,
            )
            db.add(regla)
            existentes[clave] = regla
        regla.salario_minimo_mensual = entrada["salario_minimo_mensual"]
        regla.auxilio_transporte = entrada.get("auxilio_transporte")
        regla.aportes_empleado = entrada.get("aportes_empleado")
        regla.aportes_empleador = entrada.get("aportes_empleador")
        regla.prestaciones = entrada.get("prestaciones")
        regla.jornada_max_horas_semanales = entrada.get("jornada_max_horas_semanales")
        regla.recargos = entrada.get("recargos")
        regla.porcentaje_comision_venta = entrada.get("porcentaje_comision_venta", 0)
        regla.porcentaje_comision_cobro = entrada.get("porcentaje_comision_cobro", 0)
        regla.bono_incentivo = entrada.get("bono_incentivo", 0)
        regla.payment_currencies = entrada.get("payment_currencies")
        regla.tasas_cambio_referencia = entrada.get("tasas_cambio_referencia")
        regla.source_url = entrada.get("source_url") or None
        regla.verified = bool(entrada.get("verified", False))
        regla.borrador = False
        guardadas.append(regla)

        if moneda == str(pais.moneda_principal).upper() or iso not in regla_principal_por_pais:
            prev = regla_principal_por_pais.get(iso)
            if prev is None or moneda == str(pais.moneda_principal).upper():
                regla_principal_por_pais[iso] = regla

    for iso, regla in regla_principal_por_pais.items():
        pais = regla.pais or obtener_pais_por_iso(db, iso)
        if pais is not None:
            aplicar_regla_a_pais(pais, regla)

    db.flush()
    logger.info("Payroll rules 2026: %d registro(s) sincronizado(s).", len(guardadas))
    return guardadas
