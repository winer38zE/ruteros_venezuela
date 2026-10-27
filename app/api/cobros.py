from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import obtener_usuario_opcional, require_cobrador_o_superior, require_operaciones, rol_confirma_pago
from app.core.tenant import obtener_empresa_tenant
from app.api.empresas import resolver_cuenta_transferencia
from app.models.core import (
    Cobro, Venta, Usuario, MonedaPago, EstadoVenta, RolUsuario,
    Producto, DetalleVenta, EstadoCuota, CuentaBancaria,
)
from app.schemas.core import (
    CobroCreate,
    CobroResponse,
    VentaPendienteResponse,
    CuotaAmortizacionResponse,
    EnvioReciboResponse,
    ComprobanteWhatsappRequest,
    WhatsappReporteResponse,
)
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
import uuid
from app.services.contabilidad import generar_asiento_cobro
from app.services.buro_credito import actualizar_historial_comportamiento, actualizar_score_por_cobro
from app.services.amortizacion import (
    aplicar_abono_a_cuotas,
    proxima_cuota_pendiente,
    serializar_cuota,
)
from app.services.recibos_email import enviar_recibo_cobro
from app.services.evolution_service import (
    armar_caption_comprobante,
    enviar_imagen,
    estado_http_whatsapp,
    normalizar_telefono,
    telefono_administrador,
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

FRECUENCIA_LABEL = {
    "semanal": "Semanal",
    "quincenal": "Quincenal",
    "mensual": "Mensual",
    "contado": "Contado",
}


def _actualizar_estado_venta(db: Session, venta: Venta, cobro_actual: Cobro, usuario: Usuario) -> list[Cobro]:
    """Devuelve cobros que pasan de no verificados a verificados en este abono."""
    if cobro_actual.es_transferencia and not rol_confirma_pago(usuario):
        cobro_actual.verificado = False
    else:
        cobro_actual.verificado = True

    recien_verificados: list[Cobro] = []
    total_cobrado = sum(Decimal(str(c.monto_usd)) for c in venta.cobros)
    total_venta = Decimal(str(venta.total_usd))

    if total_cobrado >= total_venta:
        hay_sin_verificar = any(c.verificado is False for c in venta.cobros)
        if hay_sin_verificar and not rol_confirma_pago(usuario):
            venta.estado = EstadoVenta.POR_VERIFICAR
        else:
            if rol_confirma_pago(usuario):
                for cobro in venta.cobros:
                    if cobro.verificado is False:
                        cobro.verificado = True
                        recien_verificados.append(cobro)
            venta.estado = EstadoVenta.PAGADA
    elif total_cobrado > 0:
        venta.estado = EstadoVenta.PARCIAL
    else:
        venta.estado = EstadoVenta.PENDIENTE
    return recien_verificados


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


def _puede_ver_costos(usuario: Usuario) -> bool:
    return usuario.rol in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR)


def _asegurar_cobro_en_lista_venta(venta: Venta, cobro: Cobro) -> None:
    cobros = list(venta.cobros or [])
    if not any(str(c.id) == str(cobro.id) for c in cobros):
        cobros.append(cobro)
    venta.cobros = cobros


def _respuesta_cobro(cobro: Cobro, venta: Venta | None) -> CobroResponse:
    moneda = cobro.moneda_pago
    if isinstance(moneda, MonedaPago):
        moneda = moneda.value
    estado_venta = venta.estado.value if venta and venta.estado else None
    return CobroResponse(
        id=str(cobro.id),
        empresa_id=str(cobro.empresa_id),
        venta_id=str(cobro.venta_id),
        cobrador_id=str(cobro.cobrador_id),
        fecha=cobro.fecha,
        monto_usd=float(cobro.monto_usd),
        moneda_pago=str(moneda),
        tasa_usd_aplicada=float(cobro.tasa_usd_aplicada),
        tasa_eur_aplicada=float(cobro.tasa_eur_aplicada),
        sincronizado=bool(cobro.sincronizado if cobro.sincronizado is not None else True),
        fecha_creacion=cobro.fecha_creacion or cobro.fecha or datetime.utcnow(),
        es_transferencia=bool(cobro.es_transferencia),
        verificado=bool(cobro.verificado if cobro.verificado is not None else True),
        referencia_pago=cobro.referencia_pago,
        tiene_comprobante=bool(cobro.tiene_comprobante),
        estado_venta=estado_venta,
    )


