from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.core import Usuario, Empresa
from app.schemas.core import UsuarioCreate, UsuarioResponse
from typing import List

router = APIRouter()

@router.post("/", response_model=UsuarioResponse)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    empresa_actual = db.query(Empresa).first()
    if not empresa_actual:
        raise HTTPException(status_code=400, detail="Debes crear una empresa primero")

    usuario_existente = db.query(Usuario).filter(Usuario.username == usuario.username).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está en uso")

    nuevo_usuario = Usuario(
        nombre=usuario.nombre,
        username=usuario.username,
        password_hash=usuario.password,  # <-- CORREGIDO: Empatamos con tu modelo de BD
        rol=usuario.rol,
        empresa_id=empresa_actual.id
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario

@router.get("/", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(get_db)):
    return db.query(Usuario).all()