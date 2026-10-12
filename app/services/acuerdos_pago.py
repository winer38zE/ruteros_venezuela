"""Acuerdos flexibles y plazos de gracia.

El acuerdo no mueve la fecha de las cuotas ni el estado de la venta.
Eso dejaría intactos la cobranza de calle, el buró, Isar y la sincronización.
Lo que cambia es la alerta estricta de la carpeta crítica: queda suspendida
mientras el acuerdo esté activo y la fecha límite no haya pasado.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from app.models.core import (
    AcuerdoPago,
    EstadoVenta,
    Usuario,
    Venta,
)

ESTADOS_ACUERDO = {
    "activo": "Activo",
    "cumplido": "Cumplido",
    "incumplido": "Incumplido",
}

_ESTADOS_ABIERTOS = (EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL)


def etiqueta_acuerdo(estado: str) -> str:
    return ESTADOS_ACUERDO.get(estado, estado)


def _saldo_cliente(db: Session, empresa_id: uuid.UUID, cliente_id: uuid.UUID) -> Decimal:
    ventas = (
        db.query(Venta)
        .options(joinedload(Venta.cobros))
        .filter(
            Venta.empresa_id == empresa_id,
            Venta.cliente_id == cliente_id,
            Venta.estado.in_(_ESTADOS_ABIERTOS),
        )
        .all()
    )
    ventas = list({venta.id: venta for venta in ventas}.values())
    total = Decimal("0")
    for venta in ventas:
        cobrado = sum((Decimal(str(c.monto_usd)) for c in venta.cobros), Decimal("0"))
        saldo = Decimal(str(venta.total_usd)) - cobrado
        if saldo > 0:
            total += saldo
    return total


def reconciliar_acuerdos(
    db: Session,
    empresa_id: uuid.UUID,
    saldos_abiertos: dict[uuid.UUID, Decimal],
    hoy: date,
) -> list[AcuerdoPago]:
    """Pasa a cumplido si ya no hay saldo, o a incumplido si venció el plazo."""
    acuerdos = (
        db.query(AcuerdoPago)
        .filter(
            AcuerdoPago.empresa_id == empresa_id,
            AcuerdoPago.estado == "activo",
        )
        .all()
    )
    cambio = False
    for acuerdo in acuerdos:
        saldo = saldos_abiertos.get(acuerdo.cliente_id, Decimal("0"))
        if saldo <= 0:
            acuerdo.estado = "cumplido"
            cambio = True
        elif acuerdo.fecha_limite < hoy:
            acuerdo.estado = "incumplido"
            cambio = True
    if cambio:
        db.commit()
    return (
        db.query(AcuerdoPago)
        .filter(AcuerdoPago.empresa_id == empresa_id)
        .order_by(AcuerdoPago.fecha_creacion.desc())
        .all()
    )


def _en_gracia(acuerdo: AcuerdoPago, hoy: date) -> bool:
    return acuerdo.estado == "activo" and acuerdo.fecha_limite >= hoy


def acuerdo_que_suspende(
    acuerdos: list[AcuerdoPago],
    hoy: date,
) -> Optional[AcuerdoPago]:
    vivos = [a for a in acuerdos if _en_gracia(a, hoy)]
    if not vivos:
        return None
    return max(vivos, key=lambda a: (a.fecha_limite, a.fecha_creacion or datetime.min))


def serializar_acuerdo(
    acuerdo: AcuerdoPago,
    usuario_nombre: str,
    hoy: date,
) -> dict:
    en_gracia = _en_gracia(acuerdo, hoy)
    return {
        "id": acuerdo.id,
        "empresa_id": acuerdo.empresa_id,
        "cliente_id": acuerdo.cliente_id,
        "usuario_id": acuerdo.usuario_id,
        "usuario_nombre": usuario_nombre,
        "monto_acordado_usd": float(acuerdo.monto_acordado_usd),
        "fecha_limite": acuerdo.fecha_limite,
        "cuotas_pactadas": acuerdo.cuotas_pactadas,
        "estado": acuerdo.estado,
        "estado_etiqueta": etiqueta_acuerdo(acuerdo.estado),
        "nota_consideracion": acuerdo.nota_consideracion,
        "fecha_creacion": acuerdo.fecha_creacion,
        "en_plazo_de_gracia": en_gracia,
        "alerta_estricta": not en_gracia,
    }


def resumen_acuerdo(acuerdo: AcuerdoPago) -> dict:
    return {
        "id": acuerdo.id,
        "monto_acordado_usd": float(acuerdo.monto_acordado_usd),
        "fecha_limite": acuerdo.fecha_limite,
        "cuotas_pactadas": acuerdo.cuotas_pactadas,
        "estado": acuerdo.estado,
        "estado_etiqueta": etiqueta_acuerdo(acuerdo.estado),
        "nota_consideracion": acuerdo.nota_consideracion,
    }


def aplicar_gracia(
    db: Session,
    empresa_id: uuid.UUID,
    fichas: list[dict],
    saldos_abiertos: dict[uuid.UUID, Decimal],
    hoy: date,
) -> None:
    """Marca cada ficha. No toca ventas ni cuotas."""
    acuerdos = reconciliar_acuerdos(db, empresa_id, saldos_abiertos, hoy)
    por_cliente: dict[uuid.UUID, list[AcuerdoPago]] = {}
    for acuerdo in acuerdos:
        por_cliente.setdefault(acuerdo.cliente_id, []).append(acuerdo)

    for ficha in fichas:
        del_cliente = por_cliente.get(ficha["cliente_id"], [])
        vigente = acuerdo_que_suspende(del_cliente, hoy)
        mostrar = vigente or (del_cliente[0] if del_cliente else None)
        en_gracia = vigente is not None
        ficha["en_plazo_de_gracia"] = en_gracia
        ficha["alerta_estricta"] = not en_gracia
        ficha["acuerdo"] = resumen_acuerdo(mostrar) if mostrar else None
        if en_gracia and vigente is not None:
            ficha["estado_consideracion"] = "acuerdo_pago"
            ficha["estado_etiqueta"] = "Acuerdo de pago"


def listar_acuerdos_cliente(
    db: Session,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    hoy: Optional[date] = None,
) -> list[dict]:
    referencia = hoy or datetime.utcnow().date()
    filas = (
        db.query(AcuerdoPago, Usuario.nombre)
        .join(Usuario, Usuario.id == AcuerdoPago.usuario_id)
        .filter(
            AcuerdoPago.empresa_id == empresa_id,
            AcuerdoPago.cliente_id == cliente_id,
        )
        .order_by(AcuerdoPago.fecha_creacion.desc())
        .all()
    )
    return [serializar_acuerdo(acuerdo, nombre, referencia) for acuerdo, nombre in filas]


def crear_acuerdo(
    db: Session,
    *,
    empresa_id: uuid.UUID,
    cliente_id: uuid.UUID,
    usuario_id: uuid.UUID,
    usuario_nombre: str,
    monto_acordado_usd: float,
    fecha_limite: date,
    cuotas_pactadas: int,
    nota_consideracion: str,
    hoy: Optional[date] = None,
) -> dict:
    from app.services.cartera_critica import crear_nota, cliente_de_empresa

    referencia = hoy or datetime.utcnow().date()
    if fecha_limite < referencia:
        raise ValueError("La fecha límite del plazo de gracia no puede estar vencida")
    if cuotas_pactadas < 1:
        raise ValueError("El acuerdo necesita al menos una cuota pactada")
    texto = nota_consideracion.strip()
    if len(texto) < 3:
        raise ValueError("Escribe la nota de consideración del acuerdo")

    cliente = cliente_de_empresa(db, empresa_id, cliente_id)
    if cliente is None:
        raise LookupError("El cliente no pertenece a la empresa")
    if _saldo_cliente(db, empresa_id, cliente_id) <= 0:
        raise ValueError("El cliente no tiene saldo pendiente para reestructurar")

    from app.models.core import NotaSeguimientoCobranza

    motivo_vigente = (
        db.query(NotaSeguimientoCobranza.motivo)
        .filter(
            NotaSeguimientoCobranza.empresa_id == empresa_id,
            NotaSeguimientoCobranza.cliente_id == cliente_id,
        )
        .order_by(NotaSeguimientoCobranza.fecha.desc())
        .first()
    )
    motivo = motivo_vigente[0] if motivo_vigente and motivo_vigente[0] else "otro"

    ahora = datetime.utcnow()
    acuerdo = AcuerdoPago(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        usuario_id=usuario_id,
        monto_acordado_usd=Decimal(str(monto_acordado_usd)),
        fecha_limite=fecha_limite,
        cuotas_pactadas=cuotas_pactadas,
        estado="activo",
        nota_consideracion=texto,
        fecha_creacion=ahora,
    )
    db.add(acuerdo)
    crear_nota(
        db,
        empresa_id=empresa_id,
        cliente_id=cliente_id,
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        motivo=motivo,
        estado_consideracion="acuerdo_pago",
        observacion=(
            f"Plazo de gracia hasta {fecha_limite.strftime('%d/%m/%Y')}. "
            f"Monto acordado {monto_acordado_usd:.2f} USD en {cuotas_pactadas} cuota(s). {texto}"
        ),
        commit=False,
    )
    db.commit()
    db.refresh(acuerdo)
    return serializar_acuerdo(acuerdo, usuario_nombre, referencia)
