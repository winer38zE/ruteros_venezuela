from uuid import UUID
from typing import Optional
from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.core import Usuario, RolUsuario


def obtener_usuario_actual(
    x_usuario_id: str = Header(..., alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
) -> Usuario:
    try:
        usuario_id = UUID(x_usuario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Usuario-Id inválido")

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o inactivo")
    return usuario


def require_dueno(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.DUENO:
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido al rol DUEÑO",
        )
    return usuario


def obtener_usuario_opcional(
    x_usuario_id: Optional[str] = Header(None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    if not x_usuario_id:
        return None
    try:
        usuario_id = UUID(x_usuario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Usuario-Id inválido")
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o inactivo")
    return usuario


def require_vendedor_o_dueno(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    if usuario.rol not in (RolUsuario.VENDEDOR, RolUsuario.DUENO):
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a VENDEDOR o DUEÑO",
        )
    return usuario


def require_cobrador_o_dueno(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    if usuario.rol not in (RolUsuario.COBRADOR, RolUsuario.DUENO):
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a COBRADOR o DUEÑO",
        )
    return usuario
