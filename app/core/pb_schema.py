"""Crea y sincroniza colecciones PocketBase equivalentes a las tablas SQLAlchemy."""
from __future__ import annotations

import logging
import os
import secrets
from typing import Any

import app.models.core  # noqa: F401 — registra todos los mappers en Base.registry
from pocketbase.errors import ClientResponseError
from pocketbase import PocketBase
from sqlalchemy import Integer, inspect as sa_inspect

from app.core.db import autenticar_admin_pocketbase
from app.core.pb_collections_cache import (
    ids_colecciones_por_nombre,
    invalidar_cache_colecciones,
    mapa_colecciones_por_nombre,
)
from app.core.pb_orm import mapper
from app.core.usuario_password_hash import CAMPO_HASH_USUARIO
from app.models.core import Usuario

logger = logging.getLogger(__name__)

_MIN_MAX_PASSWORD_HASH = 101

_COLECCIONES_NUCLEO: tuple[str, ...] = (
    "empresas",
    "usuarios",
    "clientes",
    "almacenes",
)

_ORDEN_COLECCIONES: tuple[str, ...] = (
    "paises",
    "empresas",
    "cuentas_bancarias",
    "configuracion_fiscal",
    "configuracion_nomina",
    "almacenes",
    "usuarios",
    "cuentas_bancarias_empleados",
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
    "pagos_nomina",
    "visitas_diarias",
    "notas_seguimiento_cobranza",
    "acuerdos_pago",
    "eventos_buro_credito",
)

_SNAKE_A_API: dict[str, str] = {
    "auto_generate_pattern": "autogeneratePattern",
    "primary_key": "primaryKey",
    "max_size": "maxSize",
    "only_int": "onlyInt",
    "collection_id": "collectionId",
    "cascade_delete": "cascadeDelete",
    "min_select": "minSelect",
    "max_select": "maxSelect",
}


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
    return mapa_colecciones_por_nombre(pb)


def colecciones_faltantes(pb: PocketBase) -> list[str]:
    existentes = set(_mapa_colecciones(pb).keys())
    return [n for n in nombres_colecciones_requeridas() if n not in existentes]


def confirmar_acceso_registros(pb: PocketBase, nombres: tuple[str, ...] | None = None) -> None:
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
        if length:
            entry["max"] = int(length)
        elif col.key == "password_hash":
            entry["max"] = 255
        else:
            entry["max"] = 0
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
    return ids_colecciones_por_nombre(pb)


