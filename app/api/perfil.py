from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.deps import obtener_usuario_actual, require_vendedor_o_cobrador
from app.models.core import Usuario
from app.schemas.core import (
    CuentaBancariaEmpleadoResponse,
    CuentaBancariaEmpleadoUpsert,
)
from app.services.cuenta_bancaria_empleado import (
    obtener_cuenta_empleado,
    upsert_cuenta_empleado,
)

router = APIRouter()


def _serializar_cuenta(cuenta) -> dict:
    return {
        "id": cuenta.id,
        "empresa_id": cuenta.empresa_id,
        "usuario_id": cuenta.usuario_id,
        "banco": cuenta.banco,
        "tipo_cuenta": cuenta.tipo_cuenta,
        "numero_cuenta": cuenta.numero_cuenta,
        "titular": cuenta.titular,
        "documento_identidad": cuenta.documento_identidad,
        "canal": cuenta.canal,
        "telefono_pago_movil": cuenta.telefono_pago_movil,
        "activa": cuenta.activa,
        "verificada_por_dueno": cuenta.verificada_por_dueno,
        "fecha_actualizacion": cuenta.fecha_actualizacion,
        "configurado": True,
    }


@router.get("/cuenta-bancaria", response_model=CuentaBancariaEmpleadoResponse)
def ver_mi_cuenta_bancaria(
    db: Session = Depends(get_db),
    empleado: Usuario = Depends(require_vendedor_o_cobrador),
):
    cuenta = obtener_cuenta_empleado(db, empleado.id)
    if not cuenta:
        raise HTTPException(status_code=404, detail="Aún no has registrado tu cuenta bancaria")
    return _serializar_cuenta(cuenta)


@router.put("/cuenta-bancaria", response_model=CuentaBancariaEmpleadoResponse)
def guardar_mi_cuenta_bancaria(
    body: CuentaBancariaEmpleadoUpsert,
    db: Session = Depends(get_db),
    empleado: Usuario = Depends(require_vendedor_o_cobrador),
):
    try:
        cuenta = upsert_cuenta_empleado(db, empleado, body.model_dump())
        db.commit()
        db.refresh(cuenta)
        return _serializar_cuenta(cuenta)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
