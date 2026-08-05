from fastapi import FastAPI
from app.models.core import Base
from app.core.db import engine
# Agregamos "ventas" al final
from app.api import empresas, clientes, usuarios, productos, ventas, tasas_cambio, cobros

Base.metadata.create_all(bind=engine)

app = FastAPI(title="API Sistema Ruteros Multimoneda", version="1.0.0")

app.include_router(empresas.router, prefix="/api/v1/empresas", tags=["Empresas"])
app.include_router(usuarios.router, prefix="/api/v1/usuarios", tags=["Usuarios"])
app.include_router(clientes.router, prefix="/api/v1/clientes", tags=["Clientes"])
app.include_router(productos.router, prefix="/api/v1/productos", tags=["Productos"])
# <-- INYECTAMOS LAS VENTAS AQUÍ
app.include_router(ventas.router, prefix="/api/v1/ventas", tags=["Ventas"])
app.include_router(tasas_cambio.router, prefix="/api/v1/tasas-cambio", tags=["Tasas de Cambio"])
app.include_router(cobros.router, prefix="/api/v1/cobros", tags=["Cobros"])

@app.get("/")
def estado_servidor():
    return {
        "estado": "Online",
        "mensaje": "El backend híbrido Multi-Tenant está funcionando correctamente."
    }