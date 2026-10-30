"""Generación y envío de comprobantes por correo."""
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.core import Cobro, Venta, Producto
from app.services.amortizacion import monto_pendiente_cuota, proxima_cuota_pendiente, serializar_cuota
from app.services.email_service import enviar_correo

FRECUENCIA_LABEL = {
    "semanal": "Semanal",
    "quincenal": "Quincenal",
    "mensual": "Mensual",
    "contado": "Contado",
}

MONEDA_LABEL = {
    "bolivar": "Bolívares (VES)",
    "dolar": "Dólares (USD)",
    "euro": "Euros (EUR)",
    "pago_movil": "Pago Móvil",
    "transferencia": "Transferencia / COP",
}


def _fmt_usd(val) -> str:
    return f"${float(val):,.2f} USD"


def _productos_html(db: Session, venta: Venta) -> str:
    filas = []
    for d in venta.detalles or []:
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        nombre = prod.nombre if prod else str(d.producto_id)[:8]
        subtotal = float(d.precio_unitario_usd or 0) * d.cantidad
        filas.append(
            f"<tr><td>{nombre}</td><td>{d.cantidad}</td>"
            f"<td>{_fmt_usd(d.precio_unitario_usd)}</td>"
            f"<td>{_fmt_usd(subtotal)}</td></tr>"
        )
    if not filas:
        return "<p>Sin detalle de productos.</p>"
    return (
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%'>"
        "<tr style='background:#f0f0f0'><th>Producto</th><th>Cant.</th><th>P.Unit.</th><th>Subtotal</th></tr>"
        + "".join(filas)
        + "</table>"
    )


def _cuotas_html(venta: Venta) -> str:
    if not venta.cuotas:
        return "<p>Venta de contado — sin plan de cuotas.</p>"
    freq = venta.frecuencia_pago.value if venta.frecuencia_pago else "contado"
    filas = []
    for c in sorted(venta.cuotas, key=lambda x: x.numero_cuota):
        data = serializar_cuota(c, venta.frecuencia_pago)
        fecha = c.fecha_vencimiento.strftime("%d/%m/%Y") if c.fecha_vencimiento else "—"
        filas.append(
            f"<tr><td>{data['etiqueta_periodo']}</td><td>{fecha}</td>"
            f"<td>{_fmt_usd(c.monto_usd)}</td><td>{data['estado_display']}</td></tr>"
        )
    return (
        f"<p><strong>Crédito {FRECUENCIA_LABEL.get(freq, freq)}</strong> — {len(venta.cuotas)} cuotas</p>"
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;width:100%'>"
        "<tr style='background:#f0f0f0'><th>Período</th><th>Fecha cobro</th><th>Monto</th><th>Estado</th></tr>"
        + "".join(filas)
        + "</table>"
    )


