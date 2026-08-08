from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.db import get_db
from app.core.tenant import obtener_empresa_tenant
from app.models.core import (
    Almacen, LoteInventario, PrecioProducto, Producto, TipoCliente,
    MovimientoInventario, TipoMovimientoInventario,
)
from app.schemas.core import (
    AlmacenCreate, AlmacenResponse,
    LoteInventarioCreate, LoteInventarioResponse,
    PrecioProductoCreate, PrecioProductoResponse,
    StockProductoResponse, InventarioValoradoItem,
    MovimientoInventarioResponse, AjusteInventarioCreate,
)
from app.services.inventario import consultar_stock_producto, inventario_valorado, ajustar_stock_manual

router = APIRouter()


@router.post("/almacenes", response_model=AlmacenResponse)
def crear_almacen(almacen: AlmacenCreate, db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)

    if almacen.es_principal:
        db.query(Almacen).filter(
            Almacen.empresa_id == empresa.id, Almacen.es_principal.is_(True)
        ).update({"es_principal": False})

    nuevo = Almacen(empresa_id=empresa.id, **almacen.model_dump())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/almacenes", response_model=List[AlmacenResponse])
def listar_almacenes(db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    return (
        db.query(Almacen)
        .filter(Almacen.empresa_id == empresa.id, Almacen.activo.is_(True))
        .all()
    )


@router.post("/lotes", response_model=LoteInventarioResponse)
def registrar_lote(lote: LoteInventarioCreate, db: Session = Depends(get_db)):
    from decimal import Decimal
    from app.models.core import Proveedor

    empresa = obtener_empresa_tenant(db)

    producto = db.query(Producto).filter(
        Producto.id == lote.producto_id, Producto.empresa_id == empresa.id
    ).first()
    if not producto:
        raise HTTPException(status_code=400, detail="Producto no encontrado")

    almacen = db.query(Almacen).filter(
        Almacen.id == lote.almacen_id, Almacen.empresa_id == empresa.id
    ).first()
    if not almacen:
        raise HTTPException(status_code=400, detail="Almacén no encontrado")

    proveedor_id = lote.proveedor_id or producto.proveedor_id
    nuevo = LoteInventario(
        empresa_id=empresa.id,
        producto_id=lote.producto_id,
        almacen_id=lote.almacen_id,
        proveedor_id=proveedor_id,
        genera_deuda_proveedor=lote.genera_deuda_proveedor,
        numero_lote=lote.numero_lote,
        cantidad=lote.cantidad,
        costo_unitario_usd=lote.costo_unitario_usd,
        fecha_vencimiento=lote.fecha_vencimiento,
    )
    db.add(nuevo)
    db.flush()

    from app.services.inventario import registrar_movimiento
    registrar_movimiento(
        db, empresa.id, producto.id, almacen.id, nuevo.id,
        TipoMovimientoInventario.ENTRADA, lote.cantidad, "lote", nuevo.id,
    )

    if lote.genera_deuda_proveedor and proveedor_id:
        prov = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
        if prov:
            monto_deuda = Decimal(str(lote.costo_unitario_usd)) * lote.cantidad
            prov.saldo_deuda_usd = Decimal(str(prov.saldo_deuda_usd or 0)) + monto_deuda

    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/lotes", response_model=List[LoteInventarioResponse])
def listar_lotes(
    db: Session = Depends(get_db),
    producto_id: Optional[UUID] = Query(None),
    almacen_id: Optional[UUID] = Query(None),
):
    empresa = obtener_empresa_tenant(db)
    q = db.query(LoteInventario).filter(LoteInventario.empresa_id == empresa.id)
    if producto_id:
        q = q.filter(LoteInventario.producto_id == producto_id)
    if almacen_id:
        q = q.filter(LoteInventario.almacen_id == almacen_id)
    return q.all()


@router.post("/productos/{producto_id}/precios", response_model=PrecioProductoResponse)
def asignar_precio(producto_id: UUID, precio: PrecioProductoCreate, db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)

    producto = db.query(Producto).filter(
        Producto.id == producto_id, Producto.empresa_id == empresa.id
    ).first()
    if not producto:
        raise HTTPException(status_code=400, detail="Producto no encontrado")

    tipo = TipoCliente(precio.tipo_cliente)
    existente = (
        db.query(PrecioProducto)
        .filter(PrecioProducto.producto_id == producto.id, PrecioProducto.tipo_cliente == tipo)
        .first()
    )
    if existente:
        existente.precio_usd = precio.precio_usd
        db.commit()
        db.refresh(existente)
        return existente

    nuevo = PrecioProducto(
        producto_id=producto.id,
        tipo_cliente=tipo,
        precio_usd=precio.precio_usd,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.get("/productos/{producto_id}/precios", response_model=List[PrecioProductoResponse])
def listar_precios_producto(producto_id: UUID, db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    producto = db.query(Producto).filter(
        Producto.id == producto_id, Producto.empresa_id == empresa.id
    ).first()
    if not producto:
        raise HTTPException(status_code=400, detail="Producto no encontrado")
    return db.query(PrecioProducto).filter(PrecioProducto.producto_id == producto_id).all()


@router.get("/stock/{producto_id}", response_model=StockProductoResponse)
def consultar_stock(producto_id: UUID, db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    return consultar_stock_producto(db, empresa.id, producto_id)


@router.get("/stock", response_model=List[StockProductoResponse])
def consultar_stock_todos(db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    productos = db.query(Producto).filter(Producto.empresa_id == empresa.id).all()
    return [consultar_stock_producto(db, empresa.id, p.id) for p in productos]


@router.get("/valorado", response_model=List[InventarioValoradoItem])
def consultar_inventario_valorado(db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    return inventario_valorado(db, empresa.id)


@router.post("/movimiento", response_model=MovimientoInventarioResponse)
def registrar_movimiento_manual(body: AjusteInventarioCreate, db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    try:
        tipo = TipoMovimientoInventario(body.tipo)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tipo de movimiento inválido")

    mov = ajustar_stock_manual(
        db,
        empresa.id,
        body.producto_id,
        tipo,
        body.cantidad,
        body.motivo,
        body.almacen_id,
    )
    db.commit()
    db.refresh(mov)
    return mov


@router.get("/movimientos", response_model=List[MovimientoInventarioResponse])
def listar_movimientos(
    db: Session = Depends(get_db),
    producto_id: Optional[UUID] = Query(None),
    limit: int = Query(100, le=500),
):
    empresa = obtener_empresa_tenant(db)
    q = (
        db.query(MovimientoInventario)
        .filter(MovimientoInventario.empresa_id == empresa.id)
        .order_by(MovimientoInventario.fecha.desc())
    )
    if producto_id:
        q = q.filter(MovimientoInventario.producto_id == producto_id)
    return q.limit(limit).all()
