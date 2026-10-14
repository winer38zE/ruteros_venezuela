"""Crea colecciones PocketBase equivalentes a las tablas SQLAlchemy."""
from __future__ import annotations

import logging
import os
import secrets
from typing import Any

from pocketbase.errors import ClientResponseError
from pocketbase import PocketBase
from sqlalchemy import Integer, inspect as sa_inspect

from app.core.db import autenticar_admin_pocketbase
from app.core.pb_orm import mapper

logger = logging.getLogger(__name__)

# Colecciones críticas (deben responder en /records antes del bootstrap).
_COLECCIONES_NUCLEO: tuple[str, ...] = (
    "empresas",
    "usuarios",
    "clientes",
    "almacenes",
)

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


def _credenciales_admin() -> tuple[str, str]:
    email = os.getenv("ADMIN_EMAIL", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    return email, password


def _autenticar_admin_api(pb: PocketBase) -> None:
    email, password = _credenciales_admin()
    autenticar_admin_pocketbase(pb, email=email, password=password)


def _mapa_colecciones(pb: PocketBase) -> dict[str, Any]:
    return {c.name: c for c in pb.collections.get_full_list()}


def colecciones_faltantes(pb: PocketBase) -> list[str]:
    existentes = set(_mapa_colecciones(pb).keys())
    return [n for n in nombres_colecciones_requeridas() if n not in existentes]


def confirmar_acceso_registros(pb: PocketBase, nombres: tuple[str, ...] | None = None) -> None:
    """Comprueba que la API de registros responde (no basta con listar metadatos de colección)."""
    objetivos = nombres or _COLECCIONES_NUCLEO
    for nombre in objetivos:
        try:
            pb.collection(nombre).get_list(1, 1)
        except ClientResponseError as exc:
            if exc.status == 404:
                raise RuntimeError(
                    f"La colección '{nombre}' no existe o no es accesible en "
                    f"{getattr(pb, 'base_url', 'PocketBase')} (HTTP 404 en /records)."
                ) from exc
            raise


def verificar_colecciones_completas(pb: PocketBase) -> None:
    faltantes = colecciones_faltantes(pb)
    if faltantes:
        raise RuntimeError(
            "Colecciones PocketBase faltantes antes del bootstrap: "
            + ", ".join(faltantes)
        )
    confirmar_acceso_registros(pb)


def _field_id(field_type: str) -> str:
    base = field_type.replace("_", "")[:3]
    return f"{base}{secrets.token_hex(6)}"[:15]


def _tabla_fk(col) -> str | None:
    fks = getattr(col, "foreign_keys", None)
    if not fks:
        return None
    fk = next(iter(fks))
    return fk.column.table.name


def _field_for_column(
    col,
    ids_por_tabla: dict[str, str],
    *,
    usar_relaciones: bool,
) -> dict[str, Any]:
    tabla_rel = _tabla_fk(col)
    if usar_relaciones and tabla_rel and tabla_rel in ids_por_tabla:
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


def _fields_for_model(
    model: type,
    ids_por_tabla: dict[str, str],
    *,
    usar_relaciones: bool,
) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for col in sa_inspect(model).columns:
        if col.key == "id":
            continue
        fields.append(_field_for_column(col, ids_por_tabla, usar_relaciones=usar_relaciones))
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


def _crear_coleccion(
    pb: PocketBase,
    model: type,
    ids_por_tabla: dict[str, str],
    *,
    usar_relaciones: bool,
) -> None:
    nombre = mapper.collection_name(model)
    body = {
        "name": nombre,
        "type": "base",
        "fields": _fields_for_model(model, ids_por_tabla, usar_relaciones=usar_relaciones),
        "listRule": "",
        "viewRule": "",
        "createRule": "",
        "updateRule": "",
        "deleteRule": "",
    }
    created = pb.collections.create(body)
    coll_id = getattr(created, "id", None)
    if coll_id:
        ids_por_tabla[nombre] = str(coll_id)
    logger.info(
        "Colección PocketBase creada: %s (%d campos, relaciones=%s)",
        nombre,
        len(body["fields"]),
        usar_relaciones,
    )


def asegurar_colecciones(pb: PocketBase) -> None:
    _autenticar_admin_api(pb)
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
        try:
            _crear_coleccion(pb, model, ids_por_tabla, usar_relaciones=True)
        except ClientResponseError as exc:
            logger.warning(
                "Reintento sin relaciones para '%s' (status=%s).",
                nombre,
                getattr(exc, "status", "?"),
            )
            try:
                _crear_coleccion(pb, model, ids_por_tabla, usar_relaciones=False)
            except ClientResponseError as exc2:
                logger.error(
                    "No se pudo crear la colección %s: status=%s data=%s",
                    nombre,
                    getattr(exc2, "status", "?"),
                    getattr(exc2, "data", exc2),
                )
                raise RuntimeError(f"Fallo al crear colección '{nombre}' en PocketBase") from exc2
        existentes.add(nombre)
        creadas += 1

    verificar_colecciones_completas(pb)

    if creadas:
        logger.info("Esquema PocketBase: %d colección(es) nueva(s).", creadas)
    else:
        logger.info("Esquema PocketBase: todas las colecciones ya existían.")


def preparar_esquema_pocketbase(pb: PocketBase) -> None:
    """Auth admin + crear colecciones + verificar acceso a registros (obligatorio antes del bootstrap)."""
    asegurar_colecciones(pb)
