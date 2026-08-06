from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.core import (
    AsientoContable,
    LineaAsiento,
    ConfiguracionFiscal,
    Venta,
    Cobro,
    TipoReferenciaAsiento,
    MonedaPago,
)
from app.services.fiscal_engine import (
    _d,
    calcular_impuestos_venta,
    calcular_impuestos_cobro,
    CUENTAS,
)


def _obtener_fiscal(db: Session, empresa_id) -> ConfiguracionFiscal:
    fiscal = (
        db.query(ConfiguracionFiscal)
        .filter(ConfiguracionFiscal.empresa_id == empresa_id)
        .first()
    )
    if not fiscal:
        fiscal = ConfiguracionFiscal(empresa_id=empresa_id, pais="VE")
        db.add(fiscal)
        db.flush()
    return fiscal


def _asiento_existe(
    db: Session,
    empresa_id,
    referencia_tipo: TipoReferenciaAsiento,
    referencia_id,
) -> bool:
    return (
        db.query(AsientoContable)
        .filter(
            AsientoContable.empresa_id == empresa_id,
            AsientoContable.referencia_tipo == referencia_tipo,
            AsientoContable.referencia_id == referencia_id,
        )
        .first()
        is not None
    )


def _crear_linea(asiento_id, codigo, nombre, deb_usd, cred_usd, tasa_usd):
    deb_usd = _d(deb_usd)
    cred_usd = _d(cred_usd)
    tasa = _d(tasa_usd)
    return LineaAsiento(
        asiento_id=asiento_id,
        cuenta_codigo=codigo,
        cuenta_nombre=nombre,
        debito_usd=deb_usd,
        credito_usd=cred_usd,
        debito_bs=_d(deb_usd * tasa),
        credito_bs=_d(cred_usd * tasa),
    )


def generar_asiento_venta(db: Session, venta: Venta):
    if _asiento_existe(db, venta.empresa_id, TipoReferenciaAsiento.VENTA, venta.id):
        return None

    fiscal = _obtener_fiscal(db, venta.empresa_id)
    imp = calcular_impuestos_venta(fiscal, venta.total_usd)
    tasa = _d(venta.tasa_usd_aplicada)

    asiento = AsientoContable(
        empresa_id=venta.empresa_id,
        fecha=venta.fecha,
        referencia_tipo=TipoReferenciaAsiento.VENTA,
        referencia_id=venta.id,
        descripcion=f"Venta #{str(venta.id)[:8]}",
        tasa_usd_aplicada=tasa,
    )
    db.add(asiento)
    db.flush()

    cod_cxc, nom_cxc = CUENTAS["CXC"]
    cod_ing, nom_ing = CUENTAS["INGRESOS"]
    cod_iva, nom_iva = CUENTAS["IVA"]

    db.add(_crear_linea(asiento.id, cod_cxc, nom_cxc, imp.total_usd, 0, tasa))
    db.add(_crear_linea(asiento.id, cod_ing, nom_ing, 0, imp.base_usd, tasa))
    db.add(_crear_linea(asiento.id, cod_iva, nom_iva, 0, imp.iva_usd, tasa))

    return asiento


def generar_asiento_cobro(db: Session, cobro: Cobro):
    if _asiento_existe(db, cobro.empresa_id, TipoReferenciaAsiento.COBRO, cobro.id):
        return None

    fiscal = _obtener_fiscal(db, cobro.empresa_id)
    imp = calcular_impuestos_cobro(fiscal, cobro.monto_usd, cobro.moneda_pago)
    tasa = _d(cobro.tasa_usd_aplicada)

    if cobro.moneda_pago == MonedaPago.BOLIVAR:
        cod_caja, nom_caja = CUENTAS["CAJA_BS"]
    else:
        cod_caja, nom_caja = CUENTAS["CAJA_DIV"]

    cod_cxc, nom_cxc = CUENTAS["CXC"]
    cod_igtf, nom_igtf = CUENTAS["IGTF"]

    asiento = AsientoContable(
        empresa_id=cobro.empresa_id,
        fecha=cobro.fecha,
        referencia_tipo=TipoReferenciaAsiento.COBRO,
        referencia_id=cobro.id,
        descripcion=f"Cobro #{str(cobro.id)[:8]}",
        tasa_usd_aplicada=tasa,
    )
    db.add(asiento)
    db.flush()

    db.add(_crear_linea(asiento.id, cod_caja, nom_caja, imp.neto_cobro_usd, 0, tasa))
    if imp.igtf_usd > 0:
        db.add(_crear_linea(asiento.id, cod_igtf, nom_igtf, imp.igtf_usd, 0, tasa))
    db.add(_crear_linea(asiento.id, cod_cxc, nom_cxc, 0, imp.total_usd, tasa))

    return asiento


def calcular_resumen_contable(db: Session, empresa_id) -> dict:
    from app.models.core import Venta, Cobro

    ventas = db.query(Venta).filter(Venta.empresa_id == empresa_id).all()
    cobros = db.query(Cobro).filter(Cobro.empresa_id == empresa_id).all()
    asientos = (
        db.query(AsientoContable)
        .filter(AsientoContable.empresa_id == empresa_id)
        .count()
    )

    ingresos = sum(Decimal(str(v.total_usd)) for v in ventas)
    cobrado = sum(Decimal(str(c.monto_usd)) for c in cobros)

    fiscal = _obtener_fiscal(db, empresa_id)
    iva_est = ingresos * _d(fiscal.iva_porcentaje) / Decimal("100")

    return {
        "empresa_id": str(empresa_id),
        "pais": fiscal.pais,
        "total_ventas_usd": float(ingresos),
        "total_cobrado_usd": float(cobrado),
        "cuentas_por_cobrar_usd": float(ingresos - cobrado),
        "iva_estimado_usd": float(iva_est),
        "asientos_generados": asientos,
    }
