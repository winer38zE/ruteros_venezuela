"""Nómina lee salarios desde payroll_rules (incl. Venezuela USD/VES)."""
from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

from app.models.core import Pais, PayrollRule
from app.services.payroll_rules import parametros_nomina_desde_reglas, reglas_por_moneda


def _mock_db_con_reglas(reglas: list[PayrollRule]):
    db = MagicMock()
    db.query.return_value.filter.return_value.order_by.return_value.all.return_value = reglas
    db.query.return_value.filter.return_value.order_by.return_value.first.return_value = (
        reglas[0] if reglas else None
    )
    return db


def test_payroll_reglas_dual_venezuela():
    pais_id = uuid4()
    r_ves = PayrollRule(
        pais_id=pais_id,
        year=2026,
        effective_from=date(2026, 1, 1),
        salario_minimo_mensual=Decimal("130"),
        moneda_salario="VES",
        porcentaje_comision_venta=2,
        porcentaje_comision_cobro=5,
        verified=True,
    )
    r_usd = PayrollRule(
        pais_id=pais_id,
        year=2026,
        effective_from=date(2026, 1, 1),
        salario_minimo_mensual=Decimal("240"),
        moneda_salario="USD",
        porcentaje_comision_venta=2,
        porcentaje_comision_cobro=5,
        verified=False,
    )
    db = _mock_db_con_reglas([r_ves, r_usd])
    por_moneda = reglas_por_moneda(db, pais_id, date(2026, 6, 1))
    assert set(por_moneda.keys()) == {"VES", "USD"}
    assert float(por_moneda["VES"].salario_minimo_mensual) == 130.0
    assert float(por_moneda["USD"].salario_minimo_mensual) == 240.0


def test_parametros_nomina_colombia_desde_regla():
    pais = Pais(
        id=uuid4(),
        nombre="Colombia",
        codigo_iso="CO",
        moneda_principal="COP",
        simbolo_moneda="$",
        activo=True,
        configuracion_bancaria={},
        sueldo_base_legal=0,
    )
    regla = PayrollRule(
        pais_id=pais.id,
        year=2026,
        effective_from=date(2026, 1, 1),
        salario_minimo_mensual=Decimal("1750905"),
        moneda_salario="COP",
        porcentaje_comision_venta=Decimal("2.5"),
        porcentaje_comision_cobro=Decimal("3"),
        verified=True,
    )
    db = _mock_db_con_reglas([regla])
    params = parametros_nomina_desde_reglas(db, pais, date(2026, 3, 1))
    assert params["sueldo_base_legal"] == 1_750_905.0
    assert params["regla_verificada"] is True
    assert params["moneda_salario"] == "COP"


def test_parametros_nomina_sin_regla_usa_pais():
    pais = Pais(
        id=uuid4(),
        nombre="Test",
        codigo_iso="XX",
        moneda_principal="USD",
        simbolo_moneda="$",
        activo=True,
        configuracion_bancaria={},
        sueldo_base_legal=100,
        porcentaje_comision_venta=1,
        porcentaje_comision_cobro=2,
    )
    db = _mock_db_con_reglas([])
    params = parametros_nomina_desde_reglas(db, pais)
    assert params["sueldo_base_legal"] == 100.0
    assert params["porcentaje_comision_venta"] == 1.0
