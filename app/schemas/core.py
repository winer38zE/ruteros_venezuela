from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

# --- EMPRESAS ---
class EmpresaCreate(BaseModel):
    nombre: str

class EmpresaResponse(BaseModel):
    id: UUID
    nombre: str
    activa: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)

# --- USUARIOS ---
class UsuarioCreate(BaseModel):
    nombre: str
    username: str
    password: str
    rol: str = Field(pattern="^(DUEÑO|VENDEDOR|COBRADOR)$")

class UsuarioResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    username: str
    rol: str
    activo: bool

    model_config = ConfigDict(from_attributes=True)

# --- CLIENTES ---
class ClienteCreate(BaseModel):
    # Esto es lo que entra desde el navegador/app
    id: Optional[str] = None 
    nombre_completo: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None

class ClienteResponse(BaseModel):
    # Esto es lo que sale de la base de datos (Debe coincidir exacto con app/models/core.py)
    id: UUID
    empresa_id: UUID  # Corregido: Ahora espera un UUID real, no un string
    nombre: str       # Corregido: La BD usa 'nombre', no 'nombre_completo'
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    # Eliminamos 'ultima_actualizacion' y 'saldo_deuda' temporalmente hasta agregarlos a la BD

    model_config = ConfigDict(from_attributes=True)

# --- PRODUCTOS ---
class ProductoCreate(BaseModel):
    id: Optional[str] = None 
    nombre: str
    precio_base_usd: float
    stock_actual: float = 0.0

class ProductoResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    # CORRECCIÓN: Usamos los nombres exactos de tu base de datos
    precio_usd: float  
    stock: int
    
    model_config = ConfigDict(from_attributes=True)

# --- VENTAS ---
class VentaCreate(BaseModel):
    total_usd: float
    tasa_usd_aplicada: float
    tasa_eur_aplicada: float
    frecuencia_pago: str  # Ej: "semanal", "quincenal"

class VentaResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID
    vendedor_id: UUID
    total_usd: float
    estado: str

    model_config = ConfigDict(from_attributes=True)

# --- TASAS DE CAMBIO ---
class TasaCambioCreate(BaseModel):
    momento: str = Field(pattern="^(manana|tarde)$")
    usd_bs: float
    eur_bs: float

class TasaCambioResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    fecha: datetime
    momento: str
    usd_bs: float
    eur_bs: float

    model_config = ConfigDict(from_attributes=True)

# --- COBROS ---
class CobroCreate(BaseModel):
    id: Optional[str] = None
    venta_id: UUID
    cobrador_id: Optional[UUID] = None
    fecha: Optional[datetime] = None
    monto_usd: float
    moneda_pago: str = Field(
        pattern="^(bolivar|dolar|euro|pago_movil|transferencia)$"
    )
    tasa_usd_aplicada: float
    tasa_eur_aplicada: float

class CobroResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    venta_id: UUID
    cobrador_id: UUID
    fecha: datetime
    monto_usd: float
    moneda_pago: str
    tasa_usd_aplicada: float
    tasa_eur_aplicada: float
    sincronizado: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)