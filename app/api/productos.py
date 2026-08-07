from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Producto, PrecioProducto, TipoCliente
from app.schemas.core import ProductoCreate, ProductoUpdate, ProductoResponse
from typing import List

router = APIRouter()


def _aplicar_precios_tier(db: Session, producto: Producto, body: ProductoCreate | ProductoUpdate) -> None:
    detal = getattr(body, "precio_detal_usd", None)
    mayorista = getattr(body, "precio_mayorista_usd", None)
    if detal is not None:
        existente = (
            db.query(PrecioProducto)
            .filter(PrecioProducto.producto_id == producto.id, PrecioProducto.tipo_cliente == TipoCliente.DETAL)
            .first()
        )
        if existente:
            existente.precio_usd = detal
        else:
            db.add(PrecioProducto(producto_id=producto.id, tipo_cliente=TipoCliente.DETAL, precio_usd=detal))
    if mayorista is not None:
        existente = (
            db.query(PrecioProducto)
            .filter(PrecioProducto.producto_id == producto.id, PrecioProducto.tipo_cliente == TipoCliente.MAYORISTA)
            .first()
        )
        if existente:
            existente.precio_usd = mayorista
        else:
            db.add(PrecioProducto(producto_id=producto.id, tipo_cliente=TipoCliente.MAYORISTA, precio_usd=mayorista))


@router.post("/", response_model=ProductoResponse)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    empresa_actual = obtener_empresa_tenant(db)

    if producto.sku:
        dup = (
            db.query(Producto)
            .filter(Producto.empresa_id == empresa_actual.id, Producto.sku == producto.sku)
            .first()
        )
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe un producto con ese SKU/código")

    nuevo_producto = Producto(
        nombre=producto.nombre,
        sku=producto.sku,
        categoria=producto.categoria,
        precio_usd=producto.precio_base_usd,
        precio_ves=producto.precio_ves,
        precio_cop=producto.precio_cop,
        costo_usd=producto.costo_usd,
        stock=int(producto.stock_actual),
        stock_minimo=producto.stock_minimo,
        empresa_id=empresa_actual.id,
    )

    db.add(nuevo_producto)
    db.flush()
    _aplicar_precios_tier(db, nuevo_producto, producto)

    db.commit()
    db.refresh(nuevo_producto)

    return nuevo_producto


@router.get("/", response_model=List[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    return (
        db.query(Producto)
        .filter(Producto.empresa_id == empresa.id, Producto.activo.is_(True))
        .order_by(Producto.nombre.asc())
        .all()
    )


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(producto_id: UUID, db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    producto = (
        db.query(Producto)
        .filter(Producto.id == producto_id, Producto.empresa_id == empresa.id)
        .first()
    )
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: UUID,
    body: ProductoUpdate,
    db: Session = Depends(get_db),
):
    empresa = obtener_empresa_tenant(db)
    producto = (
        db.query(Producto)
        .filter(Producto.id == producto_id, Producto.empresa_id == empresa.id)
        .first()
    )
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if body.sku is not None and body.sku != producto.sku:
        dup = (
            db.query(Producto)
            .filter(
                Producto.empresa_id == empresa.id,
                Producto.sku == body.sku,
                Producto.id != producto.id,
            )
            .first()
        )
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe un producto con ese SKU/código")

    if body.nombre is not None:
        producto.nombre = body.nombre
    if body.sku is not None:
        producto.sku = body.sku or None
    if body.categoria is not None:
        producto.categoria = body.categoria or None
    if body.precio_base_usd is not None:
        producto.precio_usd = body.precio_base_usd
    if body.precio_ves is not None:
        producto.precio_ves = body.precio_ves
    if body.precio_cop is not None:
        producto.precio_cop = body.precio_cop
    if body.costo_usd is not None:
        producto.costo_usd = body.costo_usd
    if body.stock_minimo is not None:
        producto.stock_minimo = body.stock_minimo
    if body.activo is not None:
        producto.activo = body.activo

    _aplicar_precios_tier(db, producto, body)

    db.commit()
    db.refresh(producto)
    return producto
