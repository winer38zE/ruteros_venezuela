from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db
from app.models.core import Empresa
from app.schemas.core import EmpresaCreate, EmpresaResponse

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