from datetime import datetime

from sqlalchemy.orm import Session

from app.models.core import CuentaBancariaEmpleado, Usuario


def obtener_cuenta_empleado(db: Session, usuario_id) -> CuentaBancariaEmpleado | None:
    return (
        db.query(CuentaBancariaEmpleado)
        .filter(
            CuentaBancariaEmpleado.usuario_id == usuario_id,
            CuentaBancariaEmpleado.activa.is_(True),
        )
        .first()
    )


def upsert_cuenta_empleado(
    db: Session,
    usuario: Usuario,
    data: dict,
) -> CuentaBancariaEmpleado:
    canal = data.get("canal", "transferencia")
    if canal == "transferencia" and not data.get("numero_cuenta"):
        raise ValueError("numero_cuenta es obligatorio para transferencia")
    if canal == "pago_movil" and not data.get("telefono_pago_movil"):
        raise ValueError("telefono_pago_movil es obligatorio para pago móvil")

    cuenta = obtener_cuenta_empleado(db, usuario.id)
    if cuenta is None:
        cuenta = CuentaBancariaEmpleado(
            empresa_id=usuario.empresa_id,
            usuario_id=usuario.id,
        )
        db.add(cuenta)

    cuenta.banco = data["banco"]
    cuenta.tipo_cuenta = data["tipo_cuenta"]
    cuenta.numero_cuenta = data.get("numero_cuenta")
    cuenta.titular = data["titular"]
    cuenta.documento_identidad = data["documento_identidad"]
    cuenta.canal = canal
    cuenta.telefono_pago_movil = data.get("telefono_pago_movil")
    cuenta.activa = True
    cuenta.verificada_por_dueno = False
    cuenta.fecha_actualizacion = datetime.utcnow()
    db.flush()
    return cuenta
