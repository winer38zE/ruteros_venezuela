"""Crea colecciones PocketBase equivalentes a las tablas SQLAlchemy."""
from __future__ import annotations

import logging
import secrets
from typing import Any

from pocketbase.errors import ClientResponseError
from pocketbase import PocketBase
from sqlalchemy import Integer, inspect as sa_inspect

from app.core.pb_orm import mapper

logger = logging.getLogger(__name__)

# Mismo orden que scripts/migrate_sqlite_to_pocketbase.py (FK lógicas al insertar datos).
_ORDEN_COLECCIONES: tuple[str, ...] = (
    "empresas",
    "cuentas_bancarias",
    "configuracion_fiscal",
    "configuracion_nomina",
    "almacenes",
    "usuarios",
    "proveedores",
    "clientes",
    "productos",
    "precios_producto",
    "lotes_inventario",
    "tasas_cambio",
    "ventas",
    "detalles_venta",
    "cuotas_amortizacion",
    "cobros",
    "asientos_contables",
    "lineas_asiento",
    "movimientos_inventario",
    "movimientos_financieros",
    "visitas_diarias",
    "notas_seguimiento_cobranza",
    "acuerdos_pago",
    "eventos_buro_credito",
)


def _field_id(field_type: str) -> str:
    """PocketBase v0.23+ exige id único por campo en el JSON de la colección."""
    return f"{field_type}{secrets.token_hex(7)}"[:15]


def _field_for_column(col) -> dict[str, Any]:
    ftype = mapper.pb_field_type(col)
    entry: dict[str, Any] = {
        "id": _field_id(ftype),
        "name": col.key,
        "type": ftype,
        "required": False,
        "presentable": False,
    }
    if ftype == "text":
        length = getattr(col.type, "length", None)
        entry["min"] = 0
        entry["max"] = int(length) if length else 0
    elif ftype == "editor":
        entry["maxSize"] = 5_000_000
    elif ftype == "number":
        entry["onlyInt"] = isinstance(col.type, Integer)
    return entry


def _fields_for_model(model: type) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for col in sa_inspect(model).columns:
        if col.key == "id":
            continue
        fields.append(_field_for_column(col))
    return fields


def _modelos_ordenados() -> list[type]:
    by_table = {mapper.collection_name(m): m for m in mapper.all_models()}
    ordered: list[type] = []
    seen: set[str] = set()
    for name in _ORDEN_COLECCIONES:
        if name in by_table:
            ordered.append(by_table[name])
            seen.add(name)
    for name, model in sorted(by_table.items()):
        if name not in seen:
            ordered.append(model)
    return ordered


def asegurar_colecciones(pb: PocketBase) -> None:
    try:
        existentes = {c.name for c in pb.collections.get_full_list()}
    except ClientResponseError as exc:
        logger.error("No se pudo listar colecciones PocketBase: %s", exc)
        raise

    creadas = 0
    for model in _modelos_ordenados():
        nombre = mapper.collection_name(model)
        if nombre in existentes:
            continue
        body = {
            "name": nombre,
            "type": "base",
            "fields": _fields_for_model(model),
            "listRule": "",
            "viewRule": "",
            "createRule": "",
            "updateRule": "",
            "deleteRule": "",
        }
        try:
            pb.collections.create(body)
            existentes.add(nombre)
            creadas += 1
            logger.info("Colección PocketBase creada: %s (%d campos)", nombre, len(body["fields"]))
        except ClientResponseError as exc:
            logger.error(
                "No se pudo crear la colección %s: status=%s data=%s",
                nombre,
                getattr(exc, "status", "?"),
                getattr(exc, "data", exc),
            )
            raise RuntimeError(f"Fallo al crear colección '{nombre}' en PocketBase") from exc

    faltantes = [
        mapper.collection_name(m)
        for m in mapper.all_models()
        if mapper.collection_name(m) not in existentes
    ]
    if faltantes:
        raise RuntimeError(f"Colecciones Ruteros aún faltantes en PocketBase: {faltantes}")

    if creadas:
        logger.info("Esquema PocketBase: %d colección(es) nueva(s).", creadas)
    else:
        logger.info("Esquema PocketBase: todas las colecciones ya existían.")
