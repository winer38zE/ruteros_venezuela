from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.core.deps import obtener_usuario_actual, require_admin_o_dueno
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Empresa, Usuario
from app.schemas.core import (
    EmpresaCreate,
    EmpresaResponse,
    DatosBancariosResponse,
    DatosBancariosUpdate,
)

# APIRouter nos permite agrupar rutas relacionadas
router = APIRouter()

@router.post("/", response_model=EmpresaResponse)
def crear_empresa(empresa: EmpresaCreate, db: Session = Depends(get_db)):
    # 1. Creamos la instancia basada en el modelo de base de datos
    # No le pasamos el 'id' porque SQLAlchemy generará el UUID automáticamente
    nueva_empresa = Empresa(nombre=empresa.nombre)
    
    # 2. La añadimos a la sesión y guardamos (commit)
    db.add(nueva_empresa)
    db.commit()
    
    # 3. Refrescamos para obtener los datos generados por la BD (como el id y fecha)
    db.refresh(nueva_empresa)
    
    return nueva_empresa


def _datos_bancarios(empresa: Empresa) -> DatosBancariosResponse:
    banco = (empresa.banco or "").strip() or None
    tipo = (empresa.tipo_cuenta or "").strip() or None
    numero = (empresa.numero_cuenta or "").strip() or None
    cedula = (empresa.cedula_nit or "").strip() or None
    return DatosBancariosResponse(
        banco=banco,
        tipo_cuenta=tipo,
        numero_cuenta=numero,
        cedula_nit=cedula,
        configurado=bool(banco or numero),
    )


def _empresa_del_usuario(db: Session, usuario: Usuario) -> Empresa:
    empresa = obtener_empresa_tenant(db)
    if usuario.empresa_id != empresa.id:
        raise HTTPException(status_code=403, detail="La empresa no corresponde al usuario")
    return empresa


@router.get("/datos-bancarios", response_model=DatosBancariosResponse)
def obtener_datos_bancarios(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(obtener_usuario_actual),
):
    return _datos_bancarios(_empresa_del_usuario(db, usuario))


@router.put("/datos-bancarios", response_model=DatosBancariosResponse)
def actualizar_datos_bancarios(
    datos: DatosBancariosUpdate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_o_dueno),
):
    empresa = _empresa_del_usuario(db, usuario)
    empresa.banco = (datos.banco or "").strip() or None
    empresa.tipo_cuenta = (datos.tipo_cuenta or "").strip() or None
    empresa.numero_cuenta = (datos.numero_cuenta or "").strip() or None
    empresa.cedula_nit = (datos.cedula_nit or "").strip() or None
    db.commit()
    db.refresh(empresa)
    return _datos_bancarios(empresa)