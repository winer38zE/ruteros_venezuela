"""Crea colecciones PocketBase equivalentes a las tablas SQLAlchemy."""
from __future__ import annotations

import logging
from typing import Any

from pocketbase.errors import ClientResponseError
from pocketbase import PocketBase
from sqlalchemy import inspect as sa_inspect

from app.core.pb_orm import mapper
logger = logging.getLogger(__name__)


def _fields_for_model(model: type) -> list[dict[str, Any]]:
    fields: list[dict[str, Any]] = []
    for col in sa_inspect(model).columns:
        if col.key == "id":
            continue
        fields.append(
            {
                "name": col.key,
                "type": mapper.pb_field_type(col),
                "required": False,
                "presentable": False,
                "unique": False,
            }
        )
    return fields


def asegurar_colecciones(pb: PocketBase) -> None:
    existentes = {c.name for c in pb.collections.get_full_list()}
    for model in mapper.all_models():
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
            logger.info("Colección PocketBase creada: %s", nombre)
        except ClientResponseError as exc:
            logger.warning("No se pudo crear colección %s: %s", nombre, exc)
