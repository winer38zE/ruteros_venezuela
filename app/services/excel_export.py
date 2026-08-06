from io import BytesIO
from decimal import Decimal
from datetime import datetime
from typing import Optional
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from sqlalchemy.orm import Session, joinedload
from app.models.core import (
    AsientoContable,
    Venta,
    Cobro,
    ConfiguracionFiscal,
    MonedaPago,
    MovimientoFinanciero,
)
from app.services.inventario import inventario_valorado
from app.services.finanzas import calcular_nomina, calcular_resumen_financiero

# Colores corporativos ED NET PRO
HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
ACCENT_FILL = PatternFill("solid", fgColor="D6E4F0")
HEADER_FONT = Font(color="FFFFFF", bold=True, size=11)
TITLE_FONT = Font(bold=True, size=14, color="1F4E79")
SUBTITLE_FONT = Font(bold=True, size=11, color="1F4E79")
MONEY_FMT = "#,##0.00"
THIN = Side(style="thin", color="CCCCCC")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def _header_row(ws, row, headers, start_col=1):
    for i, title in enumerate(headers, start=start_col):
        cell = ws.cell(row=row, column=i, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = BORDER


def _money_cell(ws, row, col, value):
    cell = ws.cell(row=row, column=col, value=float(value))
    cell.number_format = MONEY_FMT
    cell.border = BORDER
    return cell


def _auto_width(ws):
    for col_cells in ws.columns:
        max_len = 0
        col_letter = None
        for cell in col_cells:
            if hasattr(cell, "column_letter"):
                col_letter = cell.column_letter
            if cell.value is not None:
                max_len = max(max_len, len(str(cell.value)))
        if col_letter:
            ws.column_dimensions[col_letter].width = min(max_len + 3, 45)


def _titulo_hoja(ws, titulo: str, subtitulo: str, merge_cols: int = 6):
    ws["A1"] = titulo
    ws["A1"].font = TITLE_FONT
    ws["A2"] = subtitulo
    ws["A2"].font = Font(size=10, color="444444")
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=merge_cols)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=merge_cols)


