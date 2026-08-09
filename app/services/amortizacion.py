"""Generación y actualización del plan de amortización de ventas a crédito."""
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.core import (
    CuotaAmortizacion,
    EstadoCuota,
    EstadoVenta,
    FrecuenciaPago,
    Venta,
)


CUOTAS_DEFAULT = {
    FrecuenciaPago.SEMANAL: 12,
    FrecuenciaPago.QUINCENAL: 6,
    FrecuenciaPago.MENSUAL: 6,
}

DIAS_FRECUENCIA = {
    FrecuenciaPago.SEMANAL: 7,
    FrecuenciaPago.QUINCENAL: 15,
    FrecuenciaPago.MENSUAL: 30,
}

ETIQUETA_PERIODO = {
    FrecuenciaPago.SEMANAL: "Semana",
    FrecuenciaPago.QUINCENAL: "Quincena",
    FrecuenciaPago.MENSUAL: "Mes",
}


def _d(val) -> Decimal:
    return Decimal(str(val))


def cuotas_por_defecto(frecuencia: FrecuenciaPago) -> int:
    return CUOTAS_DEFAULT.get(frecuencia, 6)


def etiqueta_periodo(frecuencia: FrecuenciaPago, numero_cuota: int) -> str:
    prefijo = ETIQUETA_PERIODO.get(frecuencia, "Cuota")
    return f"{prefijo} {numero_cuota}"


def estado_cuota_display(cuota: CuotaAmortizacion, referencia: Optional[datetime] = None) -> str:
    if cuota.estado == EstadoCuota.PAGADA:
        return "Pagado"
    hoy = (referencia or datetime.utcnow()).date()
    if cuota.fecha_vencimiento.date() < hoy and cuota.estado in (
        EstadoCuota.PENDIENTE,
        EstadoCuota.PARCIAL,
    ):
        return "Vencido"
    if cuota.estado == EstadoCuota.PARCIAL:
        return "Parcial"
    return "Pendiente"


def monto_pendiente_cuota(cuota: CuotaAmortizacion) -> float:
    pendiente = _d(cuota.monto_usd) - _d(cuota.monto_pagado_usd)
    return float(max(Decimal("0"), pendiente))


def serializar_cuota(cuota: CuotaAmortizacion, frecuencia: FrecuenciaPago) -> dict:
    return {
        "id": cuota.id,
        "venta_id": cuota.venta_id,
        "numero_cuota": cuota.numero_cuota,
        "fecha_vencimiento": cuota.fecha_vencimiento,
        "monto_usd": float(cuota.monto_usd),
        "monto_pagado_usd": float(cuota.monto_pagado_usd),
        "estado": cuota.estado.value if cuota.estado else "pendiente",
        "etiqueta_periodo": etiqueta_periodo(frecuencia, cuota.numero_cuota),
        "estado_display": estado_cuota_display(cuota),
        "monto_pendiente_usd": monto_pendiente_cuota(cuota),
    }


def generar_plan_amortizacion(
    db: Session,
    venta: Venta,
    numero_cuotas: Optional[int] = None,
) -> List[CuotaAmortizacion]:
    if venta.frecuencia_pago == FrecuenciaPago.CONTADO:
        return []

    n = numero_cuotas or venta.numero_cuotas or cuotas_por_defecto(venta.frecuencia_pago)
    n = max(1, int(n))
    venta.numero_cuotas = n

    total = _d(venta.total_usd)
    cuota_base = (total / Decimal(n)).quantize(Decimal("0.01"), ROUND_HALF_UP)
    dias = DIAS_FRECUENCIA.get(venta.frecuencia_pago, 30)
    fecha_base = venta.fecha or datetime.utcnow()

    cuotas: List[CuotaAmortizacion] = []
    acumulado = Decimal("0")
    for i in range(1, n + 1):
        monto = cuota_base
        if i == n:
            monto = total - acumulado
        acumulado += monto
        cuota = CuotaAmortizacion(
            venta_id=venta.id,
            numero_cuota=i,
            fecha_vencimiento=fecha_base + timedelta(days=dias * i),
            monto_usd=monto,
            monto_pagado_usd=Decimal("0"),
            estado=EstadoCuota.PENDIENTE,
        )
        db.add(cuota)
        cuotas.append(cuota)
    return cuotas


def aplicar_abono_a_cuotas(db: Session, venta: Venta, monto_abono_usd: Decimal) -> None:
    if venta.frecuencia_pago == FrecuenciaPago.CONTADO:
        return

    restante = _d(monto_abono_usd)
    cuotas = (
        db.query(CuotaAmortizacion)
        .filter(CuotaAmortizacion.venta_id == venta.id)
        .order_by(CuotaAmortizacion.numero_cuota.asc())
        .all()
    )
    for cuota in cuotas:
        if restante <= 0:
            break
        pendiente = _d(cuota.monto_usd) - _d(cuota.monto_pagado_usd)
        if pendiente <= 0:
            cuota.estado = EstadoCuota.PAGADA
            continue
        aplicar = min(restante, pendiente)
        cuota.monto_pagado_usd = _d(cuota.monto_pagado_usd) + aplicar
        restante -= aplicar
        if _d(cuota.monto_pagado_usd) >= _d(cuota.monto_usd):
            cuota.estado = EstadoCuota.PAGADA
        elif _d(cuota.monto_pagado_usd) > 0:
            cuota.estado = EstadoCuota.PARCIAL


def proxima_cuota_pendiente(db: Session, venta_id) -> Optional[CuotaAmortizacion]:
    return (
        db.query(CuotaAmortizacion)
        .filter(
            CuotaAmortizacion.venta_id == venta_id,
            CuotaAmortizacion.estado.in_([EstadoCuota.PENDIENTE, EstadoCuota.PARCIAL]),
        )
        .order_by(CuotaAmortizacion.fecha_vencimiento.asc())
        .first()
    )


def resumen_amortizacion(db: Session, venta: Venta) -> dict:
    cuotas = (
        db.query(CuotaAmortizacion)
        .filter(CuotaAmortizacion.venta_id == venta.id)
        .order_by(CuotaAmortizacion.numero_cuota.asc())
        .all()
    )
    proxima = proxima_cuota_pendiente(db, venta.id)
    return {
        "numero_cuotas": len(cuotas),
        "cuotas_pagadas": sum(1 for c in cuotas if c.estado == EstadoCuota.PAGADA),
        "proximo_pago": proxima.fecha_vencimiento if proxima else None,
        "monto_proxima_cuota_usd": float(proxima.monto_usd - proxima.monto_pagado_usd) if proxima else 0.0,
    }


def puede_aprobar_venta(venta: Venta) -> bool:
    return venta.estado == EstadoVenta.BORRADOR
