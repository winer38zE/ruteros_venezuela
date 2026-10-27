"""Cálculo y registro de pagos de nómina por empleado (VE / CO)."""
from __future__ import annotations

import logging
from calendar import monthrange
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.data.tasas_nomina_defaults import (
    SALARIO_REFERENCIA_CO_COP,
    SALARIO_REFERENCIA_VE_USD,
    USD_TO_COP,
    USD_TO_VES_BCV,
    tasas_por_defecto,
)
from app.models.core import (
    EstadoPagoNomina,
    PagoEmpleadoNomina,
    Pais,
    RolUsuario,
    Usuario,
)
from app.services.finanzas import _obtener_config_nomina, aprobar_pago_nomina
from app.services.nomina import _rango_datetime, calcular_linea_empleado
from app.services.tasas_cambio import obtener_ultima_tasa

logger = logging.getLogger(__name__)

_TOLERANCIA_USD = Decimal("0.05")


def _d(val) -> Decimal:
    return Decimal(str(val or 0))


def _iso_pais(pais: str | None, pais_obj: Pais | None) -> str:
    if pais:
        return pais.strip().upper()[:2]
    if pais_obj and pais_obj.codigo_iso:
        return str(pais_obj.codigo_iso).upper()[:2]
    return "VE"


def _moneda_principal_pais(iso: str, pais_obj: Pais | None) -> str:
    if pais_obj and pais_obj.moneda_principal:
        return str(pais_obj.moneda_principal).upper()
    if iso == "CO":
        return "COP"
    if iso == "VE":
        return "VES"
    return "USD"


def obtener_tasas_nomina(db: Session, empresa_id) -> dict[str, float]:
    """Tasas del día (BD) con fallback a valores de referencia."""
    base = tasas_por_defecto()
    tasa = obtener_ultima_tasa(db, empresa_id)
    if tasa:
        ves = float(tasa.usd_bcv_bs or tasa.usd_bs or 0)
        cop = float(tasa.cop_usd or 0)
        if ves > 0:
            base["USD_TO_VES"] = ves
        if cop > 0:
            base["USD_TO_COP"] = cop
        base["origen"] = "base_datos"
    else:
        base["origen"] = "defecto"
    return base


def _periodo_mes(ref: date) -> tuple[datetime, datetime]:
    inicio = date(ref.year, ref.month, 1)
    ultimo = monthrange(ref.year, ref.month)[1]
    fin = date(ref.year, ref.month, ultimo)
    return _rango_datetime(inicio, fin)


def _salario_base_local(iso: str, tipo_pago: str, salario_override: Optional[float]) -> Decimal:
    if salario_override is not None and _d(salario_override) > 0:
        return _d(salario_override)
    if tipo_pago == "comision":
        return _d("0")
    if iso == "CO":
        return _d(SALARIO_REFERENCIA_CO_COP)
    if iso == "VE":
        return _d(SALARIO_REFERENCIA_VE_USD)
    return _d("0")


def _local_a_usd(monto_local: Decimal, iso: str, tasas: dict[str, float]) -> Decimal:
    if monto_local <= 0:
        return _d("0")
    if iso == "CO":
        cop_usd = _d(tasas.get("USD_TO_COP") or USD_TO_COP)
        if cop_usd <= 0:
            return _d("0")
        return (monto_local / cop_usd).quantize(Decimal("0.01"), ROUND_HALF_UP)
    if iso == "VE":
        # Salario de referencia ya viene en USD
        return monto_local.quantize(Decimal("0.01"), ROUND_HALF_UP)
    return monto_local.quantize(Decimal("0.01"), ROUND_HALF_UP)


