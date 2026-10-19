from decimal import Decimal
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models.core import (
    ConfiguracionNomina,
    Empresa,
    MovimientoFinanciero,
    TipoMovimientoFinanciero,
    CategoriaMovimientoFinanciero,
    MonedaGasto,
    MetodoPagoSalida,
    Pais,
    Usuario,
    RolUsuario,
    Cobro,
)
from app.services.nomina import calcular_linea_empleado, _rango_datetime


def _d(val) -> Decimal:
    return Decimal(str(val))


def _moneda_operativa_empresa(db: Session, empresa_id) -> tuple[str, str]:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()
    if empresa is None or not empresa.pais_id:
        return "USD", "$"
    pais = db.query(Pais).filter(Pais.id == empresa.pais_id).first()
    if pais is None:
        return "USD", "$"
    return str(pais.moneda_principal), str(pais.simbolo_moneda)


def _moneda_operativa_pais(db: Session, pais_id) -> tuple[str, str]:
    if not pais_id:
        return "USD", "$"
    pais = db.query(Pais).filter(Pais.id == pais_id).first()
    if pais is None:
        return "USD", "$"
    return str(pais.moneda_principal), str(pais.simbolo_moneda)


def _obtener_pais_nomina(db: Session, pais_id) -> Pais | None:
    if not pais_id:
        return None
    return db.query(Pais).filter(Pais.id == pais_id, Pais.activo.is_(True)).first()


def _obtener_config_nomina(db: Session, empresa_id) -> ConfiguracionNomina:
    cfg = (
        db.query(ConfiguracionNomina)
        .filter(ConfiguracionNomina.empresa_id == empresa_id)
        .first()
    )
    if not cfg:
        cfg = ConfiguracionNomina(empresa_id=empresa_id)
        db.add(cfg)
        db.flush()
    return cfg


def _filtro_fecha(q, col, fecha_desde, fecha_hasta):
    if fecha_desde:
        q = q.filter(col >= fecha_desde)
    if fecha_hasta:
        q = q.filter(col <= fecha_hasta)
    return q


def _pagos_empleado(
    db: Session,
    empresa_id,
    empleado_id,
    fecha_desde: Optional[datetime],
    fecha_hasta: Optional[datetime],
) -> Decimal:
    q = db.query(MovimientoFinanciero).filter(
        MovimientoFinanciero.empresa_id == empresa_id,
        MovimientoFinanciero.empleado_id == empleado_id,
        MovimientoFinanciero.tipo == TipoMovimientoFinanciero.SALIDA,
        MovimientoFinanciero.categoria.in_([
            CategoriaMovimientoFinanciero.PAGO_VENDEDOR,
            CategoriaMovimientoFinanciero.PAGO_COBRADOR,
        ]),
    )
    q = _filtro_fecha(q, MovimientoFinanciero.fecha, fecha_desde, fecha_hasta)
    return sum(_d(m.monto_usd) for m in q.all())


