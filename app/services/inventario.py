from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.core import (
    Producto,
    LoteInventario,
    Almacen,
    PrecioProducto,
    TipoCliente,
    DetalleVenta,
    MovimientoInventario,
    TipoMovimientoInventario,
)


def obtener_almacen(db: Session, empresa_id, almacen_id=None) -> Almacen:
    if almacen_id:
        almacen = (
            db.query(Almacen)
            .filter(Almacen.id == almacen_id, Almacen.empresa_id == empresa_id)
            .first()
        )
        if not almacen:
            raise HTTPException(status_code=400, detail="Almacén no encontrado")
        return almacen

    almacen = (
        db.query(Almacen)
        .filter(Almacen.empresa_id == empresa_id, Almacen.es_principal.is_(True))
        .first()
    )
    if not almacen:
        almacen = db.query(Almacen).filter(Almacen.empresa_id == empresa_id).first()
    if not almacen:
        raise HTTPException(
            status_code=400,
            detail="Debes crear al menos un almacén antes de vender con inventario",
        )
    return almacen


def resolver_precio(db: Session, producto: Producto, tipo_cliente: TipoCliente) -> Decimal:
    precio = (
        db.query(PrecioProducto)
        .filter(
            PrecioProducto.producto_id == producto.id,
            PrecioProducto.tipo_cliente == tipo_cliente,
        )
        .first()
    )
    if precio:
        return Decimal(str(precio.precio_usd))
    return Decimal(str(producto.precio_usd))


def stock_en_lotes(db: Session, producto_id, almacen_id=None) -> int:
    q = db.query(LoteInventario).filter(
        LoteInventario.producto_id == producto_id,
        LoteInventario.cantidad > 0,
    )
    if almacen_id:
        q = q.filter(LoteInventario.almacen_id == almacen_id)
    return sum(l.cantidad for l in q.all())


def stock_disponible(db: Session, producto: Producto, almacen_id=None) -> int:
    return producto.stock + stock_en_lotes(db, producto.id, almacen_id)


def registrar_movimiento(
    db: Session,
    empresa_id,
    producto_id,
    almacen_id,
    lote_id,
    tipo: TipoMovimientoInventario,
    cantidad: int,
    referencia_tipo: str,
    referencia_id,
):
    db.add(
        MovimientoInventario(
            empresa_id=empresa_id,
            producto_id=producto_id,
            almacen_id=almacen_id,
            lote_id=lote_id,
            tipo=tipo,
            cantidad=cantidad,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
        )
    )


def descontar_stock(
    db: Session,
    empresa_id,
    producto_id,
    cantidad: int,
    almacen_id=None,
    referencia_tipo: str = "venta",
    referencia_id=None,
) -> Decimal:
    producto = (
        db.query(Producto)
        .filter(Producto.id == producto_id, Producto.empresa_id == empresa_id)
        .first()
    )
    if not producto:
        raise HTTPException(status_code=400, detail=f"Producto {producto_id} no encontrado")

    almacen = obtener_almacen(db, empresa_id, almacen_id)
    pendiente = cantidad
    costo_total = Decimal("0")

    if stock_disponible(db, producto, almacen.id) < cantidad:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente para '{producto.nombre}' en almacén '{almacen.nombre}'",
        )

    lotes = (
        db.query(LoteInventario)
        .filter(
            LoteInventario.producto_id == producto_id,
            LoteInventario.almacen_id == almacen.id,
            LoteInventario.cantidad > 0,
        )
        .order_by(LoteInventario.fecha_creacion.asc())
        .all()
    )

    for lote in lotes:
        if pendiente <= 0:
            break
        tomar = min(lote.cantidad, pendiente)
        lote.cantidad -= tomar
        pendiente -= tomar
        costo_total += Decimal(str(lote.costo_unitario_usd)) * tomar
        registrar_movimiento(
            db, empresa_id, producto_id, almacen.id, lote.id,
            TipoMovimientoInventario.SALIDA, tomar, referencia_tipo, referencia_id,
        )

    if pendiente > 0:
        producto.stock -= pendiente
        costo_total += Decimal(str(producto.precio_usd)) * Decimal(str(pendiente)) * Decimal("0.6")
        registrar_movimiento(
            db, empresa_id, producto_id, almacen.id, None,
            TipoMovimientoInventario.SALIDA, pendiente, referencia_tipo, referencia_id,
        )

    return costo_total