def _usd_a_local(monto_usd: Decimal, moneda: str, tasas: dict[str, float]) -> Decimal:
    mon = moneda.upper()
    if mon == "USD":
        return monto_usd.quantize(Decimal("0.01"), ROUND_HALF_UP)
    if mon == "COP":
        return (monto_usd * _d(tasas.get("USD_TO_COP") or USD_TO_COP)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
    if mon in ("VES", "BS"):
        return (monto_usd * _d(tasas.get("USD_TO_VES") or USD_TO_VES_BCV)).quantize(
            Decimal("0.01"), ROUND_HALF_UP
        )
    return monto_usd


def _monto_en_usd_desde_detalle(
    detalle: dict[str, Any],
    tasas: dict[str, float],
) -> Decimal:
    total = _d("0")
    for moneda, valor in detalle.items():
        m = _d(valor)
        if m <= 0:
            continue
        key = str(moneda).upper()
        if key == "USD":
            total += m
        elif key in ("VES", "BS"):
            tasa = _d(tasas.get("USD_TO_VES") or USD_TO_VES_BCV)
            if tasa > 0:
                total += (m / tasa).quantize(Decimal("0.01"), ROUND_HALF_UP)
        elif key == "COP":
            tasa = _d(tasas.get("USD_TO_COP") or USD_TO_COP)
            if tasa > 0:
                total += (m / tasa).quantize(Decimal("0.01"), ROUND_HALF_UP)
    return total.quantize(Decimal("0.01"), ROUND_HALF_UP)


def _desglose_sugerido_ve(total_usd: Decimal, tasas: dict[str, float]) -> dict[str, float]:
    """Sugerencia: todo en USD; el front puede repartir."""
    ves_tasa = float(tasas.get("USD_TO_VES") or USD_TO_VES_BCV)
    cop_tasa = float(tasas.get("USD_TO_COP") or USD_TO_COP)
    return {
        "USD": float(total_usd),
        "VES": float(_usd_a_local(total_usd, "VES", tasas)),
        "COP": float(_usd_a_local(total_usd, "COP", tasas)),
        "tasas": {"USD_TO_VES": ves_tasa, "USD_TO_COP": cop_tasa},
    }


def calcular_nomina(
    db: Session,
    empresa_id,
    *,
    usuario_id: str,
    pais: Optional[str] = None,
    tipo_pago: str = "mixto",
    fecha_pago: Optional[date] = None,
    salario_base: Optional[float] = None,
    total_bonos: float = 0,
    porcentaje_cobro: Optional[float] = None,
    detalles_pago: Optional[dict[str, float]] = None,
    datos_extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Calcula totales y desglose multi-moneda para un empleado."""
    datos_extra = datos_extra or {}
    ref = fecha_pago or date.today()
    tipo = (tipo_pago or "mixto").lower().strip()
    if tipo not in ("salario_basico", "comision", "mixto"):
        raise ValueError("tipo_pago debe ser salario_basico, comision o mixto")

    emp = (
        db.query(Usuario)
        .filter(Usuario.id == str(usuario_id), Usuario.empresa_id == empresa_id)
        .first()
    )
    if not emp:
        raise ValueError("Empleado no encontrado")
    if emp.rol not in (RolUsuario.VENDEDOR, RolUsuario.COBRADOR, RolUsuario.ADMINISTRADOR):
        raise ValueError("El usuario seleccionado no es elegible para nómina operativa")

    pais_obj: Pais | None = None
    if emp.pais_id:
        pais_obj = db.query(Pais).filter(Pais.id == emp.pais_id).first()
    iso = _iso_pais(pais, pais_obj)
    moneda_principal = _moneda_principal_pais(iso, pais_obj)
    tasas = obtener_tasas_nomina(db, empresa_id)

    cfg = _obtener_config_nomina(db, empresa_id)
    dt_desde, dt_hasta = _periodo_mes(ref)
    if datos_extra.get("fecha_desde") and datos_extra.get("fecha_hasta"):
        fd = date.fromisoformat(str(datos_extra["fecha_desde"])[:10])
        fh = date.fromisoformat(str(datos_extra["fecha_hasta"])[:10])
        dt_desde, dt_hasta = _rango_datetime(fd, fh)

    linea = calcular_linea_empleado(
        db, empresa_id, emp, cfg, dt_desde, dt_hasta, pais=pais_obj
    )

    comisiones_usd = _d("0")
    if tipo in ("comision", "mixto"):
        comisiones_usd = _d(linea["comision_usd"])
        if porcentaje_cobro is not None and emp.rol == RolUsuario.COBRADOR:
            pct = _d(porcentaje_cobro)
            total_cob = _d(linea["total_cobrado_usd"])
            comisiones_usd = (total_cob * pct / _d("100")).quantize(
                Decimal("0.01"), ROUND_HALF_UP
            )

    salario_local = _salario_base_local(iso, tipo, salario_base)
    if emp.sueldo_base_usd and _d(emp.sueldo_base_usd) > 0 and tipo != "comision":
        if iso == "VE" or moneda_principal == "USD":
            salario_local = _d(emp.sueldo_base_usd)
        elif iso == "CO":
            salario_local = _usd_a_local(_d(emp.sueldo_base_usd), "COP", tasas)

    salario_usd = _d("0")
    if tipo in ("salario_basico", "mixto"):
        salario_usd = _local_a_usd(salario_local, iso, tasas)

    bonos_input = _d(total_bonos)
    if iso == "CO":
        bonos_usd = _local_a_usd(bonos_input, "CO", tasas)
    else:
        bonos_usd = bonos_input

    total_usd = (salario_usd + comisiones_usd + bonos_usd).quantize(
        Decimal("0.01"), ROUND_HALF_UP
    )
    tasa_ref = _d(tasas.get("USD_TO_COP") if iso == "CO" else tasas.get("USD_TO_VES"))
    total_local = _usd_a_local(total_usd, moneda_principal, tasas)

    detalle_out: dict[str, float]
    advertencia_detalle: str | None = None
    if iso == "VE":
        if detalles_pago:
            det_norm = {str(k).upper(): float(v) for k, v in detalles_pago.items() if v}
            suma_usd = _monto_en_usd_desde_detalle(det_norm, tasas)
            if abs(suma_usd - total_usd) > _TOLERANCIA_USD:
                advertencia_detalle = (
                    f"El desglose ({float(suma_usd):.2f} USD eq.) no coincide con "
                    f"el total ({float(total_usd):.2f} USD)."
                )
            detalle_out = det_norm
        else:
            detalle_out = _desglose_sugerido_ve(total_usd, tasas)
    else:
        detalle_out = {
            moneda_principal: float(total_local),
            "USD": float(total_usd),
        }

    return {
        "usuario_id": str(emp.id),
        "empleado_nombre": emp.nombre,
        "rol": emp.rol.value,
        "pais": iso,
        "moneda_principal": moneda_principal,
        "tipo_pago": tipo,
        "fecha_pago": ref.isoformat(),
        "periodo_desde": dt_desde.date().isoformat(),
        "periodo_hasta": dt_hasta.date().isoformat(),
        "salario_base": float(salario_local),
        "salario_base_usd": float(salario_usd),
        "total_comisiones": float(comisiones_usd),
        "total_bonos": float(total_bonos),
        "porcentaje_cobro": float(porcentaje_cobro) if porcentaje_cobro is not None else None,
        "num_ventas": linea["num_ventas"],
        "total_cobrado_usd": linea["total_cobrado_usd"],
        "total_pagar_usd": float(total_usd),
        "total_pagar_local": float(total_local),
        "tasa_cambio_aplicada": float(tasa_ref),
        "tasas": tasas,
        "detalles_pago": detalle_out,
        "advertencia_detalle": advertencia_detalle,
    }


def procesar_pago_nomina(
    db: Session,
    empresa_id,
    registrado_por_id,
    payload: dict[str, Any],
) -> PagoEmpleadoNomina:
    """Persiste el pago y registra movimiento financiero."""
    calc = calcular_nomina(
        db,
        empresa_id,
        usuario_id=payload["usuario_id"],
        pais=payload.get("pais"),
        tipo_pago=payload.get("tipo_pago", "mixto"),
        fecha_pago=date.fromisoformat(str(payload.get("fecha_pago", date.today()))[:10]),
        salario_base=payload.get("salario_base"),
        total_bonos=float(payload.get("total_bonos") or 0),
        porcentaje_cobro=payload.get("porcentaje_cobro"),
        detalles_pago=payload.get("detalles_pago"),
        datos_extra=payload.get("datos_extra"),
    )
    if calc.get("advertencia_detalle") and not payload.get("forzar_desglose"):
        raise ValueError(calc["advertencia_detalle"])

    ref = date.fromisoformat(calc["fecha_pago"])
    dt_desde = datetime.combine(date.fromisoformat(calc["periodo_desde"]), time.min)
    dt_hasta = datetime.combine(date.fromisoformat(calc["periodo_hasta"]), time.max)

    emp = db.query(Usuario).filter(Usuario.id == calc["usuario_id"]).first()
    pais_id = emp.pais_id if emp else None

    detalles = payload.get("detalles_pago") or calc["detalles_pago"]
    if isinstance(detalles, dict) and "tasas" in detalles:
        detalles = {k: v for k, v in detalles.items() if k != "tasas"}

    registro = PagoEmpleadoNomina(
        empresa_id=empresa_id,
        usuario_id=calc["usuario_id"],
        pais_id=pais_id,
        fecha_pago=ref,
        pais=calc["pais"],
        moneda_principal=calc["moneda_principal"],
        tipo_pago=calc["tipo_pago"],
        salario_base=calc["salario_base"],
        total_comisiones=calc["total_comisiones"],
        total_bonos=calc["total_bonos"],
        porcentaje_cobro=calc.get("porcentaje_cobro"),
        total_pagar_usd=calc["total_pagar_usd"],
        total_pagar_local=calc["total_pagar_local"],
        tasa_cambio_aplicada=calc["tasa_cambio_aplicada"],
        detalles_pago=detalles,
        estado=EstadoPagoNomina.REALIZADO,
        registrado_por_id=registrado_por_id,
        notas=payload.get("notas"),
    )
    db.add(registro)
    db.flush()

    descripcion = payload.get("notas") or (
        f"Pago nómina {calc['tipo_pago']} — {calc['empleado_nombre']} ({calc['pais']})"
    )
    try:
        mov = aprobar_pago_nomina(
            db,
            empresa_id,
            registrado_por_id,
            calc["usuario_id"],
            float(calc["total_pagar_usd"]),
            dt_desde,
            dt_hasta,
            descripcion,
        )
        registro.movimiento_financiero_id = mov.id
    except Exception:
        logger.exception("Movimiento financiero de nómina omitido pago=%s", registro.id)

    db.flush()
    return registro
