from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.db import get_db
from app.core.deps import require_dueno
from app.models.core import Usuario, RolUsuario
from app.schemas.core import UsuarioCreate, UsuarioResponse, UsuarioUpdate
from app.api.auth import get_password_hash

router = APIRouter()


@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    return (
        db.query(Usuario)
        .filter(Usuario.empresa_id == dueno.empresa_id)
        .order_by(Usuario.nombre.asc())
        .all()
    )


@router.post("/", response_model=UsuarioResponse)
def crear_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    existente = (
        db.query(Usuario)
        .filter(Usuario.username == usuario.username)
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    try:
        rol = RolUsuario(usuario.rol)
    except ValueError:
        raise HTTPException(status_code=400, detail="Rol inválido")

    nuevo = Usuario(
        nombre=usuario.nombre,
        username=usuario.username,
        password_hash=get_password_hash(usuario.password),
        rol=rol,
        empresa_id=dueno.empresa_id,
        activo=True,
    )
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)
    return nuevo


@router.patch("/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: UUID,
    body: UsuarioUpdate,
    db: Session = Depends(get_db),
    dueno: Usuario = Depends(require_dueno),
):
    user = (
        db.query(Usuario)
        .filter(Usuario.id == usuario_id, Usuario.empresa_id == dueno.empresa_id)
        .first()
    )
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == dueno.id and body.activo is False:
        raise HTTPException(status_code=400, detail="No puedes desactivar tu propio usuario")

    if body.nombre is not None:
        user.nombre = body.nombre
    if body.telefono is not None:
        user.telefono = body.telefono
    if body.activo is not None:
        user.activo = body.activo
    if body.password:
        user.password_hash = get_password_hash(body.password)

    db.commit()
    db.refresh(user)
    return user
