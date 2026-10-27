from datetime import date
from uuid import UUID
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.tenant import obtener_empresa_tenant
from app.core.deps import require_operaciones, obtener_usuario_actual
from app.models.core import (
    Empresa,
    Pais,
    Producto,
    PrecioProducto,
    TipoCliente,
    Proveedor,
    TipoTasaUsd,
    Usuario,
)
from app.schemas.core import ProductoCreate, ProductoUpdate, ProductoResponse
from app.services.tasas_cambio import (
    convertir_cop_a_usd,
    convertir_usd_a_ves,
    convertir_usd_a_cop,
    obtener_ultima_tasa,
)
from typing import List

router = APIRouter()


def _resolver_proveedor_pago(
    *,
    proveedor: str | None,
    condicion_pago: str | None,
    fecha_limite_pago: date | None,
) -> tuple[str | None, str | None, date | None]:
    prov = proveedor.strip() if proveedor and proveedor.strip() else None
    cond = (condicion_pago or "contado").strip().lower()
    if cond not in ("contado", "credito", "plazo"):
        cond = "contado"
    fecha = fecha_limite_pago if cond in ("credito", "plazo") else None
    return prov, cond, fecha


def _empresa_es_venezuela(db: Session, empresa: Empresa) -> bool:
    if not empresa.pais_id:
        return True
    pais = db.query(Pais).filter(Pais.id == empresa.pais_id).first()
    if not pais:
        return True
    return (pais.codigo_iso or "").upper() == "VE"


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


def _auto_precios(db: Session, empresa_id, precio_usd: float, tipo_tasa: str = "bcv") -> tuple:
    tasa = obtener_ultima_tasa(db, empresa_id)
    if not tasa:
        return None, None
    tipo = TipoTasaUsd(tipo_tasa)
    ves = convertir_usd_a_ves(Decimal(str(precio_usd)), tasa, tipo)
    cop = convertir_usd_a_cop(Decimal(str(precio_usd)), tasa)
    return float(ves), float(cop)


def _to_response(db: Session, producto: Producto) -> ProductoResponse:
    prov = db.query(Proveedor).filter(Proveedor.id == producto.proveedor_id).first() if producto.proveedor_id else None
    empresa = db.query(Empresa).filter(Empresa.id == producto.empresa_id).first()
    ves_calc, cop_calc = (None, None)
    if empresa and _empresa_es_venezuela(db, empresa):
        ves_calc, cop_calc = _auto_precios(db, producto.empresa_id, float(producto.precio_usd))
    return ProductoResponse(
        id=producto.id,
        empresa_id=producto.empresa_id,
        nombre=producto.nombre,
        sku=producto.sku,
        categoria=producto.categoria,
        precio_usd=float(producto.precio_usd),
        precio_ves=float(producto.precio_ves) if producto.precio_ves else None,
        precio_cop=float(producto.precio_cop) if producto.precio_cop else None,
        costo_usd=float(producto.costo_usd or 0),
        stock=producto.stock,
        stock_minimo=producto.stock_minimo or 0,
        activo=producto.activo,
        proveedor_id=producto.proveedor_id,
        proveedor_nombre=prov.nombre if prov else None,
        proveedor=producto.proveedor,
        condicion_pago=producto.condicion_pago,
        fecha_limite_pago=producto.fecha_limite_pago,
        precio_ves_calculado=ves_calc,
        precio_cop_calculado=cop_calc,
    )


