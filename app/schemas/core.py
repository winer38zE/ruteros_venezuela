from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, date
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

class DatosBancariosResponse(BaseModel):
    banco: Optional[str] = None
    tipo_cuenta: Optional[str] = None
    numero_cuenta: Optional[str] = None
    cedula_nit: Optional[str] = None
    configurado: bool = False

class DatosBancariosUpdate(BaseModel):
    banco: Optional[str] = Field(default=None, max_length=120)
    tipo_cuenta: Optional[str] = Field(default=None, max_length=40)
    numero_cuenta: Optional[str] = Field(default=None, max_length=64)
    cedula_nit: Optional[str] = Field(default=None, max_length=32)

class CuentaBancariaCreate(BaseModel):
    canal: str = Field(default="transferencia", pattern="^(transferencia|pago_movil)$")
    banco: str = Field(min_length=1, max_length=120)
    tipo_cuenta: Optional[str] = Field(default=None, max_length=40)
    numero_cuenta: Optional[str] = Field(default=None, max_length=64)
    telefono: Optional[str] = Field(default=None, max_length=20)
    titular: str = Field(min_length=1, max_length=160)
    documento: str = Field(min_length=1, max_length=32)

class CuentaBancariaResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    banco: str
    tipo_cuenta: str
    numero_cuenta: str
    titular: str
    documento: str
    canal: str = "transferencia"
    telefono: Optional[str] = None
    activa: bool = True

    model_config = ConfigDict(from_attributes=True)

# --- USUARIOS ---
class UsuarioCreate(BaseModel):
    nombre: str
    username: str
    password: str
    rol: str = Field(pattern="^(DUEÑO|ADMINISTRADOR|VENDEDOR|COBRADOR)$")

class UsuarioResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    username: str
    rol: str
    activo: bool
    telefono: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None
    password: Optional[str] = None

# --- CLIENTES ---
class ClienteCreate(BaseModel):
    id: Optional[str] = None
    nombre_completo: str
    identificacion: str = Field(min_length=5, max_length=32)
    telefono: Optional[str] = None
    telefono_secundario: Optional[str] = None
    direccion: Optional[str] = None
    punto_referencia: Optional[str] = None
    latitud_residencia: Optional[float] = None
    longitud_residencia: Optional[float] = None
    empresa_trabajo: Optional[str] = None
    direccion_laboral: Optional[str] = None
    latitud_trabajo: Optional[float] = None
    longitud_trabajo: Optional[float] = None
    ref_familiar_nombre: Optional[str] = None
    ref_familiar_parentesco: Optional[str] = None
    ref_familiar_telefono: Optional[str] = None
    email: Optional[str] = None
    tipo_cliente: Optional[str] = Field(default="detal", pattern="^(mayorista|detal)$")
    vendedor_id: Optional[UUID] = None
    dia_visita: Optional[str] = Field(
        default=None,
        pattern="^(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO|DOMINGO)$",
    )
    orden_secuencial: Optional[int] = Field(default=None, ge=1)
    dia_ruta: Optional[str] = None
    orden_ruta: Optional[int] = Field(default=None, ge=1)

class ClienteUpdate(BaseModel):
    nombre_completo: Optional[str] = None
    identificacion: Optional[str] = Field(default=None, min_length=5, max_length=32)
    telefono: Optional[str] = None
    telefono_secundario: Optional[str] = None
    direccion: Optional[str] = None
    punto_referencia: Optional[str] = None
    latitud_residencia: Optional[float] = None
    longitud_residencia: Optional[float] = None
    empresa_trabajo: Optional[str] = None
    direccion_laboral: Optional[str] = None
    latitud_trabajo: Optional[float] = None
    longitud_trabajo: Optional[float] = None
    ref_familiar_nombre: Optional[str] = None
    ref_familiar_parentesco: Optional[str] = None
    ref_familiar_telefono: Optional[str] = None
    email: Optional[str] = None
    tipo_cliente: Optional[str] = Field(default=None, pattern="^(mayorista|detal)$")
    vendedor_id: Optional[UUID] = None
    dia_visita: Optional[str] = Field(
        default=None,
        pattern="^(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO|DOMINGO)$",
    )
    orden_secuencial: Optional[int] = Field(default=None, ge=1)
    dia_ruta: Optional[str] = None
    orden_ruta: Optional[int] = Field(default=None, ge=1)
    tipo_visita_ruta: Optional[str] = Field(default=None, pattern="^(frecuente|nuevo)$")

class ClienteResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    identificacion: str
    telefono: Optional[str] = None
    telefono_secundario: Optional[str] = None
    direccion: Optional[str] = None
    punto_referencia: Optional[str] = None
    latitud_residencia: Optional[float] = None
    longitud_residencia: Optional[float] = None
    empresa_trabajo: Optional[str] = None
    direccion_laboral: Optional[str] = None
    latitud_trabajo: Optional[float] = None
    longitud_trabajo: Optional[float] = None
    ref_familiar_nombre: Optional[str] = None
    ref_familiar_parentesco: Optional[str] = None
    ref_familiar_telefono: Optional[str] = None
    email: Optional[str] = None
    score_credito: int = 70
    nivel_riesgo: str = "bueno"
    estado_credito: str = "Bueno"
    clasificacion_credito: str = "Bueno"
    total_compras: int = 0
    monto_compras_usd: float = 0
    total_pagos: int = 0
    monto_pagos_usd: float = 0
    estado_morosidad: str = "al_dia"
    tipo_cliente: str = "detal"
    vendedor_id: Optional[UUID] = None
    dia_visita: Optional[str] = None
    orden_secuencial: Optional[int] = None
    dia_ruta: Optional[str] = None
    orden_ruta: Optional[int] = None
    tipo_visita_ruta: str = "frecuente"

    model_config = ConfigDict(from_attributes=True)


class RutaClienteResponse(BaseModel):
    id: UUID
    vendedor_id: Optional[UUID] = None
    nombre: str
    direccion: Optional[str] = None
    dia_visita: str
    dia_ruta: str
    orden_secuencial: int
    orden_ruta: int
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    tipo_visita_ruta: str
    telefono: Optional[str] = None
    estado_visita: str = "pendiente"
    marcado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class RutasDiaResponse(BaseModel):
    vendedor_id: UUID
    dia: str
    fecha: date
    total_clientes: int
    visitados: int = 0
    pendientes: int = 0
    clientes: List["RutaClienteResponse"] = []


class OrdenRutaItem(BaseModel):
    cliente_id: UUID
    orden_ruta: Optional[int] = Field(default=None, ge=1)
    orden_secuencial: int = Field(ge=1)


class ReordenarRutaRequest(BaseModel):
    vendedor_id: Optional[UUID] = None
    dia: str = Field(pattern="^(LUNES|MARTES|MIERCOLES|JUEVES|VIERNES|SABADO|DOMINGO)$")
    orden: List[OrdenRutaItem] = Field(min_length=1)


class VisitaCreate(BaseModel):
    cliente_id: UUID
    estado: str = Field(default="visitado", pattern="^(pendiente|visitado|no_encontrado)$")
    notas: Optional[str] = None
    latitud_visita: Optional[float] = None
    longitud_visita: Optional[float] = None
    fecha: Optional[date] = None


class VisitaLoteRequest(BaseModel):
    visitas: List[VisitaCreate] = Field(min_length=1)


class VisitaResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    vendedor_id: UUID
    fecha: date
    estado: str
    notas: Optional[str] = None
    latitud_visita: Optional[float] = None
    longitud_visita: Optional[float] = None
    marcado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class ResumenVendedorRuta(BaseModel):
    vendedor_id: UUID
    vendedor_nombre: str
    total_clientes: int
    visitados: int
    pendientes: int
    no_encontrados: int = 0
    porcentaje_avance: float


class RutasResumenResponse(BaseModel):
    fecha: date
    dia: str
    vendedores: List[ResumenVendedorRuta] = []


class WhatsappReporteRequest(BaseModel):
    telefono: Optional[str] = None
    texto: Optional[str] = Field(default=None, max_length=4000)
    dia: Optional[str] = None
    fecha: Optional[date] = None


class WhatsappReporteResponse(BaseModel):
    enviado: bool
    telefono: str
    mensaje: str


class HistorialBuroItem(BaseModel):
    fecha: str
    tipo: str
    mensaje: str

class BuroCreditoResponse(BaseModel):
    identificacion: str
    encontrado: bool
    score_global: Optional[int] = None
    nivel_riesgo: Optional[str] = None
    estado_credito: Optional[str] = None
    historial_cumplimiento: List[HistorialBuroItem] = []

class ClienteAutocompletadoResponse(BaseModel):
    identificacion: str
    nombre_completo: Optional[str] = None
    telefono: Optional[str] = None
    telefono_secundario: Optional[str] = None
    direccion: Optional[str] = None
    punto_referencia: Optional[str] = None
    latitud_residencia: Optional[float] = None
    longitud_residencia: Optional[float] = None
    empresa_trabajo: Optional[str] = None
    direccion_laboral: Optional[str] = None
    latitud_trabajo: Optional[float] = None
    longitud_trabajo: Optional[float] = None
    ref_familiar_nombre: Optional[str] = None
    ref_familiar_parentesco: Optional[str] = None
    ref_familiar_telefono: Optional[str] = None
    email: Optional[str] = None
    score_global: Optional[int] = None
    nivel_riesgo: Optional[str] = None
    estado_credito: Optional[str] = None
    en_red: bool = False

