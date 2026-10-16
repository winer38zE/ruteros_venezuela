"""Compila filtros SQLAlchemy usados en la app a sintaxis PocketBase."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, or_
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList, Grouping
from sqlalchemy.sql.functions import Function


def compile_filters(model: type, criteria: tuple[Any, ...]) -> str:
    parts = [_compile_one(model, c) for c in criteria if c is not None]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return " && ".join(f"({p})" if " || " in p else p for p in parts)


def _compile_one(model: type, crit: Any) -> str:
    if crit is True:
        return ""
    if isinstance(crit, BooleanClauseList):
        op = " && " if crit.operator is and_ else " || "
        inner = [_compile_one(model, c) for c in crit.clauses]
        inner = [i for i in inner if i]
        if not inner:
            return ""
        return op.join(f"({i})" for i in inner)
    if isinstance(crit, Grouping):
        inner = _compile_one(model, crit.element)
        return f"({inner})" if inner else ""
    if isinstance(crit, BinaryExpression):
        return _compile_binary(crit)
    return ""


def _field_name(expr_left: Any) -> str:
    if isinstance(expr_left, Function) and getattr(expr_left, "name", "") == "lower":
        inner = expr_left.clauses.clauses[0]
        base = getattr(inner, "key", None) or str(inner)
        return f"{base}:lower"
    return getattr(expr_left, "key", None) or str(expr_left)


def _compile_binary(expr: BinaryExpression) -> str:
    key = _field_name(expr.left)
    op = expr.operator
    right = expr.right
    val = getattr(right, "value", right)
    if hasattr(val, "effective_value"):
        val = val.effective_value

    name = op.__name__

    if name == "eq":
        return f"{key} = {_fmt(val)}"
    if name == "ne":
        return f"{key} != {_fmt(val)}"
    if name == "gt":
        return f"{key} > {_fmt(val)}"
    if name == "ge":
        return f"{key} >= {_fmt(val)}"
    if name == "lt":
        return f"{key} < {_fmt(val)}"
    if name == "le":
        return f"{key} <= {_fmt(val)}"
    if name in ("in_op", "in"):
        items = list(val)
        if not items:
            return "id = ''"
        return " || ".join(f"{key} = {_fmt(v)}" for v in items)
    if name == "is_":
        if val is True or val is not False and str(val).lower() == "true":
            return f"{key} = true"
        if val is False or str(val).lower() == "false":
            return f"{key} = false"
        return f"{key} = null"
    if name == "is_not":
        if val is True:
            return f"{key} != true"
        if val is False:
            return f"{key} != false"
        return f"{key} != null"
    if name in ("like_op", "ilike_op", "contains"):
        s = str(val).replace("%", "")
        return f"{key} ~ {_fmt(f'%{s}%')}"
    return ""


def _fmt(val: Any) -> str:
    if val is None:
        return "null"
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float, Decimal)):
        return str(val)
    if isinstance(val, uuid.UUID):
        return f"'{val}'"
    if isinstance(val, enum.Enum):
        return f"'{val.value}'"
    if isinstance(val, (datetime, date)):
        return f"'{val.isoformat()}'"
    s = str(val).replace("'", "\\'")
    return f"'{s}'"