def html_recibo_venta(db: Session, venta: Venta) -> str:
    cliente = venta.cliente
    nombre = cliente.nombre if cliente else "Cliente"
    freq = venta.frecuencia_pago.value if venta.frecuencia_pago else "contado"
    cobrado = sum(Decimal(str(c.monto_usd)) for c in (venta.cobros or []))
    saldo = float(venta.total_usd) - float(cobrado)
    proxima = proxima_cuota_pendiente(db, venta.id)
    prox_txt = proxima.fecha_vencimiento.strftime("%d/%m/%Y") if proxima else "—"

    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#222">
    <h2 style="color:#10B981">Ruteros Venezuela — Comprobante de Venta</h2>
    <p>Hola <strong>{nombre}</strong>,</p>
    <p>Registramos tu compra con los siguientes detalles:</p>
    <ul>
      <li><strong>Total:</strong> {_fmt_usd(venta.total_usd)}</li>
      <li><strong>Forma de pago:</strong> {FRECUENCIA_LABEL.get(freq, freq)}</li>
      <li><strong>Abonado:</strong> {_fmt_usd(cobrado)}</li>
      <li><strong>Saldo pendiente:</strong> {_fmt_usd(saldo)}</li>
      <li><strong>Próximo cobro:</strong> {prox_txt}</li>
      <li><strong>Fecha venta:</strong> {venta.fecha.strftime('%d/%m/%Y %H:%M') if venta.fecha else '—'}</li>
    </ul>
    <h3>Productos</h3>
    {_productos_html(db, venta)}
    <h3>Plan de pagos</h3>
    {_cuotas_html(venta)}
    <p style="margin-top:24px;color:#666;font-size:12px">Mensaje automático — Ruteros Venezuela</p>
    </body></html>
    """


def html_recibo_cobro(db: Session, venta: Venta, cobro: Cobro) -> str:
    cliente = venta.cliente
    nombre = cliente.nombre if cliente else "Cliente"
    cobrado = sum(Decimal(str(c.monto_usd)) for c in (venta.cobros or []))
    saldo = float(venta.total_usd) - float(cobrado)
    proxima = proxima_cuota_pendiente(db, venta.id)
    prox_txt = proxima.fecha_vencimiento.strftime("%d/%m/%Y") if proxima else "—"
    prox_monto = monto_pendiente_cuota(proxima) if proxima else 0.0
    moneda = MONEDA_LABEL.get(
        cobro.moneda_pago.value if hasattr(cobro.moneda_pago, "value") else str(cobro.moneda_pago),
        str(cobro.moneda_pago),
    )

    return f"""
    <html><body style="font-family:Arial,sans-serif;color:#222">
    <h2 style="color:#00F2FE">Ruteros Venezuela — Recibo de Abono</h2>
    <p>Hola <strong>{nombre}</strong>,</p>
    <p>Confirmamos tu abono registrado:</p>
    <ul>
      <li><strong>Monto abonado:</strong> {_fmt_usd(cobro.monto_usd)}</li>
      <li><strong>Moneda de pago:</strong> {moneda}</li>
      <li><strong>Fecha:</strong> {cobro.fecha.strftime('%d/%m/%Y %H:%M') if cobro.fecha else '—'}</li>
      <li><strong>Total venta:</strong> {_fmt_usd(venta.total_usd)}</li>
      <li><strong>Total abonado:</strong> {_fmt_usd(cobrado)}</li>
      <li><strong>Saldo restante:</strong> {_fmt_usd(saldo)}</li>
      <li><strong>Próximo cobro:</strong> {prox_txt} — {_fmt_usd(prox_monto)}</li>
    </ul>
    <p style="margin-top:24px;color:#666;font-size:12px">Mensaje automático — Ruteros Venezuela</p>
    </body></html>
    """


def texto_recibo_venta(db: Session, venta: Venta) -> str:
    cliente = venta.cliente.nombre if venta.cliente else "Cliente"
    lineas = [
        f"Recibo de venta — {cliente}",
        f"Fecha: {venta.fecha.strftime('%d/%m/%Y') if venta.fecha else '—'}",
        f"Total: {_fmt_usd(venta.total_usd or 0)}",
        f"Estado: {venta.estado.value if getattr(venta, 'estado', None) else '—'}",
    ]
    for d in venta.detalles or []:
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first() if d.producto_id else None
        nombre = prod.nombre if prod else "Producto"
        lineas.append(f"- {nombre} x{d.cantidad} ({_fmt_usd(d.precio_unitario_usd or 0)})")
    cobrado = sum(Decimal(str(c.monto_usd or 0)) for c in (venta.cobros or []))
    saldo = float(venta.total_usd or 0) - float(cobrado)
    lineas.append(f"Saldo: {_fmt_usd(saldo)}")
    return "\n".join(lineas)


def enviar_recibo_venta(db: Session, venta: Venta) -> tuple[bool, str]:
    if not venta.cliente or not venta.cliente.email:
        return False, "El cliente no tiene correo registrado"
    html = html_recibo_venta(db, venta)
    asunto = f"Comprobante de venta — {_fmt_usd(venta.total_usd)}"
    return enviar_correo(venta.cliente.email, asunto, html)


def enviar_recibo_cobro(db: Session, venta: Venta, cobro: Cobro) -> tuple[bool, str]:
    if not venta.cliente or not venta.cliente.email:
        return False, "El cliente no tiene correo registrado"
    html = html_recibo_cobro(db, venta, cobro)
    asunto = f"Recibo de abono — {_fmt_usd(cobro.monto_usd)}"
    return enviar_correo(venta.cliente.email, asunto, html)
