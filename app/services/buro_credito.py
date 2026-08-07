"""Buró de crédito compartido y scoring de clientes."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.core import (
    Cliente,
    Cobro,
    EventoBuroCredito,
    FrecuenciaPago,
    EstadoVenta,
    Venta,
)

SCORE_MIN = 15
SCORE_MAX = 100
SCORE_BLOQUEO_CREDITO = 35

_DIAS_FRECUENCIA = {
    FrecuenciaPago.SEMANAL: 7,
    FrecuenciaPago.QUINCENAL: 15,
    FrecuenciaPago.MENSUAL: 30,
}


def normalizar_identificacion(identificacion: str) -> str:
    return "".join(ch for ch in identificacion.upper().strip() if ch.isalnum())


def clasificar_score(score: int) -> str:
    if score >= 85:
        return "excelente"
    if score >= 60:
        return "bueno"
    if score >= 35:
        return "regular"
    return "malo"


def etiqueta_estado(score: int) -> str:
    mapping = {
        "excelente": "Excelente",
        "bueno": "Bueno",
        "regular": "Regular",
        "malo": "Malo / Moroso",
    }
    return mapping[clasificar_score(score)]


def _clamp_score(score: int) -> int:
    return max(SCORE_MIN, min(SCORE_MAX, score))


def registrar_evento_buro(
    db: Session,
    identificacion: str,
    tipo_evento: str,
    mensaje: str,
) -> None:
    db.add(
        EventoBuroCredito(
            identificacion=normalizar_identificacion(identificacion),
            tipo_evento=tipo_evento,
            mensaje=mensaje,
        )
    )


def score_global_identificacion(db: Session, identificacion: str) -> int | None:
    ident = normalizar_identificacion(identificacion)
    clientes = db.query(Cliente).filter(Cliente.identificacion == ident).all()
    if not clientes:
        return None
    return _clamp_score(min(c.score_credito for c in clientes))


def historial_buro(db: Session, identificacion: str, limit: int = 10) -> list[EventoBuroCredito]:
    ident = normalizar_identificacion(identificacion)
    return (
        db.query(EventoBuroCredito)
        .filter(EventoBuroCredito.identificacion == ident)
        .order_by(EventoBuroCredito.fecha.desc())
        .limit(limit)
        .all()
    )


def datos_autocompletado_buro(db: Session, identificacion: str) -> dict | None:
    """Información básica verificada sin revelar empresa origen."""
    ident = normalizar_identificacion(identificacion)
    registros = (
        db.query(Cliente)
        .filter(Cliente.identificacion == ident)
        .order_by(Cliente.fecha_creacion.desc())
        .all()
    )
    if not registros:
        return None

    ref = max(registros, key=lambda c: sum(1 for v in (c.telefono, c.direccion, c.email) if v))
    score = score_global_identificacion(db, ident) or ref.score_credito

    return {
        "identificacion": ident,
        "nombre_completo": ref.nombre,
        "telefono": ref.telefono,
        "telefono_secundario": ref.telefono_secundario,
        "direccion": ref.direccion,
        "punto_referencia": ref.punto_referencia,
        "empresa_trabajo": ref.empresa_trabajo,
        "direccion_laboral": ref.direccion_laboral,
        "ref_familiar_nombre": ref.ref_familiar_nombre,
        "ref_familiar_parentesco": ref.ref_familiar_parentesco,
        "ref_familiar_telefono": ref.ref_familiar_telefono,
        "email": ref.email,
        "score_global": score,
        "nivel_riesgo": clasificar_score(score),
        "estado_credito": etiqueta_estado(score),
        "en_red": True,
    }


def consultar_buro(db: Session, identificacion: str) -> dict:
    ident = normalizar_identificacion(identificacion)
    score = score_global_identificacion(db, ident)
    eventos = historial_buro(db, ident)
    historial = [
        {
            "fecha": e.fecha.isoformat(),
            "tipo": e.tipo_evento,
            "mensaje": e.mensaje,
        }
        for e in eventos
    ]
    if score is None:
        return {
            "identificacion": ident,
            "encontrado": False,
            "score_global": None,
            "nivel_riesgo": None,
            "estado_credito": None,
            "historial_cumplimiento": [],
        }

    return {
        "identificacion": ident,
        "encontrado": True,
        "score_global": score,
        "nivel_riesgo": clasificar_score(score),
        "estado_credito": etiqueta_estado(score),
        "historial_cumplimiento": historial,
    }


def validar_venta_credito(cliente: Cliente, frecuencia: FrecuenciaPago) -> None:
    if frecuencia == FrecuenciaPago.CONTADO:
        return
    score_efectivo = cliente.score_credito
    if score_efectivo <= SCORE_BLOQUEO_CREDITO:
        raise HTTPException(
            status_code=403,
            detail=(
                "Crédito Rechazado: Cliente reportado con alto riesgo crediticio. "
                "Solo ventas de contado."
            ),
        )


def _fecha_limite_pago(venta: Venta) -> datetime | None:
    if venta.frecuencia_pago == FrecuenciaPago.CONTADO:
        return venta.fecha
    dias = _DIAS_FRECUENCIA.get(venta.frecuencia_pago)
    if not dias:
        return None
    return venta.fecha + timedelta(days=dias)


def aplicar_ajuste_score(db: Session, cliente: Cliente, delta: int, motivo: str, tipo_evento: str) -> int:
    nuevo = _clamp_score(cliente.score_credito + delta)
    cliente.score_credito = nuevo
    registrar_evento_buro(
        db,
        cliente.identificacion,
        tipo_evento,
        motivo,
    )
    return nuevo


def actualizar_score_por_cobro(db: Session, venta: Venta, cobro: Cobro) -> None:
    cliente = venta.cliente
    if not cliente or not cliente.identificacion:
        return

    limite = _fecha_limite_pago(venta)
    if limite is None:
        return

    fecha_cobro = cobro.fecha or datetime.utcnow()
    dias_mora = max(0, (fecha_cobro - limite).days)

    if dias_mora == 0:
        aplicar_ajuste_score(
            db,
            cliente,
            +5,
            "Pago registrado dentro del plazo acordado en la red Ruteros.",
            "pago_tiempo",
        )
    elif dias_mora <= 7:
        aplicar_ajuste_score(
            db,
            cliente,
            -8,
            f"Cliente con reporte de mora leve ({dias_mora} días) en la red.",
            "mora_leve",
        )
    elif dias_mora <= 30:
        aplicar_ajuste_score(
            db,
            cliente,
            -15,
            f"Cliente con reporte de mora moderada ({dias_mora} días) en otra ruta.",
            "mora_moderada",
        )
    else:
        aplicar_ajuste_score(
            db,
            cliente,
            -25,
            f"Cliente con reporte de mora severa ({dias_mora} días) en la red.",
            "mora_severa",
        )


def revisar_moras_pendientes(db: Session, cliente: Cliente) -> None:
    """Penaliza score por ventas a crédito vencidas sin cobrar."""
    ventas = (
        db.query(Venta)
        .filter(
            Venta.cliente_id == cliente.id,
            Venta.frecuencia_pago != FrecuenciaPago.CONTADO,
            Venta.estado.in_([EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL]),
        )
        .all()
    )
    for venta in ventas:
        limite = _fecha_limite_pago(venta)
        if not limite:
            continue
        dias = (datetime.utcnow() - limite).days
        if dias > 0:
            cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
            if cobrado < Decimal(str(venta.total_usd)):
                penal = min(20, 5 + dias // 7 * 3)
                aplicar_ajuste_score(
                    db,
                    cliente,
                    -penal,
                    "Cliente con reporte de mora en venta pendiente en la red.",
                    "mora_pendiente",
                )
                break


def sincronizar_score_inicial(db: Session, cliente: Cliente) -> None:
    global_score = score_global_identificacion(db, cliente.identificacion)
    if global_score is not None:
        cliente.score_credito = global_score
    else:
        cliente.score_credito = _clamp_score(cliente.score_credito or 70)