# --- PRODUCTOS ---
class ProductoCreate(BaseModel):
    id: Optional[str] = None
    nombre: str
    sku: Optional[str] = None
    categoria: Optional[str] = None
    precio_base_usd: float
    precio_ves: Optional[float] = None
    precio_cop: Optional[float] = None
    costo_usd: float = 0.0
    stock_actual: float = 0.0
    stock_minimo: int = 0
    precio_mayorista_usd: Optional[float] = None
    precio_detal_usd: Optional[float] = None
    proveedor_id: Optional[UUID] = None
    tipo_tasa_usd: Optional[str] = Field(default="bcv", pattern="^(bcv|paralelo)$")

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    sku: Optional[str] = None
    categoria: Optional[str] = None
    precio_base_usd: Optional[float] = None
    precio_ves: Optional[float] = None
    precio_cop: Optional[float] = None
    costo_usd: Optional[float] = None
    stock_minimo: Optional[int] = None
    activo: Optional[bool] = None
    precio_mayorista_usd: Optional[float] = None
    precio_detal_usd: Optional[float] = None
    proveedor_id: Optional[UUID] = None
    tipo_tasa_usd: Optional[str] = Field(default=None, pattern="^(bcv|paralelo)$")

class ProductoResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    sku: Optional[str] = None
    categoria: Optional[str] = None
    precio_usd: float
    precio_ves: Optional[float] = None
    precio_cop: Optional[float] = None
    costo_usd: float = 0.0
    stock: int
    stock_minimo: int = 0
    activo: bool = True
    proveedor_id: Optional[UUID] = None
    proveedor_nombre: Optional[str] = None
    precio_ves_calculado: Optional[float] = None
    precio_cop_calculado: Optional[float] = None

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
    numero_cuotas: Optional[int] = Field(default=None, ge=1, le=60)
    tipo_tasa_usd: Optional[str] = Field(default="bcv", pattern="^(bcv|paralelo)$")
    es_borrador: bool = False
    latitud_residencia: Optional[float] = None
    longitud_residencia: Optional[float] = None
    latitud_trabajo: Optional[float] = None
    longitud_trabajo: Optional[float] = None
    metodo_pago: Optional[str] = Field(default="efectivo", pattern="^(efectivo|transferencia|pago_movil)$")
    referencia_pago: Optional[str] = Field(default=None, max_length=80)
    comprobante_base64: Optional[str] = Field(default=None, max_length=2_000_000)
    cuenta_bancaria_id: Optional[UUID] = None

class CuotaAmortizacionResponse(BaseModel):
    id: UUID
    venta_id: UUID
    numero_cuota: int
    fecha_vencimiento: datetime
    monto_usd: float
    monto_pagado_usd: float
    estado: str
    etiqueta_periodo: str = ""
    estado_display: str = "Pendiente"
    monto_pendiente_usd: float = 0.0

    model_config = ConfigDict(from_attributes=True)

class VentaResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    cliente_id: UUID
    vendedor_id: UUID
    total_usd: float
    estado: str
    frecuencia_pago: str = "contado"
    tipo_tasa_usd: Optional[str] = "bcv"
    numero_cuotas: Optional[int] = None
    metodo_pago: str = "efectivo"
    referencia_pago: Optional[str] = None
    tiene_comprobante: bool = False
    cuenta_bancaria_id: Optional[UUID] = None
    detalles: List[DetalleVentaResponse] = []
    cuotas: List[CuotaAmortizacionResponse] = []

    model_config = ConfigDict(from_attributes=True)

# --- TASAS DE CAMBIO ---
class TasaCambioCreate(BaseModel):
    momento: str = Field(default="manana", pattern="^(manana|tarde)$")
    usd_bcv_bs: float
    usd_paralelo_bs: float
    cop_usd: float = Field(gt=0, description="Pesos colombianos por 1 USD")
    eur_bs: float = 0.0

class TasaCambioResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    fecha: datetime
    momento: str
    usd_bs: float
    usd_bcv_bs: Optional[float] = None
    usd_paralelo_bs: Optional[float] = None
    eur_bs: float
    cop_usd: Optional[float] = None
    cop_ves: Optional[float] = None
    activa: bool = True
    origen: Optional[str] = "manual"

    model_config = ConfigDict(from_attributes=True)

class TasaSincronizacionResponse(BaseModel):
    exito: bool
    momento: str
    empresas_actualizadas: int
    usd_bcv_bs: float
    usd_paralelo_bs: float
    cop_usd: float
    fuentes: dict
    mensaje: str
    tasa: Optional[TasaCambioResponse] = None

