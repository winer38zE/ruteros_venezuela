from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Optional, Tuple

from sqlalchemy.orm import Session, joinedload

from app.models.core import (
    ConfiguracionNomina,
    CuentaBancariaEmpleado,
    Cobro,
    EstadoPagoNomina,
    EstadoVenta,
    PagoNomina,
    Pais,
    RolUsuario,
    Usuario,
    Venta,
)
def _d(val) -> Decimal:
    return Decimal(str(val))


def periodo_nomina_para_fecha(cfg: ConfiguracionNomina, ref: date) -> Tuple[date, date]:
    dias = int(cfg.dias_periodo_nomina or 8)
    ancla = cfg.fecha_ancla_periodo or ref
    if ref < ancla:
        inicio = ancla
    else:
        delta = (ref - ancla).days
        bloque = delta // dias
        inicio = ancla + timedelta(days=bloque * dias)
    fin = inicio + timedelta(days=dias - 1)
    return inicio, fin


def periodo_nomina_actual(db: Session, empresa_id) -> Tuple[date, date, ConfiguracionNomina]:
    from app.services.finanzas import _obtener_config_nomina

    cfg = _obtener_config_nomina(db, empresa_id)
    inicio, fin = periodo_nomina_para_fecha(cfg, date.today())
    return inicio, fin, cfg


def _rango_datetime(desde: date, hasta: date) -> Tuple[datetime, datetime]:
    return (
        datetime.combine(desde, time.min),
        datetime.combine(hasta, time.max),
    )


def _sueldo_base_empleado(
    emp: Usuario,
    cfg: ConfiguracionNomina,
    pais: Optional[Pais] = None,
    *,
    sueldo_legal_regla: Decimal | None = None,
) -> Decimal:
    base = _d(emp.sueldo_base_usd or 0)
    if base > 0:
        return base
    if sueldo_legal_regla is not None and sueldo_legal_regla > 0:
        return sueldo_legal_regla
    if pais is not None and _d(pais.sueldo_base_legal or 0) > 0:
        return _d(pais.sueldo_base_legal)
    if emp.rol == RolUsuario.COBRADOR:
        return _d(cfg.sueldo_base_cobrador_usd or 0)
    return _d("0")


def calcular_linea_empleado(
    db: Session,
    empresa_id,
    emp: Usuario,
    cfg: ConfiguracionNomina,
    fecha_desde: datetime,
    fecha_hasta: datetime,
    pais: Optional[Pais] = None,
) -> dict:
    from app.services.payroll_rules import parametros_nomina_desde_reglas

    params = parametros_nomina_desde_reglas(db, pais)
    sueldo_regla = _d(params.get("sueldo_base_legal", 0))
    comision_por_venta = _d(cfg.comision_vendedor_por_venta_usd)
    pct_cobrador = _d(cfg.comision_cobrador_porcentaje)
    pct_venta_pais = _d(params.get("porcentaje_comision_venta", 0))
    pct_cobro_pais = _d(params.get("porcentaje_comision_cobro", 0))
    if pct_cobro_pais > 0:
        pct_cobrador = pct_cobro_pais
    base = _sueldo_base_empleado(
        emp,
        cfg,
        pais=pais,
        sueldo_legal_regla=sueldo_regla,
    )

    num_ventas = 0
    comision_ventas = _d("0")
    total_cobrado = _d("0")
    comision_cobros = _d("0")
    articulos = 0

    if emp.rol == RolUsuario.VENDEDOR:
        ventas = (
            db.query(Venta)
            .options(joinedload(Venta.detalles))
            .filter(
                Venta.empresa_id == empresa_id,
                Venta.vendedor_id == emp.id,
                Venta.fecha >= fecha_desde,
                Venta.fecha <= fecha_hasta,
                Venta.estado != EstadoVenta.BORRADOR,
            )
            .all()
        )
        num_ventas = len(ventas)
        total_ventas_usd = sum(_d(v.total_usd) for v in ventas)
        if pct_venta_pais > 0:
            comision_ventas = total_ventas_usd * pct_venta_pais / _d("100")
        else:
            comision_ventas = _d(num_ventas) * comision_por_venta
        for v in ventas:
            for d in v.detalles:
                articulos += d.cantidad

    if emp.rol == RolUsuario.COBRADOR:
        cobros = (
            db.query(Cobro)
            .filter(
                Cobro.empresa_id == empresa_id,
                Cobro.cobrador_id == emp.id,
                Cobro.fecha >= fecha_desde,
                Cobro.fecha <= fecha_hasta,
            )
            .all()
        )
        total_cobrado = sum(_d(c.monto_usd) for c in cobros)
        comision_cobros = total_cobrado * pct_cobrador / _d("100")

    comision_total = comision_ventas + comision_cobros
    total_calc = base + comision_total

    cuenta = (
        db.query(CuentaBancariaEmpleado)
        .filter(
            CuentaBancariaEmpleado.usuario_id == emp.id,
            CuentaBancariaEmpleado.activa.is_(True),
        )
        .first()
    )

    return {
        "num_ventas": num_ventas,
        "articulos_vendidos": articulos,
        "comision_ventas_usd": float(comision_ventas),
        "total_cobrado_usd": float(total_cobrado),
        "comision_cobros_usd": float(comision_cobros),
        "comision_usd": float(comision_total),
        "sueldo_base_usd": float(base),
        "total_calculado_usd": float(total_calc),
        "tiene_cuenta_bancaria": cuenta is not None,
        "cuenta_verificada": bool(cuenta and cuenta.verificada_por_dueno),
    }


