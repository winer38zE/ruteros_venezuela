"""
Importa datos desde SQLite (ruteros_local.db) hacia PocketBase.

Requisitos:
  - PocketBase en marcha y accesible (POCKETBASE_URL).
  - ADMIN_EMAIL / ADMIN_PASSWORD con permisos de superusuario.
  - Archivo SQLite con el esquema Ruteros (SQLAlchemy).

Uso:
  python scripts/migrate_sqlite_to_pocketbase.py
  python scripts/migrate_sqlite_to_pocketbase.py --sqlite ./ruteros_local.db
  python scripts/migrate_sqlite_to_pocketbase.py --dry-run
  python scripts/migrate_sqlite_to_pocketbase.py --skip-existing
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, inspect as sa_inspect
from sqlalchemy.orm import sessionmaker
from pocketbase.errors import ClientResponseError

from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
from app.core.pb_orm.mapper import collection_name, model_to_record, record_id
from app.core.pb_schema import asegurar_colecciones
from app.models.core import (
    AcuerdoPago,
    Almacen,
    AsientoContable,
    Cliente,
    Cobro,
    ConfiguracionFiscal,
    ConfiguracionNomina,
    CuentaBancaria,
    CuentaBancariaEmpleado,
    CuotaAmortizacion,
    DetalleVenta,
    Empresa,
    EventoBuroCredito,
    LineaAsiento,
    LoteInventario,
    MovimientoFinanciero,
    MovimientoInventario,
    NotaSeguimientoCobranza,
    PagoNomina,
    PrecioProducto,
    Producto,
    Proveedor,
    TasaCambio,
    Usuario,
    Venta,
    VisitaDiaria,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("migrate_sqlite_to_pb")

# Orden respetando claves foráneas
MIGRATION_ORDER: list[type] = [
    Empresa,
    CuentaBancaria,
    ConfiguracionFiscal,
    ConfiguracionNomina,
    Almacen,
    Usuario,
    CuentaBancariaEmpleado,
    Proveedor,
    Cliente,
    Producto,
    PrecioProducto,
    LoteInventario,
    TasaCambio,
    Venta,
    DetalleVenta,
    CuotaAmortizacion,
    Cobro,
    AsientoContable,
    LineaAsiento,
    MovimientoInventario,
    MovimientoFinanciero,
    PagoNomina,
    VisitaDiaria,
    NotaSeguimientoCobranza,
    AcuerdoPago,
    EventoBuroCredito,
]

DEFAULT_SQLITE_CANDIDATES = (
    "ruteros_local.db",
    os.path.join("data", "ruteros.db"),
    os.path.join("app", "data", "ruteros.db"),
)


def resolve_sqlite_path(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            raise FileNotFoundError(f"No existe el archivo SQLite: {p}")
        return p
    env_url = os.getenv("DATABASE_URL", "")
    if env_url.startswith("sqlite:///"):
        raw = env_url.replace("sqlite:///", "", 1)
        p = Path(raw)
        if p.is_file():
            return p.resolve()
    for rel in DEFAULT_SQLITE_CANDIDATES:
        p = Path(rel)
        if p.is_file():
            return p.resolve()
    raise FileNotFoundError(
        "No se encontró SQLite. Pasa --sqlite ruta/al/archivo.db "
        f"(buscado: {', '.join(DEFAULT_SQLITE_CANDIDATES)})"
    )


def upsert_record(pb, model: type, row, *, dry_run: bool, skip_existing: bool) -> str:
    name = collection_name(model)
    body = model_to_record(row)
    rid = record_id(row)
    body["id"] = rid

    if dry_run:
        return "dry-run"

    try:
        pb.collection(name).get_one(rid)
        if skip_existing:
            return "skipped"
        pb.collection(name).update(rid, body)
        return "updated"
    except ClientResponseError as exc:
        if exc.status != 404:
            raise
        pb.collection(name).create(body)
        return "created"


def migrate(sqlite_path: Path, *, dry_run: bool, skip_existing: bool) -> dict[str, dict[str, int]]:
    engine = create_engine(
        f"sqlite:///{sqlite_path.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    tables = set(sa_inspect(engine).get_table_names())
    Session = sessionmaker(bind=engine)
    sqlite = Session()

    pb = get_pocketbase_client()
    if not dry_run:
        autenticar_admin_pocketbase(pb)
        asegurar_colecciones(pb)

    stats: dict[str, dict[str, int]] = {}

    try:
        for model in MIGRATION_ORDER:
            tabla = collection_name(model)
            if tabla not in tables:
                logger.warning("Tabla %s no está en SQLite; se omite.", tabla)
                continue

            rows = sqlite.query(model).all()
            stats[tabla] = {"created": 0, "updated": 0, "skipped": 0, "dry-run": 0, "errors": 0}

            logger.info("Migrando %s (%d filas)...", tabla, len(rows))
            for row in rows:
                try:
                    result = upsert_record(
                        pb,
                        model,
                        row,
                        dry_run=dry_run,
                        skip_existing=skip_existing,
                    )
                    stats[tabla][result] = stats[tabla].get(result, 0) + 1
                except Exception as exc:
                    stats[tabla]["errors"] += 1
                    logger.error(
                        "Error en %s id=%s: %s",
                        tabla,
                        getattr(row, "id", "?"),
                        exc,
                    )
    finally:
        sqlite.close()
        engine.dispose()

    return stats


def print_summary(stats: dict[str, dict[str, int]]) -> None:
    print("\n=== Resumen migración SQLite → PocketBase ===")
    for tabla, counts in stats.items():
        print(
            f"  {tabla}: "
            f"creados={counts.get('created', 0)} "
            f"actualizados={counts.get('updated', 0)} "
            f"omitidos={counts.get('skipped', 0)} "
            f"errores={counts.get('errors', 0)}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrar ruteros SQLite a PocketBase")
    parser.add_argument(
        "--sqlite",
        dest="sqlite_path",
        help="Ruta al archivo .db (default: ruteros_local.db o DATABASE_URL)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo cuenta filas; no escribe en PocketBase",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="No actualizar registros que ya existen en PocketBase (solo crear nuevos)",
    )
    args = parser.parse_args()

    sqlite_path = resolve_sqlite_path(args.sqlite_path)
    logger.info("Origen SQLite: %s", sqlite_path)
    logger.info("Destino PocketBase: %s", os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090"))

    stats = migrate(
        sqlite_path,
        dry_run=args.dry_run,
        skip_existing=args.skip_existing,
    )
    print_summary(stats)
    if args.dry_run:
        print("\n(dry-run: no se escribió nada en PocketBase)")


if __name__ == "__main__":
    main()
