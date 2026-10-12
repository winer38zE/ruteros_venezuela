"""Reestructuración de deuda y plazos de gracia de la carpeta crítica."""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import require_admin_o_dueno, require_cobrador_o_superior
from app.models.core import Usuario
from app.schemas.core import AcuerdoPagoCreate, AcuerdoPagoResponse
from app.services import acuerdos_pago as servicio

router = APIRouter()


@router.get("/acuerdo-pago", response_model=list[AcuerdoPagoResponse])
def consultar_acuerdos(
    cliente_id: UUID = Query(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_cobrador_o_superior),
):
    """Historial de acuerdos del cliente, del más reciente al más antiguo."""
    from app.services.cartera_critica import cliente_de_empresa

    if not cliente_de_empresa(db, usuario.empresa_id, cliente_id):
        raise HTTPException(status_code=404, detail="El cliente no pertenece a la empresa")
    return servicio.listar_acuerdos_cliente(db, usuario.empresa_id, cliente_id)


@router.post("/acuerdo-pago", response_model=AcuerdoPagoResponse)
def otorgar_acuerdo(
    cuerpo: AcuerdoPagoCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    """Registra el plazo de gracia y suspende la alerta estricta hasta la fecha límite.

    No modifica cuotas, ventas ni el buró. Deja una nota de seguimiento
    con estado Acuerdo de pago para que el historial humano no se pierda.
    """
    try:
        return servicio.crear_acuerdo(
            db,
            empresa_id=usuario.empresa_id,
            cliente_id=cuerpo.cliente_id,
            usuario_id=usuario.id,
            usuario_nombre=usuario.nombre,
            monto_acordado_usd=cuerpo.monto_acordado_usd,
            fecha_limite=cuerpo.fecha_limite,
            cuotas_pactadas=cuerpo.cuotas_pactadas,
            nota_consideracion=cuerpo.nota_consideracion,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