def _build_panel_item(db: Session, v: Venta, usuario: Usuario) -> VentaPendienteResponse:
    cobrado = sum(Decimal(str(c.monto_usd)) for c in v.cobros)
    saldo = Decimal(str(v.total_usd)) - cobrado
    productos, costo = _productos_resumen(db, v)
    proxima = proxima_cuota_pendiente(db, v.id)
    cuotas_ordenadas = sorted(v.cuotas or [], key=lambda c: c.numero_cuota)
    cuotas_pagadas = sum(1 for c in cuotas_ordenadas if c.estado == EstadoCuota.PAGADA)
    freq = v.frecuencia_pago.value if v.frecuencia_pago else "contado"
    frecuencia_enum = v.frecuencia_pago
    ver_costos = _puede_ver_costos(usuario)
    margen = float(Decimal(str(v.total_usd)) - Decimal(str(costo))) if ver_costos else None

    cuotas_resp = [
        CuotaAmortizacionResponse(**serializar_cuota(c, frecuencia_enum))
        for c in cuotas_ordenadas
    ]

    return VentaPendienteResponse(
        id=v.id,
        cliente_id=v.cliente_id,
        cliente_nombre=v.cliente.nombre if v.cliente else "—",
        cliente_telefono=v.cliente.telefono if v.cliente else None,
        cliente_email=v.cliente.email if v.cliente else None,
        cliente_direccion=v.cliente.direccion if v.cliente else None,
        cliente_direccion_laboral=v.cliente.direccion_laboral if v.cliente else None,
        latitud_residencia=float(v.cliente.latitud_residencia) if v.cliente and v.cliente.latitud_residencia is not None else None,
        longitud_residencia=float(v.cliente.longitud_residencia) if v.cliente and v.cliente.longitud_residencia is not None else None,
        latitud_trabajo=float(v.cliente.latitud_trabajo) if v.cliente and v.cliente.latitud_trabajo is not None else None,
        longitud_trabajo=float(v.cliente.longitud_trabajo) if v.cliente and v.cliente.longitud_trabajo is not None else None,
        productos_resumen=productos,
        costo_total_usd=costo if ver_costos else None,
        margen_usd=margen,
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
        cuotas_totales=len(cuotas_ordenadas),
        cuotas=cuotas_resp,
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
    return [_build_panel_item(db, v, usuario) for v in ventas if Decimal(str(v.total_usd)) - sum(Decimal(str(c.monto_usd)) for c in v.cobros) > 0]


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
    usuario_header: Usuario = Depends(require_cobrador_o_superior),
):
    try:
        return _registrar_cobro_interno(db, cobro, usuario_header)
    except HTTPException:
        raise
    except IntegrityError as exc:
        logger.warning("IntegrityError registrando cobro venta=%s", cobro.venta_id, exc_info=exc)
        raise HTTPException(
            status_code=400,
            detail="No se pudo registrar el cobro. Verifica los datos o intenta de nuevo.",
        ) from exc
    except Exception as exc:
        logger.exception(
            "Error no controlado registrando cobro venta=%s monto=%s",
            cobro.venta_id,
            cobro.monto_usd,
        )
        raise HTTPException(
            status_code=400,
            detail="No se pudo registrar el cobro. Verifica los datos e intenta de nuevo.",
        ) from exc


def _registrar_cobro_interno(
    db: Session,
    cobro: CobroCreate,
    usuario_header: Usuario,
) -> CobroResponse:
    empresa_actual = obtener_empresa_tenant(db, usuario_header)

    venta = (
        db.query(Venta)
        .options(joinedload(Venta.cobros), joinedload(Venta.cliente), joinedload(Venta.cuotas))
        .filter(Venta.id == str(cobro.venta_id))
        .first()
    )
    if not venta:
        raise HTTPException(status_code=400, detail="La venta indicada no existe")
    if str(venta.empresa_id) != str(empresa_actual.id):
        raise HTTPException(status_code=400, detail="La venta no pertenece a la empresa actual")

    cobrador = _resolver_cobrador(db, empresa_actual.id, cobro.cobrador_id, usuario_header)

    cobrado = sum(Decimal(str(c.monto_usd)) for c in (venta.cobros or []))
    saldo = Decimal(str(venta.total_usd)) - cobrado
    monto = Decimal(str(cobro.monto_usd))
    if monto <= 0:
        raise HTTPException(status_code=400, detail="El monto del cobro debe ser mayor a cero")
    if monto > saldo + Decimal("0.01"):
        raise HTTPException(
            status_code=400,
            detail=f"Monto excede saldo pendiente (${float(saldo):.2f})",
        )

    try:
        moneda = MonedaPago(cobro.moneda_pago)
    except ValueError:
        raise HTTPException(status_code=400, detail="Moneda de pago inválida")

    from app.core.pb_orm.ids import id_pocketbase_desde_cualquiera, nuevo_id_pocketbase

    cobro_id = id_pocketbase_desde_cualquiera(cobro.id) if cobro.id else nuevo_id_pocketbase()
    canal = cobro.canal or ("transferencia" if cobro.es_transferencia else None)
    electronico = canal in ("transferencia", "pago_movil") or bool(cobro.es_transferencia)
    cuenta_destino = None
    if electronico and canal in ("transferencia", "pago_movil"):
        cuenta_destino = resolver_cuenta_transferencia(
            db, empresa_actual.id, cobro.cuenta_bancaria_id, canal=canal
        )

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
        es_transferencia=electronico,
        referencia_pago=(cobro.referencia_pago or "").strip() or None,
        comprobante_base64=cobro.comprobante_base64,
        cuenta_bancaria_id=cuenta_destino.id if cuenta_destino else None,
        verificado=True,
    )

    db.add(nuevo_cobro)
    db.flush()
    _asegurar_cobro_en_lista_venta(venta, nuevo_cobro)
    recien_verificados = _actualizar_estado_venta(db, venta, nuevo_cobro, usuario_header)
    try:
        aplicar_abono_a_cuotas(db, venta, monto)
    except Exception:
        logger.exception("No se pudo aplicar abono a cuotas venta=%s", venta.id)

    if venta.cliente:
        try:
            if nuevo_cobro.verificado and nuevo_cobro not in recien_verificados:
                actualizar_score_por_cobro(db, venta, nuevo_cobro)
            for cobro_previo in recien_verificados:
                actualizar_score_por_cobro(db, venta, cobro_previo)
        except Exception:
            logger.exception("Score buró omitido tras cobro venta=%s", venta.id)
        try:
            actualizar_historial_comportamiento(db, venta.cliente)
        except Exception:
            logger.exception("Historial cliente omitido tras cobro venta=%s", venta.id)

    try:
        generar_asiento_cobro(db, nuevo_cobro)
    except Exception:
        logger.exception("Asiento contable omitido para cobro=%s", nuevo_cobro.id)

    db.commit()

    try:
        db.refresh(nuevo_cobro)
    except Exception:
        logger.exception("Refresh cobro=%s falló tras commit", nuevo_cobro.id)

    try:
        enviar_recibo_cobro(db, venta, nuevo_cobro)
    except Exception:
        logger.exception("No se pudo enviar recibo de cobro por correo")

    return _respuesta_cobro(nuevo_cobro, venta)


