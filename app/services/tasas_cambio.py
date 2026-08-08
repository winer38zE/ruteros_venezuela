"""Utilidades de tasas de cambio multimoneda."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from app.models.core import TasaCambio, TipoTasaUsd


def _d(val) -> Decimal:
    return Decimal(str(val or 0))


def obtener_ultima_tasa(db: Session, empresa_id) -> Optional[TasaCambio]:
    return (
        db.query(TasaCambio)
        .filter(TasaCambio.empresa_id == empresa_id)
        .order_by(TasaCambio.fecha.desc())
        .first()
    )


def tasa_usd_a_ves(tasa: TasaCambio, tipo: TipoTasaUsd = TipoTasaUsd.BCV) -> Decimal:
    if tipo == TipoTasaUsd.PARALELO and tasa.usd_paralelo_bs:
        return _d(tasa.usd_paralelo_bs)
    if tasa.usd_bcv_bs:
        return _d(tasa.usd_bcv_bs)
    return _d(tasa.usd_bs)


def convertir_usd_a_ves(monto_usd: Decimal, tasa: TasaCambio, tipo: TipoTasaUsd) -> Decimal:
    return (_d(monto_usd) * tasa_usd_a_ves(tasa, tipo)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def convertir_usd_a_cop(monto_usd: Decimal, tasa: TasaCambio) -> Decimal:
    if not tasa.cop_usd or _d(tasa.cop_usd) == 0:
        return Decimal("0")
    return (_d(monto_usd) * _d(tasa.cop_usd)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def convertir_cop_a_usd(monto_cop: Decimal, tasa: TasaCambio) -> Decimal:
    if not tasa.cop_usd or _d(tasa.cop_usd) == 0:
        return Decimal("0")
    return (_d(monto_cop) / _d(tasa.cop_usd)).quantize(Decimal("0.01"), ROUND_HALF_UP)


def convertir_cop_a_ves(monto_cop: Decimal, tasa: TasaCambio, tipo: TipoTasaUsd) -> Decimal:
    if tasa.cop_ves:
        return (_d(monto_cop) * _d(tasa.cop_ves)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    usd = convertir_cop_a_usd(monto_cop, tasa)
    return convertir_usd_a_ves(usd, tasa, tipo)


def calcular_precios_equivalentes(
    precio_usd: Decimal,
    tasa: TasaCambio,
    tipo_tasa: TipoTasaUsd = TipoTasaUsd.BCV,
) -> dict:
    return {
        "precio_usd": float(_d(precio_usd)),
        "precio_ves_bcv": float(convertir_usd_a_ves(precio_usd, tasa, TipoTasaUsd.BCV)),
        "precio_ves_paralelo": float(convertir_usd_a_ves(precio_usd, tasa, TipoTasaUsd.PARALELO)),
        "precio_ves_activo": float(convertir_usd_a_ves(precio_usd, tasa, tipo_tasa)),
        "precio_cop": float(convertir_usd_a_cop(precio_usd, tasa)),
        "tasa_usd_bcv": float(tasa_usd_a_ves(tasa, TipoTasaUsd.BCV)),
        "tasa_usd_paralelo": float(tasa_usd_a_ves(tasa, TipoTasaUsd.PARALELO)),
        "cop_usd": float(_d(tasa.cop_usd or 0)),
    }
