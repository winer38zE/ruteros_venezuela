"""Utilidades de deps.py"""
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.pb_orm.ids import resolver_id_registro
from app.models.core import Usuario, RolUsuario


def _id_desde_header(x_usuario_id: str) -> str:
    try:
        return resolver_id_registro(x_usuario_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="X-Usuario-Id inválido")


def obtener_usuario_actual(
    x_usuario_id: str = Header(..., alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
) -> Usuario:
    usuario_id = _id_desde_header(x_usuario_id)
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o inactivo")
    return usuario


def require_dueno(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol != RolUsuario.DUENO:
        raise HTTPException(status_code=403, detail="Acceso restringido al rol DUEÑO")
    return usuario


def rol_confirma_pago(usuario: Optional[Usuario]) -> bool:
    """Dueño y administrador dan por confirmada una transferencia al registrarla."""
    if usuario is None:
        return False
    return usuario.rol in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR)


def require_admin_o_dueno(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    if usuario.rol not in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a DUEÑO o ADMINISTRADOR",
        )
    return usuario


def require_operaciones(usuario: Usuario = Depends(obtener_usuario_actual)) -> Usuario:
    """Dueño y Administrador: inventario, ventas, cobros, proveedores."""
    if usuario.rol not in (RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a operaciones (DUEÑO o ADMINISTRADOR)",
        )
    return usuario


def obtener_usuario_opcional(
    x_usuario_id: Optional[str] = Header(None, alias="X-Usuario-Id"),
    db: Session = Depends(get_db),
) -> Optional[Usuario]:
    if not x_usuario_id:
        return None
    usuario_id = _id_desde_header(x_usuario_id)
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=400, detail="Usuario no encontrado o inactivo")
    return usuario


def require_vendedor_o_superior(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    if usuario.rol not in (RolUsuario.VENDEDOR, RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a VENDEDOR, ADMINISTRADOR o DUEÑO",
        )
    return usuario


def require_cobrador_o_superior(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    if usuario.rol not in (RolUsuario.COBRADOR, RolUsuario.DUENO, RolUsuario.ADMINISTRADOR):
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a COBRADOR, ADMINISTRADOR o DUEÑO",
        )
    return usuario


def require_ruta_o_superior(
    usuario: Usuario = Depends(obtener_usuario_actual),
) -> Usuario:
    """Vendedores y cobradores en calle consultan rutas diarias."""
    if usuario.rol not in (
        RolUsuario.VENDEDOR,
        RolUsuario.COBRADOR,
        RolUsuario.DUENO,
        RolUsuario.ADMINISTRADOR,
    ):
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a VENDEDOR, COBRADOR, ADMINISTRADOR o DUEÑO",
        )
    return usuario


# Alias retrocompatibles
require_vendedor_o_dueno = require_vendedor_o_superior
require_cobrador_o_dueno = require_cobrador_o_superior
