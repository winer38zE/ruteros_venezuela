from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Cliente, TipoCliente
from app.schemas.core import ClienteCreate, ClienteResponse
from typing import List

router = APIRouter()


@router.post("/", response_model=ClienteResponse)
def crear_cliente(cliente: ClienteCreate, db: Session = Depends(get_db)):
    empresa_actual = obtener_empresa_tenant(db)

    nuevo_cliente = Cliente(
        nombre=cliente.nombre_completo,
        direccion=cliente.direccion,
        telefono=cliente.telefono,
        tipo_cliente=TipoCliente(cliente.tipo_cliente or "detal"),
        empresa_id=empresa_actual.id,
    )

    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)

    return nuevo_cliente


@router.get("/", response_model=List[ClienteResponse])
def listar_clientes(db: Session = Depends(get_db)):
    empresa = obtener_empresa_tenant(db)
    return db.query(Cliente).filter(Cliente.empresa_id == empresa.id).all()