@router.post("/{cobro_id}/enviar-recibo", response_model=EnvioReciboResponse)
def enviar_recibo_cobro_manual(
    cobro_id: uuid.UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    cobro = (
        db.query(Cobro)
        .filter(Cobro.id == cobro_id, Cobro.empresa_id == usuario.empresa_id)
        .first()
    )
    if not cobro:
        raise HTTPException(status_code=404, detail="Cobro no encontrado")
    venta = (
        db.query(Venta)
        .options(joinedload(Venta.cliente), joinedload(Venta.cobros), joinedload(Venta.cuotas))
        .filter(Venta.id == cobro.venta_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    exito, mensaje = enviar_recibo_cobro(db, venta, cobro)
    email = venta.cliente.email if venta.cliente else None
    if not exito:
        raise HTTPException(status_code=400, detail=mensaje)
    return EnvioReciboResponse(exito=exito, mensaje=mensaje, email=email)


@router.post("/{cobro_id}/comprobante/whatsapp", response_model=WhatsappReporteResponse)
def enviar_comprobante_cobro_whatsapp(
    cobro_id: uuid.UUID,
    body: ComprobanteWhatsappRequest | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    """Envía la foto del comprobante del cobro al WhatsApp del administrador."""
    cobro = (
        db.query(Cobro)
        .filter(Cobro.id == cobro_id, Cobro.empresa_id == usuario.empresa_id)
        .first()
    )
    if not cobro:
        raise HTTPException(status_code=404, detail="Cobro no encontrado")
    if not cobro.es_transferencia:
        raise HTTPException(
            status_code=400,
            detail="Este cobro no es por transferencia ni pago móvil",
        )
    if not cobro.comprobante_base64:
        raise HTTPException(
            status_code=400,
            detail="Adjunte la foto del comprobante para enviarla por WhatsApp",
        )

    venta = (
        db.query(Venta)
        .options(joinedload(Venta.cliente))
        .filter(Venta.id == cobro.venta_id, Venta.empresa_id == usuario.empresa_id)
        .first()
    )
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")

    metodo = (body.metodo if body and body.metodo else "") or ""
    if metodo not in ("transferencia", "pago_movil") and cobro.cuenta_bancaria_id:
        cuenta = db.query(CuentaBancaria).filter(CuentaBancaria.id == cobro.cuenta_bancaria_id).first()
        if cuenta and cuenta.canal in ("transferencia", "pago_movil"):
            metodo = cuenta.canal
    if metodo not in ("transferencia", "pago_movil"):
        metodo = "transferencia"

    try:
        telefono = telefono_administrador(db, usuario.empresa_id)
        destino = normalizar_telefono(telefono)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    cliente = venta.cliente.nombre if venta.cliente else "Cliente"
    caption = armar_caption_comprobante(
        cliente,
        f"${float(cobro.monto_usd):.2f} USD",
        cobro.referencia_pago,
        metodo,
    )
    ok, mensaje = enviar_imagen(
        destino,
        None,
        caption,
        imagen_base64=cobro.comprobante_base64,
    )
    if not ok:
        raise HTTPException(status_code=estado_http_whatsapp(mensaje), detail=mensaje)
    return WhatsappReporteResponse(enviado=True, telefono=destino, mensaje=mensaje)


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