def obtener_metadatos_exportacion(
    db: Session,
    empresa_id,
    empresa_nombre: str,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> dict:
    fiscal = (
        db.query(ConfiguracionFiscal)
        .filter(ConfiguracionFiscal.empresa_id == empresa_id)
        .first()
    )

    ventas_q = db.query(Venta).filter(Venta.empresa_id == empresa_id)
    cobros_q = db.query(Cobro).filter(Cobro.empresa_id == empresa_id)
    asientos_q = db.query(AsientoContable).filter(AsientoContable.empresa_id == empresa_id)

    if fecha_desde:
        ventas_q = ventas_q.filter(Venta.fecha >= fecha_desde)
        cobros_q = cobros_q.filter(Cobro.fecha >= fecha_desde)
        asientos_q = asientos_q.filter(AsientoContable.fecha >= fecha_desde)
    if fecha_hasta:
        ventas_q = ventas_q.filter(Venta.fecha <= fecha_hasta)
        cobros_q = cobros_q.filter(Cobro.fecha <= fecha_hasta)
        asientos_q = asientos_q.filter(AsientoContable.fecha <= fecha_hasta)

    inv = inventario_valorado(db, empresa_id)
    valor_inventario = sum(i["valor_total_usd"] for i in inv)

    mov_q = db.query(MovimientoFinanciero).filter(MovimientoFinanciero.empresa_id == empresa_id)
    if fecha_desde:
        mov_q = mov_q.filter(MovimientoFinanciero.fecha >= fecha_desde)
    if fecha_hasta:
        mov_q = mov_q.filter(MovimientoFinanciero.fecha <= fecha_hasta)

    resumen_fin = calcular_resumen_financiero(db, empresa_id, fecha_desde, fecha_hasta)

    return {
        "empresa": empresa_nombre,
        "pais": fiscal.pais if fiscal else "VE",
        "rif": fiscal.rif if fiscal else None,
        "razon_social": fiscal.razon_social if fiscal else None,
        "total_ventas": ventas_q.count(),
        "total_cobros": cobros_q.count(),
        "total_asientos": asientos_q.count(),
        "productos_inventario": len(inv),
        "valor_inventario_usd": round(valor_inventario, 2),
        "total_movimientos": mov_q.count(),
        "total_entradas_usd": resumen_fin["total_entradas_usd"],
        "total_salidas_usd": resumen_fin["total_salidas_usd"],
        "nomina_pendiente_usd": resumen_fin["nomina_pendiente_usd"],
        "fecha_desde": fecha_desde.isoformat() if fecha_desde else None,
        "fecha_hasta": fecha_hasta.isoformat() if fecha_hasta else None,
    }


def generar_reporte_contable(
    db: Session,
    empresa_id,
    empresa_nombre: str,
    fecha_desde: Optional[datetime] = None,
    fecha_hasta: Optional[datetime] = None,
) -> BytesIO:
    wb = Workbook()

    fiscal = (
        db.query(ConfiguracionFiscal)
        .filter(ConfiguracionFiscal.empresa_id == empresa_id)
        .first()
    )
    pais = fiscal.pais if fiscal else "VE"
    rif = fiscal.rif if fiscal else "N/A"
    razon = fiscal.razon_social or empresa_nombre
    iva_pct = float(fiscal.iva_porcentaje) if fiscal else 16.0
    igtf_pct = float(fiscal.igtf_porcentaje) if fiscal else 3.0

    ventas_q = db.query(Venta).filter(Venta.empresa_id == empresa_id)
    cobros_q = db.query(Cobro).filter(Cobro.empresa_id == empresa_id)
    if fecha_desde:
        ventas_q = ventas_q.filter(Venta.fecha >= fecha_desde)
        cobros_q = cobros_q.filter(Cobro.fecha >= fecha_desde)
    if fecha_hasta:
        ventas_q = ventas_q.filter(Venta.fecha <= fecha_hasta)
        cobros_q = cobros_q.filter(Cobro.fecha <= fecha_hasta)

    ventas = ventas_q.all()
    cobros = cobros_q.all()

    ingresos = sum(Decimal(str(v.total_usd)) for v in ventas)
    cobrado = sum(Decimal(str(c.monto_usd)) for c in cobros)
    por_cobrar = ingresos - cobrado
    iva_est = ingresos * Decimal(str(iva_pct)) / Decimal("100")

    cobros_bs = sum(
        Decimal(str(c.monto_usd)) for c in cobros
        if c.moneda_pago in (MonedaPago.BOLIVAR, MonedaPago.PAGO_MOVIL, MonedaPago.TRANSFERENCIA)
    )
    cobros_divisa = sum(
        Decimal(str(c.monto_usd)) for c in cobros
        if c.moneda_pago in (MonedaPago.DOLAR, MonedaPago.EURO)
    )
    igtf_est = sum(
        Decimal(str(c.monto_usd)) * Decimal(str(igtf_pct)) / Decimal("100")
        for c in cobros
        if c.moneda_pago in (MonedaPago.DOLAR, MonedaPago.EURO)
    )

    inv_items = inventario_valorado(db, empresa_id)
    valor_inventario = sum(Decimal(str(i["valor_total_usd"])) for i in inv_items)

    resumen_fin = calcular_resumen_financiero(db, empresa_id, fecha_desde, fecha_hasta)
    nomina = calcular_nomina(db, empresa_id, fecha_desde, fecha_hasta)

    mov_q = db.query(MovimientoFinanciero).filter(MovimientoFinanciero.empresa_id == empresa_id)
    if fecha_desde:
        mov_q = mov_q.filter(MovimientoFinanciero.fecha >= fecha_desde)
    if fecha_hasta:
        mov_q = mov_q.filter(MovimientoFinanciero.fecha <= fecha_hasta)
    movimientos = mov_q.order_by(MovimientoFinanciero.fecha.asc()).all()

    # ── Hoja 1: Resumen Ejecutivo / Balance ──
    ws1 = wb.active
    ws1.title = "Resumen Ejecutivo"
    _titulo_hoja(
        ws1,
        "ED NET PRO — Reporte Ejecutivo Contable",
        f"{razon} | RIF: {rif} | País: {pais} | Generado: {datetime.utcnow():%Y-%m-%d %H:%M UTC}",
        4,
    )

    _header_row(ws1, 4, ["Concepto", "Monto USD", "Detalle"])
    rows = [
        ("Ingresos por Ventas (base imponible)", ingresos, "Sin IVA"),
        ("IVA estimado por pagar", iva_est, f"Tasa legal {iva_pct}%"),
        ("Total Cobrado (todos los medios)", cobrado, f"{len(cobros)} cobros"),
        ("  ↳ Cobros en Bolívares / Bs digital", cobros_bs, "Bs, Pago Móvil, Transferencia"),
        ("  ↳ Cobros en Divisas", cobros_divisa, "USD / EUR"),
        ("Cuentas por Cobrar pendientes", por_cobrar, "Ventas − Cobros"),
        ("IGTF estimado (divisas)", igtf_est, f"Tasa {igtf_pct}%"),
        ("Efectivo neto en Divisas", cobros_divisa - igtf_est, "Después de IGTF"),
        ("Valor del Inventario (corte actual)", valor_inventario, f"{len(inv_items)} productos"),
        ("Total Entradas (cobros + manuales)", Decimal(str(resumen_fin["total_entradas_usd"])), "Operativo"),
        ("Total Salidas / Gastos", Decimal(str(resumen_fin["total_salidas_usd"])), "Egresos"),
        ("Gastos de Moto", Decimal(str(resumen_fin["gastos_moto_usd"])), "Categoría moto"),
        ("Nómina Pendiente", Decimal(str(resumen_fin["nomina_pendiente_usd"])), "Por pagar"),
        ("Balance Neto Estimado", Decimal(str(resumen_fin["balance_neto_usd"])), "Entradas − Salidas"),
    ]
    start = 5
    for i, (concepto, monto, obs) in enumerate(rows):
        r = start + i
        ws1.cell(r, 1, concepto).border = BORDER
        _money_cell(ws1, r, 2, monto)
        ws1.cell(r, 3, obs).border = BORDER
        if concepto.startswith("  ↳"):
            ws1.cell(r, 1).font = Font(italic=True, color="555555")

    total_row = start + len(rows) + 1
    ws1.cell(total_row, 1, "TOTAL ACTIVO ESTIMADO").font = SUBTITLE_FONT
    ws1.cell(total_row, 1).fill = ACCENT_FILL
    tot_cell = ws1.cell(total_row, 2, f"=SUM(B{start}:B{start + len(rows) - 1})")
    tot_cell.number_format = MONEY_FMT
    tot_cell.font = Font(bold=True)
    tot_cell.fill = ACCENT_FILL
    ws1.freeze_panes = "A5"

    # ── Hoja 2: Libro Diario ──
    ws2 = wb.create_sheet("Libro Diario")
    _titulo_hoja(ws2, "Libro Diario Contable — Partida Doble", f"Período filtrado · Empresa: {razon}", 8)

    _header_row(
        ws2, 4,
        ["Fecha", "Referencia", "Cuenta", "Nombre Cuenta", "Débito USD", "Crédito USD", "Débito Bs", "Crédito Bs"],
    )

    asientos_q = (
        db.query(AsientoContable)
        .filter(AsientoContable.empresa_id == empresa_id)
        .options(joinedload(AsientoContable.lineas))
    )
    if fecha_desde:
        asientos_q = asientos_q.filter(AsientoContable.fecha >= fecha_desde)
    if fecha_hasta:
        asientos_q = asientos_q.filter(AsientoContable.fecha <= fecha_hasta)
    asientos = asientos_q.order_by(AsientoContable.fecha.asc()).all()

    row = 5
    first_data = row
    for asiento in asientos:
        ref = f"{asiento.referencia_tipo.value.upper()} {str(asiento.referencia_id)[:8]}"
        for linea in asiento.lineas:
            ws2.cell(row, 1, asiento.fecha.strftime("%Y-%m-%d %H:%M")).border = BORDER
            ws2.cell(row, 2, ref).border = BORDER
            ws2.cell(row, 3, linea.cuenta_codigo).border = BORDER
            ws2.cell(row, 4, linea.cuenta_nombre).border = BORDER
            _money_cell(ws2, row, 5, linea.debito_usd)
            _money_cell(ws2, row, 6, linea.credito_usd)
            _money_cell(ws2, row, 7, linea.debito_bs)
            _money_cell(ws2, row, 8, linea.credito_bs)
            row += 1

    last_data = row - 1
    if last_data >= first_data:
        tot = row + 1
        ws2.cell(tot, 4, "TOTALES").font = Font(bold=True)
        ws2.cell(tot, 4).fill = ACCENT_FILL
        for col in range(5, 9):
            letter = get_column_letter(col)
            c = ws2.cell(tot, col, f"=SUM({letter}{first_data}:{letter}{last_data})")
            c.number_format = MONEY_FMT
            c.font = Font(bold=True)
            c.fill = ACCENT_FILL

    ws2.freeze_panes = "A5"

    # ── Hoja 3: Inventario Valorado ──
    ws3 = wb.create_sheet("Inventario Valorado")
    _titulo_hoja(ws3, "Inventario Valorado al Corte", f"Costo promedio ponderado · {razon}", 6)

    _header_row(
        ws3, 4,
        ["Producto", "Stock General", "Stock en Lotes", "Stock Total", "Costo Prom. USD", "Valor Total USD"],
    )

    row = 5
    first_inv = row
    for item in inv_items:
        ws3.cell(row, 1, item["producto_nombre"]).border = BORDER
        ws3.cell(row, 2, item["stock_general"]).border = BORDER
        ws3.cell(row, 3, item["stock_lotes"]).border = BORDER
        ws3.cell(row, 4, item["stock_total"]).border = BORDER
        _money_cell(ws3, row, 5, item["costo_promedio_usd"])
        _money_cell(ws3, row, 6, item["valor_total_usd"])
        row += 1

    last_inv = row - 1
    if last_inv >= first_inv:
        tot = row + 1
        ws3.cell(tot, 5, "TOTAL INVENTARIO USD").font = Font(bold=True)
        ws3.cell(tot, 5).fill = ACCENT_FILL
        c = ws3.cell(tot, 6, f"=SUM(F{first_inv}:F{last_inv})")
        c.number_format = MONEY_FMT
        c.font = Font(bold=True)
        c.fill = ACCENT_FILL

    ws3.freeze_panes = "A5"

    # ── Hoja 4: Movimientos Financieros ──
    ws4 = wb.create_sheet("Movimientos Financieros")
    _titulo_hoja(ws4, "Entradas y Salidas — Control Financiero", f"Empresa: {razon}", 6)
    _header_row(ws4, 4, ["Fecha", "Tipo", "Categoría", "Monto USD", "Descripción", "Empleado"])

    row = 5
    first_mov = row
    for m in movimientos:
        ws4.cell(row, 1, m.fecha.strftime("%Y-%m-%d %H:%M")).border = BORDER
        ws4.cell(row, 2, m.tipo.value.upper()).border = BORDER
        ws4.cell(row, 3, m.categoria.value.replace("_", " ").title()).border = BORDER
        _money_cell(ws4, row, 4, m.monto_usd)
        ws4.cell(row, 5, m.descripcion).border = BORDER
        ws4.cell(row, 6, str(m.empleado_id)[:8] if m.empleado_id else "—").border = BORDER
        row += 1

    last_mov = row - 1
    if last_mov >= first_mov:
        tot = row + 1
        ws4.cell(tot, 3, "TOTAL SALIDAS").font = Font(bold=True)
        ws4.cell(tot, 3).fill = ACCENT_FILL
        entradas_mov = sum(
            Decimal(str(m.monto_usd)) for m in movimientos
            if m.tipo.value == "entrada"
        )
        salidas_mov = sum(
            Decimal(str(m.monto_usd)) for m in movimientos
            if m.tipo.value == "salida"
        )
        ws4.cell(tot, 4, float(entradas_mov - salidas_mov)).number_format = MONEY_FMT

    ws4.freeze_panes = "A5"

    # ── Hoja 5: Nómina ──
    ws5 = wb.create_sheet("Nomina Empleados")
    _titulo_hoja(
        ws5,
        "Nómina — Comisiones y Pagos Pendientes",
        f"Comisión vendedor: ${nomina['comision_vendedor_por_articulo_usd']}/artículo · "
        f"Cobrador: {nomina['comision_cobrador_porcentaje']}%",
        8,
    )
    _header_row(
        ws5, 4,
        ["Empleado", "Rol", "Artículos", "Comisión Ventas", "Cobrado", "Comisión Cobros", "Pagado", "Pendiente"],
    )

    row = 5
    first_nom = row
    for emp in nomina["empleados"]:
        ws5.cell(row, 1, emp["empleado_nombre"]).border = BORDER
        ws5.cell(row, 2, emp["rol"]).border = BORDER
        ws5.cell(row, 3, emp["articulos_vendidos"]).border = BORDER
        _money_cell(ws5, row, 4, emp["comision_ventas_usd"])
        _money_cell(ws5, row, 5, emp["total_cobrado_usd"])
        _money_cell(ws5, row, 6, emp["comision_cobros_usd"])
        _money_cell(ws5, row, 7, emp["total_pagado_usd"])
        _money_cell(ws5, row, 8, emp["pendiente_usd"])
        row += 1

    last_nom = row - 1
    if last_nom >= first_nom:
        tot = row + 1
        ws5.cell(tot, 7, "TOTAL PENDIENTE").font = Font(bold=True)
        ws5.cell(tot, 7).fill = ACCENT_FILL
        c = ws5.cell(tot, 8, f"=SUM(H{first_nom}:H{last_nom})")
        c.number_format = MONEY_FMT
        c.font = Font(bold=True)
        c.fill = ACCENT_FILL

    ws5.freeze_panes = "A5"

    for ws in (ws1, ws2, ws3, ws4, ws5):
        _auto_width(ws)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer
