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


def nombres_colecciones_requeridas() -> list[str]:
    return [mapper.collection_name(m) for m in mapper.all_models()]


def _mapa_colecciones(pb: PocketBase) -> dict[str, Any]:
    return {c.name: c for c in pb.collections.get_full_list()}


def colecciones_faltantes(pb: PocketBase) -> list[str]:
    existentes = set(_mapa_colecciones(pb).keys())
    return [n for n in nombres_colecciones_requeridas() if n not in existentes]


def verificar_colecciones_completas(pb: PocketBase) -> None:
    """Fallo explícito si falta alguna tabla Ruteros (evita bootstrap sobre PB vacío)."""
    faltantes = colecciones_faltantes(pb)
    if faltantes:
        raise RuntimeError(
            "Colecciones PocketBase faltantes antes del bootstrap: "
            + ", ".join(faltantes)
        )


def _field_id(field_type: str) -> str:
    """PocketBase v0.23+ exige id único por campo en el JSON de la colección."""
    return f"{field_type}{secrets.token_hex(7)}"[:15]


def _tabla_fk(col) -> str | None:
    fks = getattr(col, "foreign_keys", None)
    if not fks:
        return None
    fk = next(iter(fks))
    return fk.column.table.name


def _field_for_column(col, ids_por_tabla: dict[str, str]) -> dict[str, Any]:
    tabla_rel = _tabla_fk(col)
    if tabla_rel and tabla_rel in ids_por_tabla:
        return {
            "id": _field_id("rel"),
            "name": col.key,
            "type": "relation",
            "required": False,
            "presentable": False,
            "collectionId": ids_por_tabla[tabla_rel],
            "cascadeDelete": False,
            "minSelect": 0,
            "maxSelect": 1,
        }

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


def _fields_for_model(model: type, ids_por_tabla: dict[str, str]) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for col in sa_inspect(model).columns:
        if col.key == "id":
            continue
        fields.append(_field_for_column(col, ids_por_tabla))
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


def _ids_por_tabla(pb: PocketBase) -> dict[str, str]:
    return {c.name: c.id for c in pb.collections.get_full_list()}


def asegurar_colecciones(pb: PocketBase) -> None:
    try:
        ids_por_tabla = _ids_por_tabla(pb)
        existentes = set(ids_por_tabla.keys())
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
            "fields": _fields_for_model(model, ids_por_tabla),
            "listRule": "",
            "viewRule": "",
            "createRule": "",
            "updateRule": "",
            "deleteRule": "",
        }
        try:
            created = pb.collections.create(body)
            coll_id = getattr(created, "id", None) or created.__dict__.get("id")
            if coll_id:
                ids_por_tabla[nombre] = str(coll_id)
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

    verificar_colecciones_completas(pb)

    if creadas:
        logger.info("Esquema PocketBase: %d colección(es) nueva(s).", creadas)
    else:
        logger.info("Esquema PocketBase: todas las colecciones ya existían.")
