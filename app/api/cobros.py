from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from app.core.db import get_db
from app.core.deps import (
    obtener_usuario_opcional,
    require_admin_o_dueno,
    require_cobrador_o_superior,
    require_operaciones,
    rol_confirma_pago,
)
from app.core.tenant import obtener_empresa_tenant
from app.api.empresas import resolver_cuenta_transferencia
from app.models.core import (
    Cobro, Venta, Usuario, MonedaPago, EstadoVenta, RolUsuario,
    Producto, DetalleVenta, EstadoCuota, CuentaBancaria, FrecuenciaPago, Cliente,
)
from app.schemas.core import (
    CobroCreate,
    CobroResponse,
    VentaPendienteResponse,
    CuotaAmortizacionResponse,
    EnvioReciboResponse,
    ComprobanteWhatsappRequest,
    WhatsappReporteResponse,
    CobradorOpcionResponse,
    PuntoSeguimientoResponse,
    SeguimientoRutaResponse,
)
from typing import List, Optional
from datetime import date, datetime
from decimal import Decimal
import enum
import uuid
from app.services.contabilidad import generar_asiento_cobro
from app.services.buro_credito import actualizar_historial_comportamiento, actualizar_score_por_cobro
from sqlalchemy import inspect as sa_inspect

from app.services.amortizacion import (
    aplicar_abono_a_cuotas,
    asegurar_cuota_unica_si_falta,
    monto_pendiente_cuota,
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


def _rel_lista(obj, nombre: str) -> list:
    """Relación no cargada o nula: lista vacía, sin lazy-load que reviente."""
    insp = sa_inspect(obj)
    if nombre in insp.unloaded:
        return []
    valor = getattr(obj, nombre, None)
    return list(valor or [])


def _rel_uno(obj, nombre: str):
    insp = sa_inspect(obj)
    if nombre in insp.unloaded:
        return None
    return getattr(obj, nombre, None)


def _texto_enum(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, enum.Enum):
        return str(valor.value).strip().lower()
    return str(valor).strip().lower()


def _es_credito(venta: Venta) -> bool:
    return _texto_enum(venta.frecuencia_pago) not in ("", "contado")


def _saldo_venta(venta: Venta) -> Decimal:
    cobrado = Decimal("0")
    for cobro in _rel_lista(venta, "cobros"):
        if cobro.monto_usd is None:
            continue
        cobrado += Decimal(str(cobro.monto_usd))
    return Decimal(str(venta.total_usd or 0)) - cobrado


def _venta_cobrable(venta: Venta) -> bool:
    """Crédito con saldo > 0 es cobrable aunque no tenga filas en cuotas_amortizacion.

    No exige el estado exacto 'pendiente': PocketBase guarda a veces el nombre
    del enum y el filtro `estado = 'pendiente'` dejaba la venta fuera.
    """
    if _texto_enum(venta.estado) == "borrador":
        return False
    if _saldo_venta(venta) <= Decimal("0.009"):
        return False
    if _es_credito(venta):
        return True
    return _texto_enum(venta.estado) in ("pendiente", "parcial", "por_verificar")


def _visible_para_usuario(usuario: Usuario, venta: Venta) -> bool:
    """Cobrador: solo clientes de su ruta (vendedor_id). Dueño y administrador: todas."""
    if usuario.rol != RolUsuario.COBRADOR:
        return True
    cliente = _rel_uno(venta, "cliente")
    if cliente is None or cliente.vendedor_id is None:
        return False
    return str(cliente.vendedor_id) == str(usuario.id)


def _productos_resumen(db: Session, venta: Venta) -> tuple[str, float]:
    detalles = _rel_lista(venta, "detalles")
    if not detalles:
        return "—", 0.0
    nombres = []
    costo = Decimal("0")
    for d in detalles:
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


def _venta_del_cobro(db: Session, cobro: Cobro) -> Venta | None:
    if not getattr(cobro, "venta_id", None):
        return None
    venta_id = str(cobro.venta_id)
    for venta in db.query(Venta).options(joinedload(Venta.cliente)).all():
        if str(venta.id) == venta_id:
            return venta
    return None


def _cobro_por_clave(db: Session, empresa_id, cobro_id: str | None, clave: str | None) -> Cobro | None:
    """Reintento con el mismo id o la misma clave: el cobro que ya se guardó."""
    filas = db.query(Cobro).all()
    if cobro_id:
        for fila in filas:
            if str(fila.id) == str(cobro_id):
                return fila
    if clave:
        for fila in filas:
            if str(getattr(fila, "empresa_id", "")) != str(empresa_id):
                continue
            if getattr(fila, "clave_idempotencia", None) == clave:
                return fila
    return None


def _respuesta_cobro(cobro: Cobro, venta: Venta | None) -> CobroResponse:
    """Arma la respuesta aunque PocketBase haya omitido defaults o la venta ya no exista.

    listar_mis_cobros devolvía el ORM crudo. FastAPI exige bool y datetime, y
    sincronizado/fecha_creacion/es_transferencia/verificado llegan en None:
    ValidationError → HTTP 500. El POST sí pasaba porque ya usaba esta función.
    """
    moneda = cobro.moneda_pago
    if isinstance(moneda, MonedaPago):
        moneda = moneda.value
    if not moneda:
        moneda = "dolar"
    estado = None
    if venta is not None and venta.estado is not None:
        estado = venta.estado.value if isinstance(venta.estado, enum.Enum) else str(venta.estado)
    fecha = cobro.fecha or cobro.fecha_creacion or datetime.utcnow()
    cliente = _rel_uno(venta, "cliente") if venta is not None else None
    lat = float(cobro.latitud) if getattr(cobro, "latitud", None) is not None else None
    lng = float(cobro.longitud) if getattr(cobro, "longitud", None) is not None else None
    tiene_gps = lat is not None and lng is not None
    return CobroResponse(
        id=str(cobro.id),
        empresa_id=str(cobro.empresa_id),
        venta_id=str(cobro.venta_id) if cobro.venta_id else "",
        cobrador_id=str(cobro.cobrador_id) if cobro.cobrador_id else "",
        fecha=fecha,
        monto_usd=float(cobro.monto_usd or 0),
        moneda_pago=str(moneda),
        tasa_usd_aplicada=float(cobro.tasa_usd_aplicada or 0),
        tasa_eur_aplicada=float(cobro.tasa_eur_aplicada or 0),
        sincronizado=bool(True if cobro.sincronizado is None else cobro.sincronizado),
        fecha_creacion=cobro.fecha_creacion or fecha,
        es_transferencia=bool(False if cobro.es_transferencia is None else cobro.es_transferencia),
        verificado=bool(True if cobro.verificado is None else cobro.verificado),
        referencia_pago=cobro.referencia_pago,
        tiene_comprobante=bool(getattr(cobro, "comprobante_base64", None)),
        estado_venta=estado,
        cuenta_bancaria_id=cobro.cuenta_bancaria_id,
        cliente_id=str(cobro.cliente_id) if getattr(cobro, "cliente_id", None) else (
            str(venta.cliente_id) if venta is not None and venta.cliente_id else None
        ),
        cliente_nombre=cliente.nombre if cliente and cliente.nombre else None,
        latitud=lat,
        longitud=lng,
        precision_metros=float(cobro.precision_metros) if getattr(cobro, "precision_metros", None) is not None else None,
        sin_ubicacion=not tiene_gps,
        notas=getattr(cobro, "notas", None),
    )


def _build_panel_item(db: Session, v: Venta, usuario: Usuario) -> VentaPendienteResponse:
    cobros = _rel_lista(v, "cobros")
    cobrado = sum(
        (Decimal(str(c.monto_usd)) for c in cobros if c.monto_usd is not None),
        Decimal("0"),
    )
    saldo = Decimal(str(v.total_usd or 0)) - cobrado
    productos, costo = _productos_resumen(db, v)
    proxima = proxima_cuota_pendiente(db, v.id)
    cuotas_ordenadas = sorted(_rel_lista(v, "cuotas"), key=lambda c: c.numero_cuota or 0)
    cuotas_pagadas = sum(1 for c in cuotas_ordenadas if c.estado == EstadoCuota.PAGADA)
    freq = _texto_enum(v.frecuencia_pago) or "contado"
    try:
        frecuencia_enum = FrecuenciaPago(freq)
    except ValueError:
        frecuencia_enum = (
            v.frecuencia_pago if isinstance(v.frecuencia_pago, FrecuenciaPago) else FrecuenciaPago.MENSUAL
        )
    ver_costos = _puede_ver_costos(usuario)
    margen = float(Decimal(str(v.total_usd or 0)) - Decimal(str(costo))) if ver_costos else None
    cliente = _rel_uno(v, "cliente")

    cuotas_resp = [
        CuotaAmortizacionResponse(**serializar_cuota(c, frecuencia_enum))
        for c in cuotas_ordenadas
    ]
    estado = _texto_enum(v.estado) or "pendiente"

    return VentaPendienteResponse(
        id=v.id,
        cliente_id=v.cliente_id,
        cliente_nombre=cliente.nombre if cliente and cliente.nombre else "—",
        cliente_telefono=cliente.telefono if cliente else None,
        cliente_email=cliente.email if cliente else None,
        cliente_direccion=cliente.direccion if cliente else None,
        cliente_direccion_laboral=cliente.direccion_laboral if cliente else None,
        latitud_residencia=float(cliente.latitud_residencia) if cliente and cliente.latitud_residencia is not None else None,
        longitud_residencia=float(cliente.longitud_residencia) if cliente and cliente.longitud_residencia is not None else None,
        latitud_trabajo=float(cliente.latitud_trabajo) if cliente and cliente.latitud_trabajo is not None else None,
        longitud_trabajo=float(cliente.longitud_trabajo) if cliente and cliente.longitud_trabajo is not None else None,
        productos_resumen=productos,
        costo_total_usd=costo if ver_costos else None,
        margen_usd=margen,
        total_usd=float(v.total_usd or 0),
        cobrado_usd=float(cobrado),
        saldo_pendiente_usd=float(saldo),
        frecuencia_pago=freq,
        tipo_credito=FRECUENCIA_LABEL.get(freq, freq),
        estado=estado,
        estado_cuenta=_estado_cuenta(proxima.fecha_vencimiento if proxima else None),
        proximo_pago=proxima.fecha_vencimiento if proxima else None,
        monto_proxima_cuota_usd=monto_pendiente_cuota(proxima) if proxima else float(saldo),
        cuotas_pagadas=cuotas_pagadas,
        cuotas_totales=len(cuotas_ordenadas) if cuotas_ordenadas else (1 if _es_credito(v) else 0),
        cuotas=cuotas_resp,
        fecha=v.fecha or datetime.utcnow(),
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
        .filter(Venta.empresa_id == usuario.empresa_id)
        .order_by(Venta.fecha.desc())
        .all()
    )
    # El filtro de estado se aplica en Python: un `estado = 'pendiente'` en
    # PocketBase no coincide si el valor guardado es "PENDIENTE" o "Pendiente",
    # y el historial igual muestra la etiqueta Pendiente.
    return [
        _build_panel_item(db, v, usuario)
        for v in ventas
        if _venta_cobrable(v) and _visible_para_usuario(usuario, v)
    ]


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
    cobros = [c for c in q.order_by(Cobro.fecha.desc()).all() if str(c.empresa_id) == str(usuario.empresa_id)]
    if usuario.rol == RolUsuario.COBRADOR:
        cobros = [c for c in cobros if str(c.cobrador_id) == str(usuario.id)]
    cobros.sort(key=lambda c: c.fecha or datetime.min, reverse=True)
    return [_respuesta_cobro(c, _venta_del_cobro(db, c)) for c in cobros]


def _nombre_cliente_cobro(db: Session, cobro: Cobro, venta: Venta | None) -> tuple[str | None, str]:
    cliente = _rel_uno(venta, "cliente") if venta is not None else None
    if cliente is None and getattr(cobro, "cliente_id", None):
        cliente = next(
            (c for c in db.query(Cliente).all() if str(c.id) == str(cobro.cliente_id)),
            None,
        )
    cliente_id = None
    if getattr(cobro, "cliente_id", None):
        cliente_id = str(cobro.cliente_id)
    elif venta is not None and venta.cliente_id:
        cliente_id = str(venta.cliente_id)
    nombre = cliente.nombre if cliente and cliente.nombre else "Cliente"
    return cliente_id, nombre


@router.get("/seguimiento/cobradores", response_model=List[CobradorOpcionResponse])
def listar_cobradores_seguimiento(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    roles = (RolUsuario.COBRADOR, RolUsuario.DUENO, RolUsuario.ADMINISTRADOR)
    personas = [
        u
        for u in db.query(Usuario).all()
        if str(u.empresa_id) == str(usuario.empresa_id) and u.rol in roles and u.activo is not False
    ]
    personas.sort(key=lambda u: (u.nombre or "").lower())
    return [
        CobradorOpcionResponse(
            id=str(u.id),
            nombre=u.nombre or "Sin nombre",
            rol=u.rol.value if isinstance(u.rol, enum.Enum) else str(u.rol),
        )
        for u in personas
    ]


@router.get("/seguimiento", response_model=SeguimientoRutaResponse)
def seguimiento_ruta(
    cobrador_id: str = Query(..., description="Usuario que cobró"),
    fecha: date = Query(..., description="Día del recorrido"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    """Puntos de cobro del día, ordenados por hora. No es ubicación continua."""
    cobrador = next(
        (
            u
            for u in db.query(Usuario).all()
            if str(u.id) == str(cobrador_id) and str(u.empresa_id) == str(usuario.empresa_id)
        ),
        None,
    )
    if not cobrador:
        raise HTTPException(status_code=404, detail="Cobrador no encontrado")
    puntos: list[PuntoSeguimientoResponse] = []
    for cobro in db.query(Cobro).all():
        if str(cobro.empresa_id) != str(usuario.empresa_id):
            continue
        if str(cobro.cobrador_id) != str(cobrador.id):
            continue
        momento = cobro.fecha
        if momento is None or momento.date() != fecha:
            continue
        venta = _venta_del_cobro(db, cobro)
        cliente_id, cliente_nombre = _nombre_cliente_cobro(db, cobro, venta)
        lat = float(cobro.latitud) if cobro.latitud is not None else None
        lng = float(cobro.longitud) if cobro.longitud is not None else None
        moneda = cobro.moneda_pago
        if isinstance(moneda, enum.Enum):
            moneda = moneda.value
        puntos.append(
            PuntoSeguimientoResponse(
                cobro_id=str(cobro.id),
                fecha=momento,
                cliente_id=cliente_id,
                cliente_nombre=cliente_nombre,
                monto_usd=float(cobro.monto_usd or 0),
                metodo=str(moneda or ""),
                latitud=lat,
                longitud=lng,
                precision_metros=float(cobro.precision_metros) if cobro.precision_metros is not None else None,
                sin_ubicacion=lat is None or lng is None,
            )
        )
    puntos.sort(key=lambda p: p.fecha)
    return SeguimientoRutaResponse(
        cobrador_id=str(cobrador.id),
        cobrador_nombre=cobrador.nombre or "Cobrador",
        fecha=fecha,
        puntos=puntos,
    )


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
        db.rollback()
        logger.warning("IntegrityError registrando cobro venta=%s", cobro.venta_id, exc_info=exc)
        from app.core.pb_orm.ids import id_pocketbase_desde_cualquiera

        clave_id = id_pocketbase_desde_cualquiera(cobro.id) if cobro.id else None
        existente = _cobro_por_clave(db, usuario_header.empresa_id, clave_id, cobro.clave_idempotencia)
        if existente and str(existente.empresa_id) == str(usuario_header.empresa_id):
            return _respuesta_cobro(existente, _venta_del_cobro(db, existente))
        raise HTTPException(
            status_code=400,
            detail="No se pudo registrar el cobro. Verifica los datos o intenta de nuevo.",
        ) from exc


def _registrar_cobro_interno(
    db: Session,
    cobro: CobroCreate,
    usuario_header: Usuario,
) -> CobroResponse:
    empresa_actual = obtener_empresa_tenant(db, usuario_header)

    from app.core.pb_orm.ids import id_pocketbase_desde_cualquiera, nuevo_id_pocketbase

    cobro_id = id_pocketbase_desde_cualquiera(cobro.id) if cobro.id else None
    clave = (cobro.clave_idempotencia or "").strip() or cobro_id
    existente = _cobro_por_clave(db, empresa_actual.id, cobro_id, clave)
    if existente:
        if str(existente.empresa_id) != str(empresa_actual.id):
            raise HTTPException(status_code=403, detail="Ese cobro pertenece a otra empresa")
        return _respuesta_cobro(existente, _venta_del_cobro(db, existente))

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

    if not cobro_id:
        cobro_id = nuevo_id_pocketbase()
        clave = clave or cobro_id
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
        sincronizado=True,
        fecha_creacion=datetime.utcnow(),
        clave_idempotencia=clave,
        cliente_id=venta.cliente_id,
        latitud=cobro.latitud if cobro.latitud is not None and cobro.longitud is not None else None,
        longitud=cobro.longitud if cobro.latitud is not None and cobro.longitud is not None else None,
        precision_metros=cobro.precision_metros if cobro.latitud is not None and cobro.longitud is not None else None,
        sin_ubicacion=not (cobro.latitud is not None and cobro.longitud is not None),
        notas=(cobro.notas or "").strip() or None,
    )

    db.add(nuevo_cobro)
    db.flush()
    _asegurar_cobro_en_lista_venta(venta, nuevo_cobro)
    recien_verificados = _actualizar_estado_venta(db, venta, nuevo_cobro, usuario_header)
    asegurar_cuota_unica_si_falta(db, venta)
    aplicar_abono_a_cuotas(db, venta, monto)

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
        f"{float(cobro.monto_usd):.2f} dólares",
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
    cobros = [
        c
        for c in db.query(Cobro).filter(Cobro.empresa_id == usuario.empresa_id).all()
        if str(c.empresa_id) == str(usuario.empresa_id)
    ]
    cobros.sort(key=lambda c: c.fecha or datetime.min, reverse=True)
    return [_respuesta_cobro(c, _venta_del_cobro(db, c)) for c in cobros]