class ConversionMonedaRequest(BaseModel):
    monto: float = Field(gt=0)
    moneda_origen: str = Field(pattern="^(usd|ves|cop)$")
    moneda_destino: str = Field(pattern="^(usd|ves|cop)$")
    tipo_tasa_usd: str = Field(default="bcv", pattern="^(bcv|paralelo)$")

class ConversionMonedaResponse(BaseModel):
    monto_origen: float
    moneda_origen: str
    monto_destino: float
    moneda_destino: str
    tipo_tasa_usd: str
    tasas_aplicadas: dict

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
    es_transferencia: bool = False
    canal: Optional[str] = Field(default=None, pattern="^(transferencia|pago_movil)$")
    referencia_pago: Optional[str] = Field(default=None, max_length=80)
    comprobante_base64: Optional[str] = Field(default=None, max_length=2_000_000)
    cuenta_bancaria_id: Optional[UUID] = None

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
    es_transferencia: bool = False
    verificado: bool = True
    referencia_pago: Optional[str] = None
    tiene_comprobante: bool = False
    estado_venta: Optional[str] = None
    cuenta_bancaria_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)

class VentaPendienteResponse(BaseModel):
    id: UUID
    cliente_id: UUID
    cliente_nombre: str
    cliente_telefono: Optional[str] = None
    cliente_email: Optional[str] = None
    cliente_direccion: Optional[str] = None
    cliente_direccion_laboral: Optional[str] = None
    latitud_residencia: Optional[float] = None
    longitud_residencia: Optional[float] = None
    latitud_trabajo: Optional[float] = None
    longitud_trabajo: Optional[float] = None
    productos_resumen: str = "—"
    costo_total_usd: Optional[float] = None
    margen_usd: Optional[float] = None
    total_usd: float
    cobrado_usd: float
    saldo_pendiente_usd: float
    frecuencia_pago: str = "contado"
    tipo_credito: str = "—"
    estado: str
    estado_cuenta: str = "Al día"
    proximo_pago: Optional[datetime] = None
    monto_proxima_cuota_usd: float = 0.0
    cuotas_pagadas: int = 0
    cuotas_totales: int = 0
    cuotas: List[CuotaAmortizacionResponse] = []

    model_config = ConfigDict(from_attributes=True)

class EnvioReciboResponse(BaseModel):
    exito: bool
    mensaje: str
    email: Optional[str] = None

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
    proveedor_id: Optional[UUID] = None
    genera_deuda_proveedor: bool = False

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

class AjusteInventarioCreate(BaseModel):
    producto_id: UUID
    tipo: str = Field(pattern="^(entrada|salida)$")
    cantidad: int = Field(gt=0)
    motivo: str = Field(min_length=2, max_length=120)
    almacen_id: Optional[UUID] = None

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
        pattern=(
            "^(ingreso_operativo|pago_vendedor|pago_cobrador|pago_proveedor|"
            "gasto_moto|servicios_operativos|operacion_general)$"
        )
    )
    monto: float = Field(gt=0)
    moneda: str = Field(default="usd", pattern="^(usd|ves|cop)$")
    metodo_pago: Optional[str] = Field(
        default=None,
        pattern="^(efectivo|transferencia|pago_movil|tarjeta|otro)$",
    )
    tasa_aplicada: Optional[float] = None
    descripcion: str
    fecha: Optional[datetime] = None
    empleado_id: Optional[UUID] = None
    proveedor_id: Optional[UUID] = None
    comprobante_base64: Optional[str] = None

class MovimientoFinancieroResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    tipo: str
    categoria: str
    monto_usd: float
    monto_original: Optional[float] = None
    moneda: str
    metodo_pago: Optional[str] = None
    tasa_aplicada: Optional[float] = None
    descripcion: str
    fecha: datetime
    registrado_por_id: UUID
    empleado_id: Optional[UUID] = None
    proveedor_id: Optional[UUID] = None
    tiene_comprobante: bool = False
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

# --- PROVEEDORES ---
class ProveedorCreate(BaseModel):
    nombre: str
    telefono: Optional[str] = None
    rif: Optional[str] = None
    notas: Optional[str] = None
    contacto: Optional[str] = None

class ProveedorUpdate(BaseModel):
    nombre: Optional[str] = None
    telefono: Optional[str] = None
    rif: Optional[str] = None
    notas: Optional[str] = None
    contacto: Optional[str] = None
    activo: Optional[bool] = None

class ProveedorResponse(BaseModel):
    id: UUID
    empresa_id: UUID
    nombre: str
    telefono: Optional[str] = None
    rif: Optional[str] = None
    notas: Optional[str] = None
    saldo_deuda_usd: float = 0.0
    activo: bool

    model_config = ConfigDict(from_attributes=True)

class PagoProveedorRequest(BaseModel):
    monto_usd: float = Field(gt=0)
    descripcion: Optional[str] = None