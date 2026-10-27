import uuid
import enum
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Boolean, DateTime, Date, ForeignKey, Numeric, Enum, Integer, Text, JSON, TypeDecorator, CHAR,
    UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# ---------- TIPO UUID PORTÁTIL ----------
class GUID(TypeDecorator):
    """Guarda UUID como texto en SQLite, y como UUID nativo si algún día usás Postgres."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID())
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return uuid.UUID(value) if not isinstance(value, uuid.UUID) else value


# ---------- ENUMS ----------
class RolUsuario(str, enum.Enum):
    DUENO = "DUEÑO"
    ADMINISTRADOR = "ADMINISTRADOR"
    VENDEDOR = "VENDEDOR"
    COBRADOR = "COBRADOR"

class TipoTasaUsd(str, enum.Enum):
    BCV = "bcv"
    PARALELO = "paralelo"

class FrecuenciaPago(str, enum.Enum):
    CONTADO = "contado"
    SEMANAL = "semanal"
    QUINCENAL = "quincenal"
    MENSUAL = "mensual"

class EstadoVenta(str, enum.Enum):
    BORRADOR = "borrador"
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    POR_VERIFICAR = "por_verificar"
    PAGADA = "pagada"

class EstadoCuota(str, enum.Enum):
    PENDIENTE = "pendiente"
    PARCIAL = "parcial"
    PAGADA = "pagada"

class MonedaPago(str, enum.Enum):
    BOLIVAR = "bolivar"
    DOLAR = "dolar"
    EURO = "euro"
    PAGO_MOVIL = "pago_movil"
    TRANSFERENCIA = "transferencia"

class TipoCliente(str, enum.Enum):
    MAYORISTA = "mayorista"
    DETAL = "detal"


class DiaVisita(str, enum.Enum):
    LUNES = "LUNES"
    MARTES = "MARTES"
    MIERCOLES = "MIERCOLES"
    JUEVES = "JUEVES"
    VIERNES = "VIERNES"
    SABADO = "SABADO"
    DOMINGO = "DOMINGO"


class TipoVisitaRuta(str, enum.Enum):
    FRECUENTE = "frecuente"
    NUEVO = "nuevo"


class EstadoVisita(str, enum.Enum):
    PENDIENTE = "pendiente"
    VISITADO = "visitado"
    NO_ENCONTRADO = "no_encontrado"

class TipoReferenciaAsiento(str, enum.Enum):
    VENTA = "venta"
    COBRO = "cobro"

class TipoMovimientoInventario(str, enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"


class TipoMovimientoFinanciero(str, enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"


class CategoriaMovimientoFinanciero(str, enum.Enum):
    INGRESO_OPERATIVO = "ingreso_operativo"
    PAGO_VENDEDOR = "pago_vendedor"
    PAGO_COBRADOR = "pago_cobrador"
    PAGO_PROVEEDOR = "pago_proveedor"
    GASTO_MOTO = "gasto_moto"
    SERVICIOS_OPERATIVOS = "servicios_operativos"
    OPERACION_GENERAL = "operacion_general"


class MonedaGasto(str, enum.Enum):
    USD = "usd"
    VES = "ves"
    COP = "cop"


class MetodoPagoSalida(str, enum.Enum):
    EFECTIVO = "efectivo"
    TRANSFERENCIA = "transferencia"
    PAGO_MOVIL = "pago_movil"
    TARJETA = "tarjeta"
    OTRO = "otro"


class EstadoPagoNomina(str, enum.Enum):
    PENDIENTE = "pendiente"
    REALIZADO = "realizado"


class CanalCuentaEmpleado(str, enum.Enum):
    TRANSFERENCIA = "transferencia"
    PAGO_MOVIL = "pago_movil"


# ---------- PAÍS (catálogo SaaS multiregión) ----------
class Pais(Base):
    __tablename__ = "paises"
    __table_args__ = (UniqueConstraint("codigo_iso", name="uq_paises_codigo_iso"),)

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    nombre = Column(String(80), nullable=False)
    codigo_iso = Column(String(3), nullable=False, index=True)
    moneda_principal = Column(String(3), nullable=False)
    simbolo_moneda = Column(String(8), nullable=False)
    locale = Column(String(10), nullable=True)
    zona_horaria = Column(String(40), nullable=True)
    activo = Column(Boolean, nullable=False, default=True)
    configuracion_bancaria = Column(JSON, nullable=False)
    configuracion_fiscal = Column(JSON, nullable=True)
    configuracion_ui = Column(JSON, nullable=True)
    sueldo_base_legal = Column(Numeric(14, 2), nullable=False, default=0)
    porcentaje_comision_venta = Column(Numeric(5, 2), nullable=False, default=0)
    porcentaje_comision_cobro = Column(Numeric(5, 2), nullable=False, default=0)
    bono_incentivo = Column(Numeric(14, 2), nullable=False, default=0)
    bandera = Column(String(8), nullable=True)
    prefijo_telefonico = Column(String(8), nullable=True)
    formato_numero = Column(String(32), nullable=True)
    formato_fecha = Column(String(32), nullable=True)
    payment_currencies = Column(JSON, nullable=True)
    tasas_cambio_referencia = Column(JSON, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    payroll_rules = relationship("PayrollRule", back_populates="pais")


class PayrollRule(Base):
    """
    Reglas de nómina / sueldo versionadas por país y año.
    Colección PocketBase: ``payroll_rules`` (alias lógico de ``countries`` + leyes).
    """

    __tablename__ = "payroll_rules"
    __table_args__ = (
        UniqueConstraint(
            "pais_id",
            "year",
            "effective_from",
            "moneda_salario",
            name="uq_payroll_rules_pais_year_effective_moneda",
        ),
        Index("ix_payroll_rules_pais_year", "pais_id", "year"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=False, index=True)
    year = Column(Integer, nullable=False)
    effective_from = Column(Date, nullable=False)
    salario_minimo_mensual = Column(Numeric(14, 2), nullable=False, default=0)
    moneda_salario = Column(String(3), nullable=False)
    auxilio_transporte = Column(Numeric(14, 2), nullable=True)
    aportes_empleado = Column(JSON, nullable=True)
    aportes_empleador = Column(JSON, nullable=True)
    prestaciones = Column(JSON, nullable=True)
    jornada_max_horas_semanales = Column(Integer, nullable=True)
    recargos = Column(JSON, nullable=True)
    porcentaje_comision_venta = Column(Numeric(5, 2), nullable=False, default=0)
    porcentaje_comision_cobro = Column(Numeric(5, 2), nullable=False, default=0)
    bono_incentivo = Column(Numeric(14, 2), nullable=False, default=0)
    payment_currencies = Column(JSON, nullable=True)
    tasas_cambio_referencia = Column(JSON, nullable=True)
    source_url = Column(Text, nullable=True)
    verified = Column(Boolean, nullable=False, default=False)
    borrador = Column(Boolean, nullable=False, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    pais = relationship("Pais", back_populates="payroll_rules")


# ---------- EMPRESA (tenant) ----------
class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    nombre = Column(String, nullable=False)
    activa = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    banco = Column(String(120), nullable=True)
    tipo_cuenta = Column(String(40), nullable=True)
    numero_cuenta = Column(String(64), nullable=True)
    cedula_nit = Column(String(32), nullable=True)

    usuarios = relationship("Usuario", back_populates="empresa")
    clientes = relationship("Cliente", back_populates="empresa")
    productos = relationship("Producto", back_populates="empresa")
    configuracion_fiscal = relationship(
        "ConfiguracionFiscal", back_populates="empresa", uselist=False
    )
    almacenes = relationship("Almacen", back_populates="empresa")
    cuentas_bancarias = relationship("CuentaBancaria", back_populates="empresa")


class CuentaBancaria(Base):
    __tablename__ = "cuentas_bancarias"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, index=True)
    banco = Column(String(120), nullable=False)
    tipo_cuenta = Column(String(40), nullable=False)
    numero_cuenta = Column(String(64), nullable=False)
    titular = Column(String(160), nullable=False)
    documento = Column(String(32), nullable=False)
    canal = Column(String(20), nullable=False, default="transferencia")
    telefono = Column(String(20), nullable=True)
    activa = Column(Boolean, nullable=False, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="cuentas_bancarias")


class CuentaBancariaEmpleado(Base):
    """Cuenta bancaria del empleado (vendedor/cobrador) para recibir nómina."""

    __tablename__ = "cuentas_bancarias_empleados"
    __table_args__ = (
        Index("ix_cuenta_bancaria_empleado_usuario", "usuario_id"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, index=True)
    usuario_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False, unique=True)
    banco = Column(String(120), nullable=False)
    tipo_cuenta = Column(String(40), nullable=False)
    numero_cuenta = Column(String(64), nullable=True)
    titular = Column(String(160), nullable=False)
    documento_identidad = Column(String(32), nullable=False)
    canal = Column(String(20), nullable=False, default="transferencia")
    telefono_pago_movil = Column(String(20), nullable=True)
    activa = Column(Boolean, nullable=False, default=True)
    verificada_por_dueno = Column(Boolean, nullable=False, default=False)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", back_populates="cuenta_bancaria_empleado")


# ---------- USUARIO ----------
class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    nombre = Column(String, nullable=False)
    username = Column(String, unique=True, index=True) # <-- AQUÍ ESTÁ AGREGADO EL USERNAME
    telefono = Column(String, nullable=True)
    rol = Column(Enum(RolUsuario), nullable=False)
    password_hash = Column(String(255), nullable=False)
    sueldo_base_usd = Column(Numeric(10, 2), nullable=False, default=0)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="usuarios")
    cuenta_bancaria_empleado = relationship(
        "CuentaBancariaEmpleado",
        back_populates="usuario",
        uselist=False,
    )


# ---------- CLIENTE ----------
class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (
        UniqueConstraint("identificacion", name="uq_clientes_identificacion_global"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    vendedor_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=True)
    nombre = Column(String, nullable=False)
    identificacion = Column(String, nullable=False, index=True)
    telefono = Column(String, nullable=True)
    telefono_secundario = Column(String, nullable=True)
    direccion = Column(Text, nullable=True)
    punto_referencia = Column(String, nullable=True)
    latitud_residencia = Column(Numeric(10, 7), nullable=True)
    longitud_residencia = Column(Numeric(10, 7), nullable=True)
    empresa_trabajo = Column(String, nullable=True)
    direccion_laboral = Column(Text, nullable=True)
    latitud_trabajo = Column(Numeric(10, 7), nullable=True)
    longitud_trabajo = Column(Numeric(10, 7), nullable=True)
    ref_familiar_nombre = Column(String, nullable=True)
    ref_familiar_parentesco = Column(String, nullable=True)
    ref_familiar_telefono = Column(String, nullable=True)
    email = Column(String, nullable=True)
    score_credito = Column(Integer, nullable=False, default=70)
    total_compras = Column(Integer, nullable=False, default=0)
    monto_compras_usd = Column(Numeric(12, 2), nullable=False, default=0)
    total_pagos = Column(Integer, nullable=False, default=0)
    monto_pagos_usd = Column(Numeric(12, 2), nullable=False, default=0)
    estado_morosidad = Column(String(20), nullable=False, default="al_dia")
    clasificacion_credito = Column(String(40), nullable=False, default="Bueno")
    tipo_cliente = Column(Enum(TipoCliente), default=TipoCliente.DETAL)
    dia_visita = Column(Enum(DiaVisita), nullable=True)
    orden_secuencial = Column(Integer, nullable=True)
    # Día legible del recorrido (Lunes, Martes, …) y parada GPS de ese día.
    dia_ruta = Column(String(20), nullable=True)
    orden_ruta = Column(Integer, nullable=True)
    tipo_visita_ruta = Column(Enum(TipoVisitaRuta), default=TipoVisitaRuta.FRECUENTE)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="clientes")
    ventas = relationship("Venta", back_populates="cliente")
    notas_seguimiento = relationship(
        "NotaSeguimientoCobranza",
        back_populates="cliente",
        cascade="all, delete-orphan",
    )
    acuerdos_pago = relationship(
        "AcuerdoPago",
        back_populates="cliente",
        cascade="all, delete-orphan",
    )


class VisitaDiaria(Base):
    """Registro de visita/cobro por cliente en una fecha calendario."""
    __tablename__ = "visitas_diarias"
    __table_args__ = (
        UniqueConstraint(
            "cliente_id", "vendedor_id", "fecha",
            name="uq_visita_cliente_vendedor_fecha",
        ),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    cliente_id = Column(GUID(), ForeignKey("clientes.id"), nullable=False)
    vendedor_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    estado = Column(Enum(EstadoVisita), nullable=False, default=EstadoVisita.VISITADO)
    notas = Column(Text, nullable=True)
    latitud_visita = Column(Numeric(10, 7), nullable=True)
    longitud_visita = Column(Numeric(10, 7), nullable=True)
    marcado_en = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", foreign_keys=[cliente_id])
    vendedor = relationship("Usuario", foreign_keys=[vendedor_id])


class NotaSeguimientoCobranza(Base):
    """Historial de cobranza humanizada por cliente.

    Cada fila es una nota inmutable. El motivo y el estado vigentes son
    los de la nota más reciente del cliente dentro de su empresa.
    Se guarda como texto (no ENUM de Postgres) para crear la tabla igual
    en SQLite local y en Supabase sin migrar tipos.
    """

    __tablename__ = "notas_seguimiento_cobranza"
    __table_args__ = (
        Index("ix_notas_seguimiento_empresa_cliente", "empresa_id", "cliente_id"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(GUID(), ForeignKey("clientes.id"), nullable=False, index=True)
    usuario_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    motivo = Column(String(40), nullable=False)
    estado_consideracion = Column(String(40), nullable=False)
    observacion = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="notas_seguimiento")
    usuario = relationship("Usuario")


class AcuerdoPago(Base):
    """Reestructuración temporal. No reescribe cuotas ni el estado de la venta.

    Mientras el acuerdo sigue activo y la fecha límite no venció, la carpeta
    crítica suspende la alerta estricta. El plan de amortización original
    permanece para cobranza, buró y sincronización.
    """

    __tablename__ = "acuerdos_pago"
    __table_args__ = (
        Index("ix_acuerdos_pago_empresa_cliente", "empresa_id", "cliente_id"),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(GUID(), ForeignKey("clientes.id"), nullable=False, index=True)
    usuario_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False)
    monto_acordado_usd = Column(Numeric(12, 2), nullable=False)
    fecha_limite = Column(Date, nullable=False)
    cuotas_pactadas = Column(Integer, nullable=False, default=1)
    estado = Column(String(20), nullable=False, default="activo")
    nota_consideracion = Column(Text, nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="acuerdos_pago")
    usuario = relationship("Usuario")


class EventoBuroCredito(Base):
    """Historial anónimo compartido por identificación (sin exponer empresa origen)."""
    __tablename__ = "eventos_buro_credito"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    identificacion = Column(String, nullable=False, index=True)
    tipo_evento = Column(String, nullable=False)
    mensaje = Column(String, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)


# ---------- PRODUCTO ----------
class Producto(Base):
    __tablename__ = "productos"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    proveedor_id = Column(GUID(), ForeignKey("proveedores.id"), nullable=True)
    nombre = Column(String, nullable=False)
    sku = Column(String, nullable=True)
    categoria = Column(String, nullable=True)
    precio_usd = Column(Numeric(10, 2), nullable=False)
    precio_ves = Column(Numeric(14, 2), nullable=True)
    precio_cop = Column(Numeric(14, 2), nullable=True)
    costo_usd = Column(Numeric(10, 2), nullable=False, default=0)
    stock = Column(Integer, default=0)
    stock_minimo = Column(Integer, default=0)
    activo = Column(Boolean, default=True)
    proveedor = Column(String, nullable=True)
    condicion_pago = Column(String, nullable=True)
    fecha_limite_pago = Column(Date, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="productos")
    proveedor = relationship("Proveedor", back_populates="productos")
    precios = relationship("PrecioProducto", back_populates="producto")
    lotes = relationship("LoteInventario", back_populates="producto")


# ---------- CONFIGURACIÓN FISCAL MULTI-PAÍS ----------
class ConfiguracionFiscal(Base):
    __tablename__ = "configuracion_fiscal"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, unique=True)
    pais = Column(String, nullable=False, default="VE")
    moneda_base = Column(String, nullable=False, default="USD")
    iva_porcentaje = Column(Numeric(5, 2), nullable=False, default=16.00)
    igtf_porcentaje = Column(Numeric(5, 2), nullable=False, default=3.00)
    aplica_igtf_divisas = Column(Boolean, default=True)
    razon_social = Column(String, nullable=True)
    rif = Column(String, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="configuracion_fiscal")


# ---------- INVENTARIO MULTI-ALMACÉN ----------
class Almacen(Base):
    __tablename__ = "almacenes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    nombre = Column(String, nullable=False)
    ubicacion = Column(String, nullable=True)
    es_principal = Column(Boolean, default=False)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    empresa = relationship("Empresa", back_populates="almacenes")
    lotes = relationship("LoteInventario", back_populates="almacen")


class LoteInventario(Base):
    __tablename__ = "lotes_inventario"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    producto_id = Column(GUID(), ForeignKey("productos.id"), nullable=False)
    almacen_id = Column(GUID(), ForeignKey("almacenes.id"), nullable=False)
    proveedor_id = Column(GUID(), ForeignKey("proveedores.id"), nullable=True)
    genera_deuda_proveedor = Column(Boolean, default=False)
    numero_lote = Column(String, nullable=False)
    cantidad = Column(Integer, nullable=False, default=0)
    costo_unitario_usd = Column(Numeric(10, 2), nullable=False, default=0)
    fecha_vencimiento = Column(DateTime, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    producto = relationship("Producto", back_populates="lotes")
    almacen = relationship("Almacen", back_populates="lotes")


class PrecioProducto(Base):
    __tablename__ = "precios_producto"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    producto_id = Column(GUID(), ForeignKey("productos.id"), nullable=False)
    tipo_cliente = Column(Enum(TipoCliente), nullable=False)
    precio_usd = Column(Numeric(10, 2), nullable=False)

    producto = relationship("Producto", back_populates="precios")


class MovimientoInventario(Base):
    __tablename__ = "movimientos_inventario"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    producto_id = Column(GUID(), ForeignKey("productos.id"), nullable=False)
    almacen_id = Column(GUID(), ForeignKey("almacenes.id"), nullable=False)
    lote_id = Column(GUID(), ForeignKey("lotes_inventario.id"), nullable=True)
    tipo = Column(Enum(TipoMovimientoInventario), nullable=False)
    cantidad = Column(Integer, nullable=False)
    referencia_tipo = Column(String, nullable=True)
    referencia_id = Column(GUID(), nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)


# ---------- CONTABILIDAD (LIBRO DIARIO) ----------
class AsientoContable(Base):
    __tablename__ = "asientos_contables"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    fecha = Column(DateTime, nullable=False)
    referencia_tipo = Column(Enum(TipoReferenciaAsiento), nullable=False)
    referencia_id = Column(GUID(), nullable=False)
    descripcion = Column(String, nullable=False)
    tasa_usd_aplicada = Column(Numeric(12, 4), nullable=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    lineas = relationship("LineaAsiento", back_populates="asiento", cascade="all, delete-orphan")


class LineaAsiento(Base):
    __tablename__ = "lineas_asiento"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    asiento_id = Column(GUID(), ForeignKey("asientos_contables.id"), nullable=False)
    cuenta_codigo = Column(String, nullable=False)
    cuenta_nombre = Column(String, nullable=False)
    debito_usd = Column(Numeric(12, 4), nullable=False, default=0)
    credito_usd = Column(Numeric(12, 4), nullable=False, default=0)
    debito_bs = Column(Numeric(14, 4), nullable=False, default=0)
    credito_bs = Column(Numeric(14, 4), nullable=False, default=0)

    asiento = relationship("AsientoContable", back_populates="lineas")


# ---------- TASA DE CAMBIO ----------
class TasaCambio(Base):
    __tablename__ = "tasas_cambio"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    momento = Column(String, nullable=False, default="manana")
    usd_bs = Column(Numeric(12, 4), nullable=False)
    usd_bcv_bs = Column(Numeric(12, 4), nullable=True)
    usd_paralelo_bs = Column(Numeric(12, 4), nullable=True)
    eur_bs = Column(Numeric(12, 4), nullable=False, default=0)
    cop_usd = Column(Numeric(12, 4), nullable=True)
    cop_ves = Column(Numeric(14, 4), nullable=True)
    activa = Column(Boolean, default=True)
    origen = Column(String, nullable=True, default="manual")


# ---------- VENTA ----------
class Venta(Base):
    __tablename__ = "ventas"

    id = Column(GUID(), primary_key=True)  # generado en el celular (offline-first)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    cliente_id = Column(GUID(), ForeignKey("clientes.id"), nullable=False)
    vendedor_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False)

    fecha = Column(DateTime, nullable=False)
    total_usd = Column(Numeric(10, 2), nullable=False)

    tasa_usd_aplicada = Column(Numeric(12, 4), nullable=False)
    tasa_eur_aplicada = Column(Numeric(12, 4), nullable=False)
    tipo_tasa_usd = Column(Enum(TipoTasaUsd), default=TipoTasaUsd.BCV)
    numero_cuotas = Column(Integer, nullable=True)

    frecuencia_pago = Column(Enum(FrecuenciaPago), nullable=False)
    estado = Column(Enum(EstadoVenta), default=EstadoVenta.PENDIENTE)
    metodo_pago = Column(String(20), nullable=False, default="efectivo")
    referencia_pago = Column(String(80), nullable=True)
    comprobante_base64 = Column(Text, nullable=True)
    cuenta_bancaria_id = Column(GUID(), ForeignKey("cuentas_bancarias.id"), nullable=True)

    sincronizado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    detalles = relationship("DetalleVenta", back_populates="venta")
    cobros = relationship("Cobro", back_populates="venta")
    cuotas = relationship("CuotaAmortizacion", back_populates="venta", cascade="all, delete-orphan")
    cliente = relationship("Cliente")

    @property
    def tiene_comprobante(self) -> bool:
        return bool(self.comprobante_base64)


class CuotaAmortizacion(Base):
    __tablename__ = "cuotas_amortizacion"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    venta_id = Column(GUID(), ForeignKey("ventas.id"), nullable=False)
    numero_cuota = Column(Integer, nullable=False)
    fecha_vencimiento = Column(DateTime, nullable=False)
    monto_usd = Column(Numeric(10, 2), nullable=False)
    monto_pagado_usd = Column(Numeric(10, 2), nullable=False, default=0)
    estado = Column(Enum(EstadoCuota), default=EstadoCuota.PENDIENTE)

    venta = relationship("Venta", back_populates="cuotas")


class DetalleVenta(Base):
    __tablename__ = "detalles_venta"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    venta_id = Column(GUID(), ForeignKey("ventas.id"), nullable=False)
    producto_id = Column(GUID(), ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False)
    precio_unitario_usd = Column(Numeric(10, 2), nullable=False)

    venta = relationship("Venta", back_populates="detalles")


# ---------- COBRO (append-only) ----------
class Cobro(Base):
    __tablename__ = "cobros"

    id = Column(GUID(), primary_key=True)  # generado en el celular
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    venta_id = Column(GUID(), ForeignKey("ventas.id"), nullable=False)
    cobrador_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False)

    fecha = Column(DateTime, nullable=False)
    monto_usd = Column(Numeric(10, 2), nullable=False)

    moneda_pago = Column(Enum(MonedaPago), nullable=False)
    tasa_usd_aplicada = Column(Numeric(12, 4), nullable=False)
    tasa_eur_aplicada = Column(Numeric(12, 4), nullable=False)
    es_transferencia = Column(Boolean, nullable=False, default=False)
    verificado = Column(Boolean, nullable=False, default=True)
    referencia_pago = Column(String(80), nullable=True)
    comprobante_base64 = Column(Text, nullable=True)
    cuenta_bancaria_id = Column(GUID(), ForeignKey("cuentas_bancarias.id"), nullable=True)

    sincronizado = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    venta = relationship("Venta", back_populates="cobros")

    @property
    def tiene_comprobante(self) -> bool:
        return bool(self.comprobante_base64)


# ---------- FINANZAS / NÓMINA ----------
class ConfiguracionNomina(Base):
    __tablename__ = "configuracion_nomina"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, unique=True)
    comision_vendedor_por_articulo_usd = Column(Numeric(10, 2), nullable=False, default=10.00)
    comision_vendedor_por_venta_usd = Column(Numeric(10, 2), nullable=False, default=10.00)
    comision_cobrador_porcentaje = Column(Numeric(5, 2), nullable=False, default=10.00)
    sueldo_base_cobrador_usd = Column(Numeric(10, 2), nullable=False, default=0.00)
    dias_periodo_nomina = Column(Integer, nullable=False, default=8)
    fecha_ancla_periodo = Column(Date, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)


class PagoNomina(Base):
    """Corte de nómina por periodo (p. ej. cada 8 días) por empleado."""

    __tablename__ = "pagos_nomina"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id",
            "usuario_id",
            "periodo_desde",
            "periodo_hasta",
            name="uq_pago_nomina_empleado_periodo",
        ),
    )

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False, index=True)
    usuario_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False, index=True)
    rol = Column(Enum(RolUsuario), nullable=False)
    periodo_desde = Column(Date, nullable=False)
    periodo_hasta = Column(Date, nullable=False)
    num_ventas = Column(Integer, nullable=False, default=0)
    total_cobrado_usd = Column(Numeric(12, 2), nullable=False, default=0)
    sueldo_base_usd = Column(Numeric(10, 2), nullable=False, default=0)
    comision_usd = Column(Numeric(12, 2), nullable=False, default=0)
    total_calculado_usd = Column(Numeric(12, 2), nullable=False, default=0)
    estado = Column(Enum(EstadoPagoNomina), nullable=False, default=EstadoPagoNomina.PENDIENTE)
    movimiento_financiero_id = Column(
        GUID(), ForeignKey("movimientos_financieros.id"), nullable=True
    )
    fecha_pago = Column(DateTime, nullable=True)
    pagado_por_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=True)
    notas = Column(String(500), nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    usuario = relationship("Usuario", foreign_keys=[usuario_id])
    movimiento_financiero = relationship("MovimientoFinanciero", foreign_keys=[movimiento_financiero_id])


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    nombre = Column(String, nullable=False)
    telefono = Column(String, nullable=True)
    rif = Column(String, nullable=True)
    notas = Column(Text, nullable=True)
    saldo_deuda_usd = Column(Numeric(12, 2), nullable=False, default=0)
    activo = Column(Boolean, default=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)

    productos = relationship("Producto", back_populates="proveedor")


class MovimientoFinanciero(Base):
    __tablename__ = "movimientos_financieros"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    pais_id = Column(GUID(), ForeignKey("paises.id"), nullable=True, index=True)
    empresa_id = Column(GUID(), ForeignKey("empresas.id"), nullable=False)
    tipo = Column(Enum(TipoMovimientoFinanciero), nullable=False)
    categoria = Column(Enum(CategoriaMovimientoFinanciero), nullable=False)
    monto_usd = Column(Numeric(12, 2), nullable=False)
    monto_original = Column(Numeric(14, 2), nullable=True)
    moneda = Column(Enum(MonedaGasto), nullable=False, default=MonedaGasto.USD)
    metodo_pago = Column(Enum(MetodoPagoSalida), nullable=True)
    tasa_aplicada = Column(Numeric(12, 4), nullable=True)
    descripcion = Column(Text, nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.utcnow)
    registrado_por_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=False)
    empleado_id = Column(GUID(), ForeignKey("usuarios.id"), nullable=True)
    proveedor_id = Column(GUID(), ForeignKey("proveedores.id"), nullable=True)
    comprobante_base64 = Column(Text, nullable=True)
    periodo_desde = Column(DateTime, nullable=True)
    periodo_hasta = Column(DateTime, nullable=True)
    aprobado = Column(Boolean, default=False)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)