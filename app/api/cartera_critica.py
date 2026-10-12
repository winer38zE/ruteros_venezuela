"""Carpeta de clientes en mora crítica y su historial de seguimiento.

Lectura y alta de notas quedan en cobrador, administrador y dueño.
El panel de cobranza general no se modifica: esta consulta es aparte
y solo devuelve atrasos estrictamente mayores a 21 días.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_cobrador_o_superior
from app.models.core import Usuario
from app.schemas.core import (
    CarteraCriticaListResponse,
    CatalogoCarteraCriticaResponse,
    NotaSeguimientoCreate,
    NotaSeguimientoResponse,
)
from app.services import cartera_critica as servicio

router = APIRouter()


@router.get("/catalogo", response_model=CatalogoCarteraCriticaResponse)
def catalogo_cartera(
    _: Usuario = Depends(require_cobrador_o_superior),
):
    """Motivos de no pago y estados de consideración que acepta el historial."""
    return servicio.catalogo()


@router.get("/", response_model=CarteraCriticaListResponse)
def listar_cartera_critica(
    motivo_mora: Optional[str] = Query(
        default=None,
        description="Opcional: todos, desempleo, alquiler o moroso_real",
    ),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    """Clientes con más de 21 días. El filtro no altera los conteos de los demás motivos."""
    try:
        return servicio.listar_clientes_criticos(
            db,
            usuario.empresa_id,
            motivo_mora=motivo_mora,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{cliente_id}/notas", response_model=list[NotaSeguimientoResponse])
def consultar_notas(
    cliente_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    """Historial de cobranza del cliente, de la nota más reciente a la más antigua."""
    cliente = servicio.cliente_de_empresa(db, usuario.empresa_id, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="El cliente no pertenece a la empresa")
    return servicio.listar_notas(db, usuario.empresa_id, cliente_id)


@router.post("/{cliente_id}/notas", response_model=NotaSeguimientoResponse)
def guardar_nota(
    cliente_id: UUID,
    cuerpo: NotaSeguimientoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    """Agrega una nota. No pisa las anteriores: la última queda como estado vigente."""
    cliente = servicio.cliente_de_empresa(db, usuario.empresa_id, cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="El cliente no pertenece a la empresa")
    try:
        return servicio.crear_nota(
            db,
            empresa_id=usuario.empresa_id,
            cliente_id=cliente_id,
            usuario_id=usuario.id,
            usuario_nombre=usuario.nombre,
            motivo=cuerpo.motivo,
            estado_consideracion=cuerpo.estado_consideracion,
            observacion=cuerpo.observacion,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