def calcular_nomina(
    db: Session,
    empresa_id,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
    pais_id: Optional[str] = None,
) -> dict:
    cfg = _obtener_config_nomina(db, empresa_id)
    pais = _obtener_pais_nomina(db, pais_id)

    q_empleados = db.query(Usuario).filter(
        Usuario.empresa_id == empresa_id,
        Usuario.activo.is_(True),
        Usuario.rol.in_([RolUsuario.VENDEDOR, RolUsuario.COBRADOR]),
    )
    if pais_id:
        q_empleados = q_empleados.filter(Usuario.pais_id == pais_id)
    empleados = q_empleados.order_by(Usuario.nombre.asc()).all()

    if fecha_desde is None or fecha_hasta is None:
        from datetime import date as date_cls

        from app.services.nomina import periodo_nomina_para_fecha

        inicio, fin = periodo_nomina_para_fecha(cfg, date_cls.today())
        fecha_desde, fecha_hasta = _rango_datetime(inicio, fin)

    detalle: List[dict] = []

    from app.services.payroll_rules import parametros_nomina_desde_reglas

    params_regla = parametros_nomina_desde_reglas(db, pais)
    pct_cobrador_pais = _d(params_regla["porcentaje_comision_cobro"])
    pct_venta_pais = _d(params_regla["porcentaje_comision_venta"])
    comision_cobrador_pct = (
        float(pct_cobrador_pais)
        if pct_cobrador_pais > 0
        else float(cfg.comision_cobrador_porcentaje)
    )

    for emp in empleados:
        linea = calcular_linea_empleado(
            db,
            empresa_id,
            emp,
            cfg,
            fecha_desde,
            fecha_hasta,
            pais=pais,
        )
        total_calc = _d(linea["total_calculado_usd"])
        pagado = _pagos_empleado(db, empresa_id, emp.id, fecha_desde, fecha_hasta)
        pendiente = max(_d("0"), total_calc - pagado)

        detalle.append({
            "empleado_id": str(emp.id),
            "empleado_nombre": emp.nombre,
            "rol": emp.rol.value,
            "num_ventas": linea["num_ventas"],
            "articulos_vendidos": linea["articulos_vendidos"],
            "comision_ventas_usd": linea["comision_ventas_usd"],
            "total_cobrado_usd": linea["total_cobrado_usd"],
            "comision_cobros_usd": linea["comision_cobros_usd"],
            "sueldo_base_usd": linea["sueldo_base_usd"],
            "total_calculado_usd": float(total_calc),
            "total_pagado_usd": float(pagado),
            "pendiente_usd": float(pendiente),
            "tiene_cuenta_bancaria": linea["tiene_cuenta_bancaria"],
            "cuenta_verificada": linea["cuenta_verificada"],
        })

    total_pendiente = sum(d["pendiente_usd"] for d in detalle)
    if pais_id:
        moneda_principal, simbolo_moneda = _moneda_operativa_pais(db, pais_id)
    else:
        moneda_principal, simbolo_moneda = _moneda_operativa_empresa(db, empresa_id)

    sueldo_legal = float(params_regla["sueldo_base_legal"]) if pais else 0.0

    return {
        "periodo_desde": fecha_desde.isoformat() if fecha_desde else None,
        "periodo_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
        "moneda_principal": moneda_principal,
        "simbolo_moneda": simbolo_moneda,
        "comision_vendedor_por_articulo_usd": float(cfg.comision_vendedor_por_articulo_usd),
        "comision_vendedor_por_venta_usd": float(cfg.comision_vendedor_por_venta_usd),
        "comision_cobrador_porcentaje": comision_cobrador_pct,
        "sueldo_base_legal_pais": sueldo_legal,
        "salarios_por_moneda": params_regla.get("salarios_por_moneda") or {},
        "regla_nomina_verificada": bool(params_regla.get("regla_verificada")),
        "porcentaje_comision_venta_pais": float(pct_venta_pais),
        "porcentaje_comision_cobro_pais": float(pct_cobrador_pais),
        "empleados": detalle,
        "total_pendiente_usd": round(total_pendiente, 2),
    }