def _campo_api_a_patch(field: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in field.items():
        if val is None:
            continue
        api_key = _SNAKE_A_API.get(key, key)
        out[api_key] = val
    return out


def _nombres_campos_coleccion(coll: Any) -> set[str]:
    nombres: set[str] = set()
    for f in coll.fields or []:
        nombre = f.get("name")
        if nombre and nombre != "id":
            nombres.add(nombre)
    return nombres


def _sincronizar_campos_coleccion(
    pb: PocketBase,
    model: type,
    coll: Any,
    ids_por_tabla: dict[str, str],
) -> int:
    """Añade campos faltantes a una colección ya existente (p. ej. empresas solo con nombre)."""
    deseados = _fields_for_model(model, ids_por_tabla, usar_relaciones=True)
    existentes = _nombres_campos_coleccion(coll)
    nuevos = [f for f in deseados if f["name"] not in existentes]
    if not nuevos:
        return 0
    try:
        payload = [_campo_api_a_patch(f) for f in coll.fields] + nuevos
        pb.collections.update(
            coll.id,
            {"fields": payload},
        )
        invalidar_cache_colecciones(pb)
        logger.info(
            "Colección '%s' ampliada con %d campo(s): %s",
            coll.name,
            len(nuevos),
            ", ".join(f["name"] for f in nuevos),
        )
        return len(nuevos)
    except ClientResponseError as exc:
        logger.warning(
            "Sync con relaciones falló en '%s' (%s); reintento campos texto.",
            coll.name,
            getattr(exc, "status", "?"),
        )
        deseados_txt = _fields_for_model(model, ids_por_tabla, usar_relaciones=False)
        nuevos_txt = [f for f in deseados_txt if f["name"] not in existentes]
        if not nuevos_txt:
            return 0
        payload = [_campo_api_a_patch(f) for f in coll.fields] + nuevos_txt
        pb.collections.update(coll.id, {"fields": payload})
        invalidar_cache_colecciones(pb)
        logger.info(
            "Colección '%s' ampliada (texto) con %d campo(s).",
            coll.name,
            len(nuevos_txt),
        )
        return len(nuevos_txt)


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
    invalidar_cache_colecciones(pb)
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
        mapa = _mapa_colecciones(pb)
    except ClientResponseError as exc:
        logger.error("No se pudo listar colecciones PocketBase: %s", exc)
        raise

    if "users" in mapa and "usuarios" not in mapa:
        logger.warning(
            "Existe la colección auth 'users' de PocketBase, pero la app usa 'usuarios' "
            "(colección base Ruteros). Se creará 'usuarios' con el esquema completo."
        )

    creadas = 0
    ampliadas = 0
    for model in _modelos_ordenados():
        nombre = mapper.collection_name(model)
        ids_por_tabla = _ids_por_tabla(pb)

        if nombre in mapa:
            ampliadas += _sincronizar_campos_coleccion(pb, model, mapa[nombre], ids_por_tabla)
            mapa = _mapa_colecciones(pb)
            ids_por_tabla = _ids_por_tabla(pb)
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
        creadas += 1
        mapa = _mapa_colecciones(pb)
        ids_por_tabla = _ids_por_tabla(pb)

    verificar_colecciones_completas(pb)

    asegurar_campo_password_hash_usuarios(pb)

    logger.info(
        "Esquema PocketBase: %d colección(es) nueva(s), %d colección(es) ampliada(s).",
        creadas,
        ampliadas,
    )


def asegurar_campo_password_hash_usuarios(pb: PocketBase) -> None:
    """Campo password_hash presente, editable y con max > 100."""
    mapa = mapa_colecciones_por_nombre(pb)
    coll = mapa.get("usuarios")
    if coll is None:
        logger.warning("Colección 'usuarios' ausente; no se validó password_hash.")
        return

    ids_por_tabla = ids_colecciones_por_nombre(pb)
    nombres = _nombres_campos_coleccion(coll)
    if CAMPO_HASH_USUARIO not in nombres:
        _sincronizar_campos_coleccion(pb, Usuario, coll, ids_por_tabla)
        invalidar_cache_colecciones(pb)
        mapa = mapa_colecciones_por_nombre(pb)
        coll = mapa.get("usuarios")
        if coll is None:
            return
        nombres = _nombres_campos_coleccion(coll)

    if CAMPO_HASH_USUARIO not in nombres:
        logger.error(
            "Esquema usuarios: falta el campo %r; PocketBase ignorará el hash en PATCH.",
            CAMPO_HASH_USUARIO,
        )
        return

    fields_raw = list(coll.fields or [])
    nuevos_fields: list[dict[str, Any]] = []
    cambio = False
    for field in fields_raw:
        f = dict(field)
        if f.get("name") != CAMPO_HASH_USUARIO:
            nuevos_fields.append(f)
            continue
        if f.get("type") != "text":
            logger.error(
                "Campo %r en usuarios tiene type=%r; se esperaba 'text'.",
                CAMPO_HASH_USUARIO,
                f.get("type"),
            )
        max_val = int(f.get("max") or 0)
        if max_val != 0 and max_val < _MIN_MAX_PASSWORD_HASH:
            f["max"] = 255
            cambio = True
            logger.info(
                "Ampliando max de %r de %d a 255 en usuarios.",
                CAMPO_HASH_USUARIO,
                max_val,
            )
        elif max_val == 0:
            f["max"] = 255
            cambio = True
        if f.get("hidden") is True:
            f["hidden"] = False
            cambio = True
        nuevos_fields.append(f)

    if not cambio:
        logger.debug(
            "Campo %r en usuarios OK (type=text, max>= %d, no oculto).",
            CAMPO_HASH_USUARIO,
            _MIN_MAX_PASSWORD_HASH,
        )
        return

    payload = [_campo_api_a_patch(f) for f in nuevos_fields]
    pb.collections.update(coll.id, {"fields": payload})
    invalidar_cache_colecciones(pb)
    logger.info("Esquema usuarios: campo %r actualizado (max/hidden).", CAMPO_HASH_USUARIO)


def preparar_esquema_pocketbase(pb: PocketBase) -> None:
    asegurar_colecciones(pb)
