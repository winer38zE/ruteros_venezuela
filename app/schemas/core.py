from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
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
    id: Optional[str] = None
    nombre_completo: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    tipo_cliente: Optional[str] = Field(default="detal", pattern="^(mayorista|detal)$")

class ClienteResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    tipo_cliente: str = "detal"

    model_config = ConfigDict(from_attributes=True)

# --- PRODUCTOS ---
class ProductoCreate(BaseModel):
    id: Optional[str] = None
    nombre: str
    precio_base_usd: float
    stock_actual: float = 0.0
    precio_mayorista_usd: Optional[float] = None
    precio_detal_usd: Optional[float] = None

class ProductoResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    # CORRECCIÓN: Usamos los nombres exactos de tu base de datos
    precio_usd: float  
    stock: int
    
    model_config = ConfigDict(from_attributes=True)

# --- VENTAS ---
class DetalleVentaCreate(BaseModel):
    producto_id: UUID
    cantidad: int = Field(gt=0)
    tipo_precio: Optional[str] = Field(default="detal", pattern="^(mayorista|detal)$")

class DetalleVentaResponse(BaseModel):
    id: UUID
    producto_id: UUID
    cantidad: int
    precio_unitario_usd: float

    model_config = ConfigDict(from_attributes=True)

class VentaCreate(BaseModel):
    total_usd: float
    tasa_usd_aplicada: float
    tasa_eur_aplicada: float
    frecuencia_pago: str  # Ej: "semanal", "quincenal"
    cliente_id: Optional[UUID] = None
    id: Optional[str] = None
    detalles: Optional[List[DetalleVentaCreate]] = None
    almacen_id: Optional[UUID] = None

class VentaResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID
    vendedor_id: UUID
    total_usd: float
    estado: str
    detalles: List[DetalleVentaResponse] = []

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

class VentaPendienteResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    cliente_nombre: str
    total_usd: float
    cobrado_usd: float
    saldo_pendiente_usd: float
    estado: str

    model_config = ConfigDict(from_attributes=True)

# --- CONFIGURACIÓN FISCAL ---
class ConfiguracionFiscalCreate(BaseModel):
    pais: str = "VE"
    moneda_base: str = "USD"
    iva_porcentaje: float = 16.0
    igtf_porcentaje: float = 3.0
    aplica_igtf_divisas: bool = True
    razon_social: Optional[str] = None
    rif: Optional[str] = None

class ConfiguracionFiscalUpdate(BaseModel):
    pais: Optional[str] = None
    moneda_base: Optional[str] = None
    iva_porcentaje: Optional[float] = None
    igtf_porcentaje: Optional[float] = None
    aplica_igtf_divisas: Optional[bool] = None
    razon_social: Optional[str] = None
    rif: Optional[str] = None

class ConfiguracionFiscalResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    pais: str
    moneda_base: str
    iva_porcentaje: float
    igtf_porcentaje: float
    aplica_igtf_divisas: bool
    razon_social: Optional[str] = None
    rif: Optional[str] = None
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True)

class PresetFiscalResponse(BaseModel):
    codigo: str
    nombre: str
    moneda_base: str
    iva_porcentaje: float
    igtf_porcentaje: float
    aplica_igtf_divisas: bool
    notas: str

class ResumenContableResponse(BaseModel):
    empresa_id: str
    pais: str
    total_ventas_usd: float
    total_cobrado_usd: float
    cuentas_por_cobrar_usd: float
    iva_estimado_usd: float
    asientos_generados: int

class ExportacionExcelInfo(BaseModel):
    empresa: str
    pais: str
    rif: Optional[str] = None
    razon_social: Optional[str] = None
    total_ventas: int
    total_cobros: int
    total_asientos: int
    productos_inventario: int
    valor_inventario_usd: float
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    hojas: List[str]
    formato: str

# --- INVENTARIO ---
class AlmacenCreate(BaseModel):
    nombre: str
    ubicacion: Optional[str] = None
    es_principal: bool = False

class AlmacenResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    ubicacion: Optional[str] = None
    es_principal: bool
    activo: bool

    model_config = ConfigDict(from_attributes=True)

class LoteInventarioCreate(BaseModel):
    producto_id: UUID
    almacen_id: UUID
    numero_lote: str
    cantidad: int = Field(ge=0)
    costo_unitario_usd: float = 0.0
    fecha_vencimiento: Optional[datetime] = None

class LoteInventarioResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    producto_id: UUID
    almacen_id: UUID
    numero_lote: str
    cantidad: int
    costo_unitario_usd: float
    fecha_vencimiento: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PrecioProductoCreate(BaseModel):
    tipo_cliente: str = Field(pattern="^(mayorista|detal)$")
    precio_usd: float

class PrecioProductoResponse(BaseModel):
    id: UUID
    producto_id: UUID
    tipo_cliente: str
    precio_usd: float

    model_config = ConfigDict(from_attributes=True)

# --- INVENTARIO FASE 2 ---
class StockAlmacenResponse(BaseModel):
    almacen_id: UUID
    almacen_nombre: str
    stock_lotes: int
    stock_general_asignado: int
    stock_total: int

class StockProductoResponse(BaseModel):
    producto_id: UUID
    producto_nombre: str
    stock_general: int
    stock_total_global: int
    por_almacen: List[StockAlmacenResponse]

class InventarioValoradoItem(BaseModel):
    producto_id: UUID
    producto_nombre: str
    stock_general: int
    stock_lotes: int
    stock_total: int
    costo_promedio_usd: float
    valor_total_usd: float

class MovimientoInventarioResponse(BaseModel):
    id: UUID
    producto_id: UUID
    almacen_id: UUID
    lote_id: Optional[UUID] = None
    tipo: str
    cantidad: int
    referencia_tipo: Optional[str] = None
    referencia_id: Optional[UUID] = None
    fecha: datetime

    model_config = ConfigDict(from_attributes=True)

# --- CONTABILIDAD ---
class LineaAsientoResponse(BaseModel):
    id: UUID
    cuenta_codigo: str
    cuenta_nombre: str
    debito_usd: float
    credito_usd: float
    debito_bs: float
    credito_bs: float

    model_config = ConfigDict(from_attributes=True)

class AsientoContableResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    fecha: datetime
    referencia_tipo: str
    referencia_id: UUID
    descripcion: str
    tasa_usd_aplicada: float
    lineas: List[LineaAsientoResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- FINANZAS / NÓMINA ---
class ConfiguracionNominaUpdate(BaseModel):
    comision_vendedor_por_articulo_usd: Optional[float] = None
    comision_cobrador_porcentaje: Optional[float] = None
    sueldo_base_cobrador_usd: Optional[float] = None

class ConfiguracionNominaResponse(BaseModel):
    empresa_id: UUID
    comision_vendedor_por_articulo_usd: float
    comision_cobrador_porcentaje: float
    sueldo_base_cobrador_usd: float

    model_config = ConfigDict(from_attributes=True)

class MovimientoFinancieroCreate(BaseModel):
    tipo: str = Field(pattern="^(entrada|salida)$")
    categoria: str = Field(
        pattern="^(ingreso_operativo|pago_vendedor|pago_cobrador|pago_proveedor|gasto_moto|operacion_general)$"
    )
    monto_usd: float = Field(gt=0)
    descripcion: str
    fecha: Optional[datetime] = None
    empleado_id: Optional[UUID] = None

class MovimientoFinancieroResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    tipo: str
    categoria: str
    monto_usd: float
    descripcion: str
    fecha: datetime
    registrado_por_id: UUID
    empleado_id: Optional[UUID] = None
    aprobado: bool
    fecha_creacion: datetime

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

class ResumenFinancieroResponse(BaseModel):
    total_entradas_usd: float
    total_salidas_usd: float
    gastos_moto_usd: float
    nomina_pendiente_usd: float
    balance_neto_usd: float
    total_cobros_operativos_usd: float

class DetalleNominaEmpleado(BaseModel):
    empleado_id: UUID
    empleado_nombre: str
    rol: str
    articulos_vendidos: int = 0
    comision_ventas_usd: float = 0.0
    total_cobrado_usd: float = 0.0
    comision_cobros_usd: float = 0.0
    sueldo_base_usd: float = 0.0
    total_calculado_usd: float
    total_pagado_usd: float
    pendiente_usd: float

class NominaCalculadaResponse(BaseModel):
    periodo_desde: Optional[str] = None
    periodo_hasta: Optional[str] = None
    comision_vendedor_por_articulo_usd: float
    comision_cobrador_porcentaje: float
    empleados: List[DetalleNominaEmpleado]
    total_pendiente_usd: float

class AprobarPagoNominaRequest(BaseModel):
    empleado_id: UUID
    monto_usd: float = Field(gt=0)
    periodo_desde: Optional[datetime] = None
    periodo_hasta: Optional[datetime] = None
    descripcion: Optional[str] = None