from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Producto, PrecioProducto, TipoCliente
from app.schemas.core import ProductoCreate, ProductoResponse
from typing import List

router = APIRouter()


@router.post("/", response_model=ProductoResponse)
def crear_producto(producto: ProductoCreate, db: Session = Depends(get_db)):
    empresa_actual = obtener_empresa_tenant(db)

    nuevo_producto = Producto(
        nombre=producto.nombre,
        precio_usd=producto.precio_base_usd,
        stock=int(producto.stock_actual),
        empresa_id=empresa_actual.id,
    )

    db.add(nuevo_producto)
    db.flush()

    if producto.precio_detal_usd is not None:
        db.add(PrecioProducto(
            producto_id=nuevo_producto.id,
            tipo_cliente=TipoCliente.DETAL,
            precio_usd=producto.precio_detal_usd,
        ))
    if producto.precio_mayorista_usd is not None:
        db.add(PrecioProducto(
            producto_id=nuevo_producto.id,
            tipo_cliente=TipoCliente.MAYORISTA,
            precio_usd=producto.precio_mayorista_usd,
        ))

    db.commit()
    db.refresh(nuevo_producto)

    return nuevo_producto


@router.get("/", response_model=List[ProductoResponse])
def listar_productos(db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    return db.query(Producto).filter(Producto.empresa_id == empresa.id).all()
