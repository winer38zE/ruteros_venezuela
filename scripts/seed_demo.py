"""
Carga datos de demostración en ruteros_local.db para probar la app completa.

Uso:
    python scripts/seed_demo.py

Usuarios creados (password: 123 en todos):
    dueno  → DUEÑO
    vend   → VENDEDOR
    cob    → COBRADOR
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fastapi.testclient import TestClient
from app.main import app
from app.models.core import Base, Usuario, Cliente
from app.core import db as db_module
from sqlalchemy.orm import sessionmaker

from app.core.migrate import aplicar_migraciones_sqlite

c = TestClient(app)


def _post(path: str, json: dict, headers: dict | None = None):
    r = c.post(path, json=json, headers=headers or {})
    if r.status_code >= 400:
        raise RuntimeError(f"POST {path} → {r.status_code}: {r.text}")
    return r.json()


def _get(path: str, headers: dict | None = None):
    r = c.get(path, headers=headers or {})
    if r.status_code >= 400:
        raise RuntimeError(f"GET {path} → {r.status_code}: {r.text}")
    return r.json()


def main():
    Session = sessionmaker(bind=db_module.engine)
    db = Session()
    try:
        tiene_dueno = db.query(Usuario).filter(Usuario.username == "dueno").first()
        demo_ok = db.query(Cliente).filter(Cliente.nombre == "Bodega La Esquina").first()
        if tiene_dueno and demo_ok:
            print("Datos demo ya existen. Nada que hacer.")
            print("Login: dueno / vend / cob  (password: 123)")
            return
        if tiene_dueno and not demo_ok:
            print("Demo parcial detectado — completando catálogo y venta de ejemplo...")
    finally:
        db.close()

    if not tiene_dueno:
        print("Creando empresa ED NET PRO...")
        _post("/api/v1/empresas/", {"nombre": "ED NET PRO Ruteros"})

        print("Creando usuarios dueno / vend / cob ...")
        dueno = _post("/api/v1/usuarios/", {
            "nombre": "Dueño Demo", "username": "dueno", "password": "123", "rol": "DUEÑO",
        })
        vend = _post("/api/v1/usuarios/", {
            "nombre": "Vendedor Demo", "username": "vend", "password": "123", "rol": "VENDEDOR",
        })
        cob = _post("/api/v1/usuarios/", {
            "nombre": "Cobrador Demo", "username": "cob", "password": "123", "rol": "COBRADOR",
        })

        print("Configuración fiscal Venezuela...")
        _post("/api/v1/configuracion-fiscal/", {
            "pais": "VE",
            "razon_social": "ED NET PRO C.A.",
            "rif": "J-12345678-9",
        })
    else:
        db2 = Session()
        try:
            dueno_row = db2.query(Usuario).filter(Usuario.username == "dueno").first()
            vend_row = db2.query(Usuario).filter(Usuario.username == "vend").first()
            cob_row = db2.query(Usuario).filter(Usuario.username == "cob").first()
            dueno = {"id": str(dueno_row.id)}
            vend = {"id": str(vend_row.id)}
            cob = {"id": str(cob_row.id)}
        finally:
            db2.close()

    print("Clientes, productos y almacén...")
    cli_det = _post("/api/v1/clientes/", {
        "nombre_completo": "Bodega La Esquina", "tipo_cliente": "detal",
    })
    cli_may = _post("/api/v1/clientes/", {
        "nombre_completo": "Distribuidora Norte", "tipo_cliente": "mayorista",
    })
    prod = _post("/api/v1/productos/", {
        "nombre": "Harina PAN 1kg",
        "precio_base_usd": 1.50,
        "stock_actual": 200,
        "precio_detal_usd": 1.80,
        "precio_mayorista_usd": 1.40,
    })
    _post("/api/v1/productos/", {
        "nombre": "Aceite 900ml",
        "precio_base_usd": 2.20,
        "stock_actual": 150,
        "precio_detal_usd": 2.50,
        "precio_mayorista_usd": 2.00,
    })
    alm = _post("/api/v1/inventario/almacenes", {
        "nombre": "Almacén Principal", "es_principal": True,
    })

    print("Tasa de cambio del día...")
    _post("/api/v1/tasas-cambio/", {"momento": "manana", "usd_bs": 50.0, "eur_bs": 55.0})

    print("Venta de ejemplo (pendiente de cobro)...")
    venta = _post(
        "/api/v1/ventas/",
        {
            "cliente_id": cli_det["id"],
            "total_usd": 36.0,
            "tasa_usd_aplicada": 50.0,
            "tasa_eur_aplicada": 55.0,
            "frecuencia_pago": "semanal",
            "almacen_id": alm["id"],
            "detalles": [
                {"producto_id": prod["id"], "cantidad": 20, "tipo_precio": "detal"},
            ],
        },
        headers={"X-Usuario-Id": vend["id"]},
    )

    resumen = _get("/api/v1/contabilidad/resumen", headers={"X-Usuario-Id": dueno["id"]})
    pendientes = _get(
        "/api/v1/cobros/ventas-pendientes",
        headers={"X-Usuario-Id": cob["id"]},
    )

    print("\n✅ Demo lista en ruteros_local.db")
    print(f"   Venta pendiente: ${venta['total_usd']} — cliente: {pendientes[0]['cliente_nombre']}")
    print(f"   Asientos contables: {resumen['asientos_generados']}")
    print("\nLogin Flutter:")
    print("   dueno  → Contabilidad + Inventario + Ventas + Cobros")
    print("   vend   → Mis Ventas")
    print("   cob    → Mis Cobros")


if __name__ == "__main__":
    aplicar_migraciones_sqlite(db_module.engine)
    Base.metadata.create_all(bind=db_module.engine)
    main()
