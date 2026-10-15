"""Query estilo SQLAlchemy sobre colecciones PocketBase."""
from __future__ import annotations

import uuid
from typing import Any

from pocketbase.errors import ClientResponseError
from sqlalchemy import func
from sqlalchemy.orm.interfaces import LoaderOption

from app.core.db import reautenticar_admin_pocketbase
from app.core.pb_orm import filter_compiler, mapper


class PbQuery:
    def __init__(self, session: Any, model: type) -> None:
        self._session = session
        self._model = model
        self._criteria: list[Any] = []
        self._order: list[tuple[str, bool]] = []
        self._limit: int | None = None
        self._offset: int | None = None
        self._eager: set[str] = set()
        self._scalar_expr: Any | None = None

    def filter(self, *criteria: Any) -> PbQuery:
        self._criteria.extend(criteria)
        return self

    def filter_by(self, **kwargs: Any) -> PbQuery:
        for k, v in kwargs.items():
            col = getattr(self._model, k)
            self._criteria.append(col == v)
        return self

    def order_by(self, *clauses: Any) -> PbQuery:
        for clause in clauses:
            desc = False
            key = clause
            if hasattr(clause, "modifier"):
                key = clause.element
                desc = str(getattr(clause, "modifier", "")).endswith("DESC")
            elif hasattr(clause, "element") and not hasattr(clause, "key"):
                key = clause.element
                desc = True
            name = getattr(key, "key", str(key))
            self._order.append((name, desc))
        return self

    def limit(self, n: int) -> PbQuery:
        self._limit = n
        return self

    def offset(self, n: int) -> PbQuery:
        self._offset = n
        return self

    def options(self, *opts: LoaderOption) -> PbQuery:
        for opt in opts:
            path = getattr(opt, "path", None)
            if path is not None and len(path):
                self._eager.add(path[-1].key)
            elif hasattr(opt, "attrs"):
                for a in opt.attrs:
                    self._eager.add(getattr(a, "key", str(a)))
        return self

    def with_entities(self, *entities: Any) -> PbQuery:
        return self

    def update(self, values: dict[str, Any]) -> int:
        rows = self.all()
        count = 0
        for row in rows:
            for k, v in values.items():
                setattr(row, k, v)
            self._session._mark_dirty(row)
            count += 1
        self._session.flush()
        return count

    def count(self) -> int:
        return len(self._fetch_all())

    def first(self) -> Any | None:
        old_limit = self._limit
        self._limit = 1
        rows = self._fetch_all()
        self._limit = old_limit
        return rows[0] if rows else None

    def all(self) -> list[Any]:
        return self._fetch_all()

    def scalar(self) -> Any:
        if self._scalar_expr is not None:
            return self._eval_scalar()
        row = self.first()
        return row

    def _fetch_all(self) -> list[Any]:
        pb = self._session.pb
        name = mapper.collection_name(self._model)
        filt = filter_compiler.compile_filters(self._model, tuple(self._criteria))
        sort_parts = []
        for field, desc in self._order:
            sort_parts.append(f"{'-' if desc else '+'}{field}")
        sort = ",".join(sort_parts) if sort_parts else "+id"

        page = 1
        per_page = 200
        items: list[Any] = []
        reintentar_auth = True
        while True:
            try:
                params: dict[str, str] = {"sort": sort}
                if filt:
                    params["filter"] = filt
                batch = pb.collection(name).get_list(page, per_page, query_params=params)
            except ClientResponseError as exc:
                if exc.status == 404:
                    raise ClientResponseError(
                        f"La colección '{name}' no existe en PocketBase.",
                        url=exc.url,
                        status=exc.status,
                        data=exc.data,
                    ) from exc
                if reintentar_auth and exc.status in (401, 403):
                    reintentar_auth = False
                    if reautenticar_admin_pocketbase(pb):
                        continue
                raise
            for rec in batch.items:
                data = mapper.record_payload(rec)
                obj = mapper.record_to_model(self._model, data)
                self._session._register_loaded(obj)
                items.append(obj)
            if len(batch.items) < per_page:
                break
            page += 1
            if self._limit and len(items) >= self._limit:
                break

        if self._offset:
            items = items[self._offset :]
        if self._limit is not None:
            items = items[: self._limit]

        if self._eager:
            for obj in items:
                self._session._load_eager(obj, self._eager)
        return items

    def _eval_scalar(self) -> Any:
        # func.max(func.coalesce(Cliente.orden_ruta, Cliente.orden_secuencial))
        rows = self.all()
        if not rows:
            return None
        expr = self._scalar_expr
        if hasattr(expr, "clauses"):
            inner = expr.clauses[0]
            if hasattr(inner, "clauses") and len(inner.clauses) == 2:
                a, b = inner.clauses
                key_a = getattr(a, "key", None)
                key_b = getattr(b, "key", None)
                vals = []
                for row in rows:
                    va = getattr(row, key_a, None) if key_a else None
                    vb = getattr(row, key_b, None) if key_b else None
                    vals.append(va if va is not None else vb)
                return max((v for v in vals if v is not None), default=None)
        return None

    def __getitem__(self, item: Any) -> PbQuery:
        if isinstance(item, slice):
            return self
        return self


def query_scalar(session: PbQuery, expression: Any) -> PbQuery:
    session._scalar_expr = expression
    return session