def generar_corte_nomina(
    db: Session,
    empresa_id,
    periodo_desde: Optional[date] = None,
    periodo_hasta: Optional[date] = None,
) -> list[PagoNomina]:
    from app.services.finanzas import _obtener_config_nomina

    cfg = _obtener_config_nomina(db, empresa_id)
    if periodo_desde is None or periodo_hasta is None:
        periodo_desde, periodo_hasta = periodo_nomina_para_fecha(cfg, date.today())

    dt_desde, dt_hasta = _rango_datetime(periodo_desde, periodo_hasta)

    empleados = (
        db.query(Usuario)
        .filter(
            Usuario.empresa_id == empresa_id,
            Usuario.activo.is_(True),
            Usuario.rol.in_([RolUsuario.VENDEDOR, RolUsuario.COBRADOR]),
        )
        .all()
    )

    creados: list[PagoNomina] = []
    for emp in empleados:
        existente = (
            db.query(PagoNomina)
            .filter(
                PagoNomina.empresa_id == empresa_id,
                PagoNomina.usuario_id == emp.id,
                PagoNomina.periodo_desde == periodo_desde,
                PagoNomina.periodo_hasta == periodo_hasta,
            )
            .first()
        )
        if existente:
            creados.append(existente)
            continue

        linea = calcular_linea_empleado(db, empresa_id, emp, cfg, dt_desde, dt_hasta)
        if linea["total_calculado_usd"] <= 0:
            continue

        pago = PagoNomina(
            empresa_id=empresa_id,
            usuario_id=emp.id,
            rol=emp.rol,
            periodo_desde=periodo_desde,
            periodo_hasta=periodo_hasta,
            num_ventas=linea["num_ventas"],
            total_cobrado_usd=linea["total_cobrado_usd"],
            sueldo_base_usd=linea["sueldo_base_usd"],
            comision_usd=linea["comision_usd"],
            total_calculado_usd=linea["total_calculado_usd"],
            estado=EstadoPagoNomina.PENDIENTE,
        )
        db.add(pago)
        db.flush()
        creados.append(pago)

    return creados


def marcar_pago_nomina_realizado(
    db: Session,
    empresa_id,
    dueno_id,
    pago_id,
    notas: Optional[str] = None,
) -> PagoNomina:
    pago = (
        db.query(PagoNomina)
        .options(joinedload(PagoNomina.usuario))
        .filter(PagoNomina.id == pago_id, PagoNomina.empresa_id == empresa_id)
        .first()
    )
    if not pago:
        raise ValueError("Registro de nómina no encontrado")
    if pago.estado == EstadoPagoNomina.REALIZADO:
        raise ValueError("Este pago ya está marcado como realizado")

    from app.services.finanzas import aprobar_pago_nomina

    dt_desde, dt_hasta = _rango_datetime(pago.periodo_desde, pago.periodo_hasta)
    mov = aprobar_pago_nomina(
        db,
        empresa_id,
        dueno_id,
        pago.usuario_id,
        float(pago.total_calculado_usd),
        dt_desde,
        dt_hasta,
        notas or f"Corte nómina {pago.periodo_desde} — {pago.periodo_hasta}",
    )

    pago.estado = EstadoPagoNomina.REALIZADO
    pago.movimiento_financiero_id = mov.id
    pago.fecha_pago = datetime.utcnow()
    pago.pagado_por_id = dueno_id
    if notas:
        pago.notas = notas
    db.flush()
    return pago
