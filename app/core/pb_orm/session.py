"""Sesión PocketBase compatible con el patrón Session de SQLAlchemy."""
from __future__ import annotations

import logging
from copy import deepcopy
from typing import Any

from pocketbase.errors import ClientResponseError
from sqlalchemy.exc import IntegrityError

from app.core.pb_orm import mapper
from app.core.pb_orm.ids import (
    es_id_pocketbase,
    id_pocketbase_desde_cualquiera,
    id_para_payload_creacion,
    nuevo_id_pocketbase,
)
from app.core.pb_orm.query import PbQuery

logger = logging.getLogger(__name__)


def _pb_client():
    from app.core.db import get_pocketbase_client

    return get_pocketbase_client()


class PbSession:
    def __init__(self, pb=None) -> None:
        self.pb = pb or _pb_client()
        self._new: set[str] = set()
        self._registry: dict[str, Any] = {}
        self._snapshots: dict[str, dict[str, Any]] = {}

    def query(self, *entities: Any) -> PbQuery:
        if not entities:
            raise ValueError("query() requiere un modelo")
        first = entities[0]
        if hasattr(first, "__tablename__"):
            return PbQuery(self, first)
        model = _infer_model_from_expression(first)
        q = PbQuery(self, model)
        q._scalar_expr = first
        return q

    def add(self, obj: Any) -> None:
        raw_id = getattr(obj, "id", None)
        if raw_id is None:
            obj.id = nuevo_id_pocketbase()
        elif not es_id_pocketbase(raw_id):
            obj.id = id_pocketbase_desde_cualquiera(raw_id)
        rid = mapper.record_id(obj)
        self._registry[rid] = obj
        self._new.add(rid)
        self._snapshots[rid] = mapper.model_to_record(obj)

    def flush(self) -> None:
        for rid in list(self._new):
            obj = self._registry[rid]
            self._create_record(obj)
        for rid, obj in self._registry.items():
            if rid in self._new:
                continue
            cur = mapper.model_to_record(obj)
            if cur != self._snapshots.get(rid):
                self._update_record(obj)

    def commit(self) -> None:
        try:
            self.flush()
            self._new.clear()
            for rid, obj in self._registry.items():
                self._snapshots[rid] = mapper.model_to_record(obj)
        except ClientResponseError as exc:
            raise _as_integrity(exc) from exc

    def rollback(self) -> None:
        self._new.clear()

    def refresh(self, obj: Any, attribute_names: list[str] | None = None) -> None:
        name = mapper.collection_name(type(obj))
        rid = mapper.record_id(obj)
        rec = self.pb.collection(name).get_one(rid)
        data = mapper.record_payload(rec)
        fresh = mapper.record_to_model(type(obj), data)
        for col in mapper.column_names(type(obj)):
            setattr(obj, col, getattr(fresh, col))
        if attribute_names:
            self._load_eager(obj, set(attribute_names))

    def close(self) -> None:
        self._registry.clear()
        self._snapshots.clear()
        self._new.clear()

    def begin_nested(self) -> _NestedTransaction:
        return _NestedTransaction(self)

    def _checkpoint(self) -> dict[str, Any]:
        return {
            "new": set(self._new),
            "registry": dict(self._registry),
            "snapshots": deepcopy(self._snapshots),
        }

    def _restore_checkpoint(self, ck: dict[str, Any]) -> None:
        self._new = ck["new"]
        self._registry = ck["registry"]
        self._snapshots = ck["snapshots"]

    def _register_loaded(self, obj: Any) -> None:
        rid = mapper.record_id(obj)
        self._registry[rid] = obj
        self._snapshots[rid] = mapper.model_to_record(obj)

    def _mark_dirty(self, obj: Any) -> None:
        rid = mapper.record_id(obj)
        self._registry[rid] = obj

    def _load_eager(self, obj: Any, names: set[str]) -> None:
        model = type(obj)
        for attr in names:
            spec = mapper.EAGER_RELATIONS.get((model, attr))
            if not spec:
                continue
            kind, rel_model, fk_field = spec
            if kind == "many-to-one":
                fk = getattr(obj, fk_field, None)
                if not fk:
                    continue
                rel = (
                    PbQuery(self, rel_model)
                    .filter(getattr(rel_model, "id") == fk)
                    .first()
                )
                setattr(obj, attr, rel)
            else:
                fk_val = getattr(obj, "id", None)
                children = (
                    PbQuery(self, rel_model)
                    .filter(getattr(rel_model, fk_field) == fk_val)
                    .all()
                )
                setattr(obj, attr, children)

    def _create_record(self, obj: Any) -> None:
        name = mapper.collection_name(type(obj))
        body = mapper.model_to_record(obj)
        rid = mapper.record_id(obj)
        body.pop("id", None)
        id_envio = id_para_payload_creacion(rid)
        if id_envio is not None:
            body["id"] = id_envio
            obj.id = id_envio
        try:
            created = self.pb.collection(name).create(body)
        except ClientResponseError as exc:
            if exc.status == 404:
                raise RuntimeError(
                    f"La colección '{name}' no existe en PocketBase. "
                    "El arranque debe crear el esquema antes del bootstrap."
                ) from exc
            raise _as_integrity(exc) from exc
        data = mapper.record_payload(created)
        nuevo_rid = str(data.get("id") or obj.id)
        if nuevo_rid != rid:
            self._registry.pop(rid, None)
            self._snapshots.pop(rid, None)
            self._new.discard(rid)
            obj.id = nuevo_rid
            self._registry[nuevo_rid] = obj
        self._snapshots[nuevo_rid] = mapper.model_to_record(obj)
        self._new.discard(nuevo_rid)

    def _update_record(self, obj: Any) -> None:
        name = mapper.collection_name(type(obj))
        body = mapper.model_to_record(obj)
        rid = mapper.record_id(obj)
        self.pb.collection(name).update(rid, body)
        self._snapshots[rid] = mapper.model_to_record(obj)


class _NestedTransaction:
    def __init__(self, session: PbSession) -> None:
        self.session = session
        self._ck: dict[str, Any] | None = None

    def __enter__(self) -> _NestedTransaction:
        self._ck = self.session._checkpoint()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        if exc_type is not None:
            if self._ck:
                self.session._restore_checkpoint(self._ck)
            return False
        try:
            self.session.flush()
        except IntegrityError:
            if self._ck:
                self.session._restore_checkpoint(self._ck)
            raise
        return False


def _as_integrity(exc: ClientResponseError) -> IntegrityError:
    msg = str(exc.data) if exc.data else str(exc)
    return IntegrityError(msg, params=None, orig=exc)


def _infer_model_from_expression(expr: Any) -> type:
    stack = [expr]
    while stack:
        node = stack.pop()
        if hasattr(node, "clauses"):
            stack.extend(reversed(list(node.clauses)))
        if hasattr(node, "element"):
            stack.append(node.element)
        prop = getattr(node, "property", None)
        if prop is not None and hasattr(prop, "parent"):
            return prop.parent.class_
    raise ValueError("No se pudo inferir el modelo de la expresión")


def SessionLocal() -> PbSession:
    return PbSession(_pb_client())
