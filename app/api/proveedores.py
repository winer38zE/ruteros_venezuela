from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import require_dueno
from app.models.core import Proveedor, Usuario
from app.schemas.core import ProveedorCreate, ProveedorResponse

router = APIRouter()


@router.get("/", response_model=List[ProveedorResponse])
def listar_proveedores(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    return (
        db.query(Proveedor)
        .filter(Proveedor.empresa_id == dueno.empresa_id, Proveedor.activo.is_(True))
        .order_by(Proveedor.nombre.asc())
        .all()
    )


@router.post("/", response_model=ProveedorResponse)
def crear_proveedor(
    body: ProveedorCreate,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    prov = Proveedor(
        empresa_id=dueno.empresa_id,
        nombre=body.nombre,
        telefono=body.telefono,
        rif=body.rif,
        notas=body.notas,
    )
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return prov
