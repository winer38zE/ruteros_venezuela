from decimal import Decimal
from typing import List, Optional
from uuid import UUID
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.db import get_db
from app.core.deps import (
    require_operaciones,
    require_dueno,
    require_vendedor_o_superior,
    obtener_usuario_opcional,
)
from app.models.core import (
    Proveedor,
    Usuario,
    RolUsuario,
    MovimientoFinanciero,
    TipoMovimientoFinanciero,
    CategoriaMovimientoFinanciero,
    MonedaGasto,
)
from app.schemas.core import (
    ProveedorCreate,
    ProveedorUpdate,
    ProveedorResponse,
    PagoProveedorRequest,
)

router = APIRouter()


def _to_response(prov: Proveedor) -> ProveedorResponse:
    return ProveedorResponse(
        id=prov.id,
        empresa_id=prov.empresa_id,
        nombre=prov.nombre,
        telefono=prov.telefono,
        rif=prov.rif,
        notas=prov.notas,
        saldo_deuda_usd=float(prov.saldo_deuda_usd or 0),
        activo=prov.activo,
    )


@router.get("/", response_model=List[ProveedorResponse])
def listar_proveedores(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    rows = (
        db.query(Proveedor)
        .filter(Proveedor.empresa_id == usuario.empresa_id, Proveedor.activo.is_(True))
        .order_by(Proveedor.nombre.asc())
        .all()
    )
    return [_to_response(p) for p in rows]


@router.post("/", response_model=ProveedorResponse)
def crear_proveedor(
    body: ProveedorCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    notas = body.notas
    if body.contacto:
        notas = f"Contacto: {body.contacto}" + (f"\n{notas}" if notas else "")
    prov = Proveedor(
        empresa_id=usuario.empresa_id,
        nombre=body.nombre,
        telefono=body.telefono,
        rif=body.rif,
        notas=notas,
    )
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return _to_response(prov)


@router.put("/{proveedor_id}", response_model=ProveedorResponse)
def actualizar_proveedor(
    proveedor_id: UUID,
    body: ProveedorUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    prov = (
        db.query(Proveedor)
        .filter(Proveedor.id == proveedor_id, Proveedor.empresa_id == usuario.empresa_id)
        .first()
    )
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    for field in ("nombre", "telefono", "rif", "notas", "activo"):
        val = getattr(body, field, None)
        if val is not None:
            setattr(prov, field, val)
    db.commit()
    db.refresh(prov)
    return _to_response(prov)


@router.post("/{proveedor_id}/pagar", response_model=ProveedorResponse)
def registrar_pago_proveedor(
    proveedor_id: UUID,
    body: PagoProveedorRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_operaciones),
):
    prov = (
        db.query(Proveedor)
        .filter(Proveedor.id == proveedor_id, Proveedor.empresa_id == usuario.empresa_id)
        .first()
    )
    if not prov:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    monto = Decimal(str(body.monto_usd))
    saldo = Decimal(str(prov.saldo_deuda_usd or 0))
    if monto > saldo + Decimal("0.01"):
        raise HTTPException(status_code=400, detail="El pago excede la deuda pendiente")

    prov.saldo_deuda_usd = saldo - monto
    mov = MovimientoFinanciero(
        empresa_id=usuario.empresa_id,
        tipo=TipoMovimientoFinanciero.SALIDA,
        categoria=CategoriaMovimientoFinanciero.PAGO_PROVEEDOR,
        monto_usd=monto,
        monto_original=monto,
        moneda=MonedaGasto.USD,
        descripcion=body.descripcion or f"Pago a proveedor {prov.nombre}",
        fecha=datetime.utcnow(),
        registrado_por_id=usuario.id,
        proveedor_id=prov.id,
        aprobado=True,
    )
    db.add(mov)
    db.commit()
    db.refresh(prov)
    return _to_response(prov)