def calcular_resumen_financiero(
    db: Session,
    empresa_id,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> dict:
    mov_q = db.query(MovimientoFinanciero).filter(
        MovimientoFinanciero.empresa_id == empresa_id
    )
    mov_q = _filtro_fecha(mov_q, MovimientoFinanciero.fecha, fecha_desde, fecha_hasta)
    movimientos = mov_q.all()

    entradas = sum(
        _d(m.monto_usd) for m in movimientos
        if m.tipo == TipoMovimientoFinanciero.ENTRADA
    )
    salidas = sum(
        _d(m.monto_usd) for m in movimientos
        if m.tipo == TipoMovimientoFinanciero.SALIDA
    )
    gastos_moto = sum(
        _d(m.monto_usd) for m in movimientos
        if m.categoria == CategoriaMovimientoFinanciero.GASTO_MOTO
    )

    cobros_q = db.query(Cobro).filter(Cobro.empresa_id == empresa_id)
    cobros_q = _filtro_fecha(cobros_q, Cobro.fecha, fecha_desde, fecha_hasta)
    total_cobros = sum(_d(c.monto_usd) for c in cobros_q.all())

    nomina = calcular_nomina(db, empresa_id, fecha_desde, fecha_hasta)
    nomina_pendiente = _d(nomina["total_pendiente_usd"])

    total_entradas = entradas + total_cobros
    balance = total_entradas - salidas

    return {
        "total_entradas_usd": float(total_entradas),
        "total_salidas_usd": float(salidas),
        "gastos_moto_usd": float(gastos_moto),
        "nomina_pendiente_usd": float(nomina_pendiente),
        "balance_neto_usd": float(balance),
        "total_cobros_operativos_usd": float(total_cobros),
    }


def _normalizar_monto_usd(monto, moneda: str, tasa_aplicada=None) -> Decimal:
    m = _d(monto)
    if moneda == MonedaGasto.USD.value or moneda == "usd":
        return m
    if not tasa_aplicada or _d(tasa_aplicada) <= 0:
        raise ValueError("Se requiere tasa_aplicada para monedas VES o COP")
    return m / _d(tasa_aplicada)


def registrar_movimiento(
    db: Session,
    empresa_id,
    registrado_por_id,
    data: dict,
) -> MovimientoFinanciero:
    moneda = data.get("moneda", MonedaGasto.USD.value)
    monto_original = _d(data.get("monto") or data.get("monto_usd"))
    tasa = data.get("tasa_aplicada")
    monto_usd = _normalizar_monto_usd(monto_original, moneda, tasa)

    metodo = data.get("metodo_pago")
    mov = MovimientoFinanciero(
        empresa_id=empresa_id,
        tipo=TipoMovimientoFinanciero(data["tipo"]),
        categoria=CategoriaMovimientoFinanciero(data["categoria"]),
        monto_usd=monto_usd,
        monto_original=monto_original,
        moneda=MonedaGasto(moneda),
        metodo_pago=MetodoPagoSalida(metodo) if metodo else None,
        tasa_aplicada=_d(tasa) if tasa else None,
        descripcion=data["descripcion"],
        fecha=data.get("fecha") or datetime.utcnow(),
        registrado_por_id=registrado_por_id,
        empleado_id=data.get("empleado_id"),
        proveedor_id=data.get("proveedor_id"),
        comprobante_base64=data.get("comprobante_base64"),
        aprobado=data.get("aprobado", False),
        periodo_desde=data.get("periodo_desde"),
        periodo_hasta=data.get("periodo_hasta"),
    )
    db.add(mov)
    db.flush()
    return mov


def aprobar_pago_nomina(
    db: Session,
    empresa_id,
    registrado_por_id,
    empleado_id,
    monto_usd: float,
    periodo_desde: Optional[datetime],
    periodo_hasta: Optional[datetime],
    descripcion: Optional[str],
) -> MovimientoFinanciero:
    emp = db.query(Usuario).filter(
        Usuario.id == empleado_id,
        Usuario.empresa_id == empresa_id,
    ).first()
    if not emp:
        raise ValueError("Empleado no encontrado")

    if emp.rol == RolUsuario.VENDEDOR:
        categoria = CategoriaMovimientoFinanciero.PAGO_VENDEDOR
    elif emp.rol == RolUsuario.COBRADOR:
        categoria = CategoriaMovimientoFinanciero.PAGO_COBRADOR
    else:
        categoria = CategoriaMovimientoFinanciero.OPERACION_GENERAL

    desc = descripcion or f"Pago nómina — {emp.nombre} ({emp.rol.value})"

    return registrar_movimiento(
        db,
        empresa_id,
        registrado_por_id,
        {
            "tipo": "salida",
            "categoria": categoria.value,
            "monto": monto_usd,
            "moneda": "usd",
            "descripcion": desc,
            "empleado_id": empleado_id,
            "periodo_desde": periodo_desde,
            "periodo_hasta": periodo_hasta,
            "aprobado": True,
        },
    )
