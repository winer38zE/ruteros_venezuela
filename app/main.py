import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.seguridad import CabecerasSeguridadMiddleware
from app.core.db import PocketBaseDep
from app.core.pocketbase_init import preparar_pocketbase_al_arranque_seguro
from app.core.scheduler import iniciar_scheduler, detener_scheduler

# Importamos todas tus rutas organizadas
from app.api import (
    empresas, clientes, usuarios, productos, ventas,
    tasas_cambio, cobros, configuracion_fiscal, inventario, contabilidad, finanzas,
    proveedores,
    auth_router,
    rutas,
    whatsapp,
    cartera_critica,
    cartera,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    preparar_pocketbase_al_arranque_seguro()
    try:
        iniciar_scheduler()
    except Exception:
        logger.exception("Scheduler de tasas no pudo iniciarse.")
    yield
    detener_scheduler()


app = FastAPI(
    title="API Sistema Ruteros Multimoneda",
    version="2.0.0",
    lifespan=lifespan,
)

_origenes = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
if not _origenes:
    _origenes = ["*"]
# El comodín no puede ir con credenciales. La app móvil usa X-Usuario-Id, no cookies.
_cors_abierto = _origenes == ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origenes,
    allow_credentials=not _cors_abierto,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Usuario-Id"],
)
app.add_middleware(CabecerasSeguridadMiddleware)

# Registro de Routers principales
app.include_router(auth_router.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(empresas.router, prefix="/api/v1/empresas", tags=["Empresas"])
app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(proveedores.router, prefix="/api/v1/proveedores", tags=["Proveedores"])
app.include_router(clientes.router, prefix="/api/v1/clientes", tags=["Clientes"])
app.include_router(productos.router, prefix="/api/v1/productos", tags=["Productos"])
app.include_router(ventas.router, prefix="/api/v1/ventas", tags=["Ventas"])
app.include_router(tasas_cambio.router, prefix="/api/v1/tasas-cambio", tags=["Tasas de Cambio"])
app.include_router(cobros.router, prefix="/api/v1/cobros", tags=["Cobros"])
app.include_router(
    cartera_critica.router,
    prefix="/api/v1/cartera-critica",
    tags=["Cartera crítica"],
)
app.include_router(cartera.router, prefix="/api/v1/cartera", tags=["Cartera"])
app.include_router(rutas.router, prefix="/api/v1/rutas", tags=["Rutas"])
app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["WhatsApp"])
app.include_router(
    configuracion_fiscal.router,
    prefix="/api/v1/configuracion-fiscal",
    tags=["Configuración Fiscal"],
)
app.include_router(inventario.router, prefix="/api/v1/inventario", tags=["Inventario"])
app.include_router(contabilidad.router, prefix="/api/v1/contabilidad", tags=["Contabilidad"])
app.include_router(finanzas.router, prefix="/api/v1/finanzas", tags=["Finanzas"])

# Ruta base de estado del servidor
@app.get("/")
def estado_servidor():
    return {
        "estado": "Online",
        "mensaje": "El backend híbrido Multi-Tenant está funcionando correctamente."
    }

# Endpoint de prueba para verificar conexión y funcionamiento rápido
@app.get("/api/v1/test-conexion")
def probar_conexion(pb: PocketBaseDep):
    return {
        "status": "success",
        "codigo": 200,
        "mensaje": "ED NET PRO - Mi primera API inteligente",
        "pocketbase_url": pb.base_url,
    }
