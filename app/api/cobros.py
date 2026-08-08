from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import obtener_usuario_opcional, require_cobrador_o_superior, require_operaciones
from app.core.tenant import obtener_empresa_tenant
from app.models.core import (
    Cobro, Venta, Usuario, MonedaPago, EstadoVenta, RolUsuario,
    Producto, DetalleVenta, EstadoCuota,
)
from app.schemas.core import CobroCreate, CobroResponse, VentaPendienteResponse
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid
from app.services.contabilidad import generar_asiento_cobro
from app.services.buro_credito import actualizar_score_por_cobro
from app.services.amortizacion import aplicar_abono_a_cuotas, proxima_cuota_pendiente

router = APIRouter()

FRECUENCIA_LABEL = {
    "semanal": "Semanal",
    "quincenal": "Quincenal",
    "mensual": "Mensual",
    "contado": "Contado",
}


def _actualizar_estado_venta(db: Session, venta: Venta) -> None:
    total_cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
    total_venta = Decimal(str(venta.total_usd))

    if total_cobrado >= total_venta:
        venta.estado = EstadoVenta.PAGADA
    elif total_cobrado > 0:
        venta.estado = EstadoVenta.PARCIAL
    else:
        venta.estado = EstadoVenta.PENDIENTE


def _resolver_cobrador(
    db: Session,
    empresa_id,
    cobrador_id=None,
    usuario_header: Optional[Usuario] = None,
) -> Usuario:
    if usuario_header:
        if usuario_header.empresa_id != empresa_id:
            raise HTTPException(status_code=400, detail="Usuario no pertenece a la empresa")
        if usuario_header.rol not in (RolUsuario.COBRADOR, RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
            raise HTTPException(status_code=403, detail="Solo COBRADOR, ADMINISTRADOR o DUEÑO puede registrar cobros")
        return usuario_header

    if cobrador_id:
        cobrador = (
            db.query(Usuario)
            .filter(Usuario.id == cobrador_id, Usuario.empresa_id == empresa_id)
            .first()
        )
        if not cobrador:
            raise HTTPException(status_code=400, detail="El cobrador indicado no existe")
        return cobrador

    cobrador = (
        db.query(Usuario)
        .filter(Usuario.empresa_id == empresa_id, Usuario.rol == RolUsuario.COBRADOR)
        .first()
    )
    if not cobrador:
        cobrador = db.query(Usuario).filter(Usuario.empresa_id == empresa_id).first()
    if not cobrador:
        raise HTTPException(status_code=400, detail="Debes crear al menos un cobrador")
    return cobrador


def _productos_resumen(db: Session, venta: Venta) -> tuple[str, float]:
    if not venta.detalles:
        return "—", 0.0
    nombres = []
    costo = Decimal("0")
    for d in venta.detalles:
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        nombre = prod.nombre if prod else str(d.producto_id)[:8]
        nombres.append(f"{nombre} x{d.cantidad}")
        if prod:
            costo += Decimal(str(prod.costo_usd or 0)) * d.cantidad
    return ", ".join(nombres[:3]) + ("..." if len(nombres) > 3 else ""), float(costo)


def _estado_cuenta(proxima_fecha: Optional[datetime]) -> str:
    if not proxima_fecha:
        return "Al día"
    if proxima_fecha.date() < datetime.utcnow().date():
        return "En mora"
    return "Al día"


def _build_panel_item(db: Session, v: Venta) -> VentaPendienteResponse:
    cobrado = sum(Decimal(str(c.monto_usd)) for c in v.cobros)
    saldo = Decimal(str(v.total_usd)) - cobrado
    productos, costo = _productos_resumen(db, v)
    proxima = proxima_cuota_pendiente(db, v.id)
    cuotas_totales = len(v.cuotas) if v.cuotas else 0
    cuotas_pagadas = sum(1 for c in (v.cuotas or []) if c.estado == EstadoCuota.PAGADA)
    freq = v.frecuencia_pago.value if v.frecuencia_pago else "contado"

    return VentaPendienteResponse(
        id=v.id,
        cliente_id=v.cliente_id,
        cliente_nombre=v.cliente.nombre if v.cliente else "—",
        productos_resumen=productos,
        costo_total_usd=costo,
        total_usd=float(v.total_usd),
        cobrado_usd=float(cobrado),
        saldo_pendiente_usd=float(saldo),
        frecuencia_pago=freq,
        tipo_credito=FRECUENCIA_LABEL.get(freq, freq),
        estado=v.estado.value,
        estado_cuenta=_estado_cuenta(proxima.fecha_vencimiento if proxima else None),
        proximo_pago=proxima.fecha_vencimiento if proxima else None,
        monto_proxima_cuota_usd=float(proxima.monto_usd - proxima.monto_pagado_usd) if proxima else 0.0,
        cuotas_pagadas=cuotas_pagadas,
        cuotas_totales=cuotas_totales,
    )


@router.get("/panel-cobranza", response_model=List[VentaPendienteResponse])
def panel_cobranza(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    ventas = (
        db.query(Venta)
        .options(
            joinedload(Venta.cobros),
            joinedload(Venta.cliente),
            joinedload(Venta.detalles),
            joinedload(Venta.cuotas),
        )
        .filter(
            Venta.empresa_id == usuario.empresa_id,
            Venta.estado.in_([EstadoVenta.PENDIENTE, EstadoVenta.PARCIAL]),
        )
        .order_by(Venta.fecha.desc())
        .all()
    )
    return [_build_panel_item(db, v) for v in ventas if Decimal(str(v.total_usd)) - sum(Decimal(str(c.monto_usd)) for c in v.cobros) > 0]


@router.get("/ventas-pendientes", response_model=List[VentaPendienteResponse])
def listar_ventas_pendientes(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    return panel_cobranza(db=db, usuario=usuario)


@router.get("/mis-cobros", response_model=List[CobroResponse])
def listar_mis_cobros(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    q = db.query(Cobro).filter(Cobro.empresa_id == usuario.empresa_id)
    if usuario.rol == RolUsuario.COBRADOR:
        q = q.filter(Cobro.cobrador_id == usuario.id)
    return q.order_by(Cobro.fecha.desc()).all()


@router.post("/", response_model=CobroResponse)
def registrar_cobro(
    cobro: CobroCreate,
    db: Session = Depends(get_db),
    usuario_header: Optional[Usuario] = Depends(obtener_usuario_opcional),
):
    empresa_actual = obtener_empresa_tenant(db)

    venta = (
        db.query(Venta)
        .options(joinedload(Venta.cobros), joinedload(Venta.cliente), joinedload(Venta.cuotas))
        .filter(Venta.id == cobro.venta_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=400, detail="La venta indicada no existe")
    if venta.empresa_id != empresa_actual.id:
        raise HTTPException(status_code=400, detail="La venta no pertenece a la empresa actual")

    cobrador = _resolver_cobrador(db, empresa_actual.id, cobro.cobrador_id, usuario_header)

    db.refresh(venta)
    cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
    saldo = Decimal(str(venta.total_usd)) - cobrado
    monto = Decimal(str(cobro.monto_usd))
    if monto > saldo + Decimal("0.01"):
        raise HTTPException(
            status_code=400,
            detail=f"Monto excede saldo pendiente (${float(saldo):.2f})",
        )

    try:
        moneda = MonedaPago(cobro.moneda_pago)
    except ValueError:
        raise HTTPException(status_code=400, detail="Moneda de pago inválida")

    cobro_id = uuid.UUID(cobro.id) if cobro.id else uuid.uuid4()

    nuevo_cobro = Cobro(
        id=cobro_id,
        empresa_id=empresa_actual.id,
        venta_id=venta.id,
        cobrador_id=cobrador.id,
        fecha=cobro.fecha or datetime.utcnow(),
        monto_usd=cobro.monto_usd,
        moneda_pago=moneda,
        tasa_usd_aplicada=cobro.tasa_usd_aplicada,
        tasa_eur_aplicada=cobro.tasa_eur_aplicada,
    )

    db.add(nuevo_cobro)
    db.flush()
    db.refresh(venta)
    _actualizar_estado_venta(db, venta)
    aplicar_abono_a_cuotas(db, venta, monto)
    db.refresh(venta, attribute_names=["cliente", "cobros"])
    if venta.cliente:
        actualizar_score_por_cobro(db, venta, nuevo_cobro)
    generar_asiento_cobro(db, nuevo_cobro)
    db.commit()
    db.refresh(nuevo_cobro)

    return nuevo_cobro


@router.get("/", response_model=List[CobroResponse])
def listar_cobros(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    return (
        db.query(Cobro)
        .filter(Cobro.empresa_id == usuario.empresa_id)
        .order_by(Cobro.fecha.desc())
        .all()
    )
