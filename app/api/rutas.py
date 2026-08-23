from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_ruta_o_superior
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Usuario, RolUsuario
from app.schemas.core import RutaClienteResponse, RutasDiaResponse
from app.services.rutas import (
    dia_actual,
    normalizar_dia,
    obtener_ruta_dia,
    serializar_cliente_ruta,
)

router = APIRouter()


def _resolver_vendedor_id(
    vendedor_id: Optional[UUID],
    usuario: Usuario,
) -> UUID:
    if vendedor_id is not None:
        return vendedor_id
    if usuario.rol in (RolUsuario.VENDEDOR, RolUsuario.COBRADOR):
        return usuario.id
    raise HTTPException(
        status_code=400,
        detail="Debe indicar vendedor_id o iniciar sesión como vendedor/cobrador",
    )


@router.get("/dia", response_model=RutasDiaResponse)
def listar_ruta_del_dia(
    vendedor_id: Optional[UUID] = Query(None, description="ID del vendedor/cobrador"),
    dia: Optional[str] = Query(None, description="Día de visita: LUNES, MARTES, ..."),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_ruta_o_superior),
):
    empresa = obtener_empresa_tenant(db)
    vid = _resolver_vendedor_id(vendedor_id, usuario)

    try:
        dia_obj = normalizar_dia(dia) if dia else dia_actual()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    clientes = obtener_ruta_dia(db, vid, dia_obj, empresa.id)
    items = [RutaClienteResponse(**serializar_cliente_ruta(c)) for c in clientes]

    return RutasDiaResponse(
        vendedor_id=vid,
        dia=dia_obj.value,
        total_clientes=len(items),
        clientes=items,
    )