def calcular_total_detalles(
    db: Session,
    empresa_id,
    detalles,
    tipo_cliente_default: TipoCliente = TipoCliente.DETAL,
) -> Decimal:
    total = Decimal("0")
    for item in detalles:
        producto = (
            db.query(Producto)
            .filter(Producto.id == item.producto_id, Producto.empresa_id == empresa_id)
            .first()
        )
        if not producto:
            raise HTTPException(status_code=400, detail="Producto no encontrado en detalle de venta")
        tipo = TipoCliente(item.tipo_precio) if item.tipo_precio else tipo_cliente_default
        precio = resolver_precio(db, producto, tipo)
        total += precio * item.cantidad
    return total


def procesar_detalles_venta(
    db: Session,
    venta,
    detalles,
    almacen_id=None,
    tipo_cliente: TipoCliente = TipoCliente.DETAL,
) -> Decimal:
    total = Decimal("0")
    for item in detalles:
        producto = (
            db.query(Producto)
            .filter(Producto.id == item.producto_id, Producto.empresa_id == venta.empresa_id)
            .first()
        )
        if not producto:
            raise HTTPException(status_code=400, detail="Producto no encontrado en la venta")

        tipo = TipoCliente(item.tipo_precio) if item.tipo_precio else tipo_cliente
        precio = resolver_precio(db, producto, tipo)
        descontar_stock(
            db, venta.empresa_id, producto.id, item.cantidad, almacen_id,
            referencia_tipo="venta", referencia_id=venta.id,
        )

        db.add(
            DetalleVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                cantidad=item.cantidad,
                precio_unitario_usd=precio,
            )
        )
        total += precio * item.cantidad
    return total


def consultar_stock_producto(db: Session, empresa_id, producto_id, almacen_id=None) -> dict:
    producto = (
        db.query(Producto)
        .filter(Producto.id == producto_id, Producto.empresa_id == empresa_id)
        .first()
    )
    if not producto:
        raise HTTPException(status_code=400, detail="Producto no encontrado")

    almacenes = db.query(Almacen).filter(Almacen.empresa_id == empresa_id, Almacen.activo.is_(True))
    if almacen_id:
        almacenes = almacenes.filter(Almacen.id == almacen_id)

    por_almacen = []
    for alm in almacenes.all():
        en_lotes = stock_en_lotes(db, producto.id, alm.id)
        por_almacen.append({
            "almacen_id": alm.id,
            "almacen_nombre": alm.nombre,
            "stock_lotes": en_lotes,
            "stock_general_asignado": producto.stock if alm.es_principal else 0,
            "stock_total": en_lotes + (producto.stock if alm.es_principal else 0),
        })

    return {
        "producto_id": producto.id,
        "producto_nombre": producto.nombre,
        "stock_general": producto.stock,
        "stock_total_global": stock_disponible(db, producto),
        "por_almacen": por_almacen,
    }


def inventario_valorado(db: Session, empresa_id) -> list[dict]:
    productos = db.query(Producto).filter(
        Producto.empresa_id == empresa_id, Producto.activo.is_(True)
    ).all()
    resultado = []
    for p in productos:
        lotes = db.query(LoteInventario).filter(LoteInventario.producto_id == p.id).all()
        stock_lotes = sum(l.cantidad for l in lotes)
        if stock_lotes > 0:
            costo_prom = sum(Decimal(str(l.costo_unitario_usd)) * l.cantidad for l in lotes) / stock_lotes
        else:
            costo_prom = Decimal(str(p.precio_usd)) * Decimal("0.6")
        stock_total = p.stock + stock_lotes
        resultado.append({
            "producto_id": p.id,
            "producto_nombre": p.nombre,
            "stock_general": p.stock,
            "stock_lotes": stock_lotes,
            "stock_total": stock_total,
            "costo_promedio_usd": float(costo_prom),
            "valor_total_usd": float(costo_prom * stock_total),
        })
    return resultado