@router.post("/", response_model=ProductoResponse)
def crear_producto(
    producto: ProductoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    empresa_actual = obtener_empresa_tenant(db, usuario)

    if producto.sku:
        dup = (
            db.query(Producto)
            .filter(Producto.empresa_id == empresa_actual.id, Producto.sku == producto.sku)
            .first()
        )
        if dup:
            raise HTTPException(status_code=400, detail="Ya existe un producto con ese SKU/código")

    es_ve = _empresa_es_venezuela(db, empresa_actual)
    precio_ves = producto.precio_ves if es_ve else None
    precio_cop = producto.precio_cop if es_ve else producto.precio_cop

    precio_usd = float(producto.precio_base_usd or 0)
    if es_ve:
        if precio_ves is None or precio_cop is None:
            auto_ves, auto_cop = _auto_precios(
                db, empresa_actual.id, precio_usd, producto.tipo_tasa_usd or "bcv"
            )
            if precio_ves is None:
                precio_ves = auto_ves
            if precio_cop is None:
                precio_cop = auto_cop
    elif precio_usd <= 0 and precio_cop:
        tasa = obtener_ultima_tasa(db, empresa_actual.id)
        if tasa:
            precio_usd = float(convertir_cop_a_usd(Decimal(str(precio_cop)), tasa))
        else:
            precio_usd = float(precio_cop)
    elif precio_usd <= 0:
        raise HTTPException(status_code=400, detail="Indica el precio de venta del producto")

    if producto.proveedor_id:
        prov = db.query(Proveedor).filter(
            Proveedor.id == producto.proveedor_id, Proveedor.empresa_id == empresa_actual.id
        ).first()
        if not prov:
            raise HTTPException(status_code=400, detail="Proveedor no encontrado")

    prov_txt, cond_pago, fecha_limite = _resolver_proveedor_pago(
        proveedor=producto.proveedor,
        condicion_pago=producto.condicion_pago,
        fecha_limite_pago=producto.fecha_limite_pago,
    )
    if cond_pago in ("credito", "plazo") and fecha_limite is None:
        raise HTTPException(
            status_code=422,
            detail="Indica la fecha límite de pago para crédito o plazo.",
        )

    nuevo_producto = Producto(
        nombre=producto.nombre,
        sku=producto.sku,
        categoria=producto.categoria,
        precio_usd=precio_usd,
        precio_ves=precio_ves,
        precio_cop=precio_cop,
        costo_usd=producto.costo_usd,
        stock=int(producto.stock_actual),
        stock_minimo=producto.stock_minimo,
        proveedor_id=producto.proveedor_id,
        proveedor=prov_txt,
        condicion_pago=cond_pago,
        fecha_limite_pago=fecha_limite,
        empresa_id=empresa_actual.id,
        activo=True,
    )

    db.add(nuevo_producto)
    db.flush()
    _aplicar_precios_tier(db, nuevo_producto, producto)

    db.commit()
    db.refresh(nuevo_producto)
    from app.services.ai_product_context import invalidar_cache_inventario

    invalidar_cache_inventario(empresa_actual.id)
    return _to_response(db, nuevo_producto)


@router.get("/", response_model=List[ProductoResponse])
def listar_productos(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    empresa = obtener_empresa_tenant(db, usuario)
    productos = (
        db.query(Producto)
        .filter(Producto.empresa_id == empresa.id, Producto.activo.is_(True))
        .order_by(Producto.nombre.asc())
        .all()
    )
    return [_to_response(db, p) for p in productos]


@router.get("/{producto_id}", response_model=ProductoResponse)
def obtener_producto(
    producto_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    empresa = obtener_empresa_tenant(db, usuario)
    producto = (
        db.query(Producto)
        .filter(Producto.id == producto_id, Producto.empresa_id == empresa.id)
        .first()
    )
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return _to_response(db, producto)


@router.put("/{producto_id}", response_model=ProductoResponse)
def actualizar_producto(
    producto_id: UUID,
    body: ProductoUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    empresa = obtener_empresa_tenant(db, usuario)
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
    if body.costo_usd is not None:
        producto.costo_usd = body.costo_usd
    if body.stock_minimo is not None:
        producto.stock_minimo = body.stock_minimo
    if body.activo is not None:
        producto.activo = body.activo
    if body.proveedor_id is not None:
        producto.proveedor_id = body.proveedor_id
    if body.proveedor is not None:
        producto.proveedor = body.proveedor.strip() or None
    if body.condicion_pago is not None or body.fecha_limite_pago is not None:
        prov_txt, cond_pago, fecha_limite = _resolver_proveedor_pago(
            proveedor=body.proveedor if body.proveedor is not None else producto.proveedor,
            condicion_pago=body.condicion_pago or producto.condicion_pago,
            fecha_limite_pago=(
                body.fecha_limite_pago
                if body.fecha_limite_pago is not None
                else producto.fecha_limite_pago
            ),
        )
        if cond_pago in ("credito", "plazo") and fecha_limite is None:
            raise HTTPException(
                status_code=422,
                detail="Indica la fecha límite de pago para crédito o plazo.",
            )
        producto.condicion_pago = cond_pago
        producto.fecha_limite_pago = fecha_limite

    es_ve = _empresa_es_venezuela(db, empresa)
    if body.precio_ves is not None:
        producto.precio_ves = body.precio_ves if es_ve else None
    if body.precio_cop is not None:
        producto.precio_cop = body.precio_cop
    if es_ve and (body.precio_base_usd is not None or body.precio_ves is None):
        tipo_tasa = body.tipo_tasa_usd or "bcv"
        auto_ves, auto_cop = _auto_precios(db, empresa.id, float(producto.precio_usd), tipo_tasa)
        if body.precio_ves is None and auto_ves is not None:
            producto.precio_ves = auto_ves
        if body.precio_cop is None and auto_cop is not None:
            producto.precio_cop = auto_cop
    elif not es_ve:
        producto.precio_ves = None

    _aplicar_precios_tier(db, producto, body)

    db.commit()
    db.refresh(producto)
    return _to_response(db, producto)
