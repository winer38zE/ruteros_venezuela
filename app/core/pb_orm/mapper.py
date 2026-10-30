"""Mapeo modelos SQLAlchemy ↔ colecciones PocketBase."""
from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Integer, JSON, Numeric, Text, inspect as sa_inspect

from app.core.pb_orm.ids import es_id_pocketbase, id_pocketbase_desde_cualquiera
from app.models import core as models

# (modelo padre, atributo relación) → (tipo, modelo hijo/padre, columna FK en hijo o en padre)
EAGER_RELATIONS: dict[tuple[type, str], tuple[str, type, str]] = {
    (models.Venta, "cliente"): ("many-to-one", models.Cliente, "cliente_id"),
    (models.Venta, "detalles"): ("one-to-many", models.DetalleVenta, "venta_id"),
    (models.Venta, "cobros"): ("one-to-many", models.Cobro, "venta_id"),
    (models.Venta, "cuotas"): ("one-to-many", models.CuotaAmortizacion, "venta_id"),
    (models.AsientoContable, "lineas"): ("one-to-many", models.LineaAsiento, "asiento_id"),
}


def all_models() -> list[type]:
    """Modelos ORM registrados (no usar inspect() sobre la clase Base)."""
    return [
        m.class_
        for m in models.Base.registry.mappers
        if getattr(m, "class_", None) is not None
    ]


def collection_name(model: type) -> str:
    return model.__tablename__


def column_names(model: type) -> list[str]:
    return [c.key for c in sa_inspect(model).columns]


def record_payload(rec: Any) -> dict[str, Any]:
    skip = {"expand", "collection_id", "collection_name", "created", "updated"}
    return {
        k: v
        for k, v in rec.__dict__.items()
        if k not in skip and not k.startswith("_")
    }


def record_to_model(model: type, data: dict[str, Any]) -> Any:
    inst = model()
    cols = {c.key: c for c in sa_inspect(model).columns}
    for key, col in cols.items():
        raw = data.get(key)
        if raw is None:
            setattr(inst, key, None)
            continue
        setattr(inst, key, _coerce_python(col, raw))
    return inst


def model_to_record(obj: Any) -> dict[str, Any]:
    model = type(obj)
    out: dict[str, Any] = {}
    for col in sa_inspect(model).columns:
        key = col.key
        val = getattr(obj, key, None)
        if val is None:
            continue
        out[key] = _coerce_storage(val)
    return out


def record_id(obj: Any) -> str:
    rid = getattr(obj, "id", None)
    if rid is None:
        raise ValueError(f"Registro sin id: {type(obj).__name__}")
    return str(rid)


def _coerce_storage(val: Any) -> Any:
    if isinstance(val, uuid.UUID):
        s = str(val)
        return s if es_id_pocketbase(s) else id_pocketbase_desde_cualquiera(val)
    if isinstance(val, str) and len(val) > 15 and not es_id_pocketbase(val):
        return id_pocketbase_desde_cualquiera(val)
    if isinstance(val, enum.Enum):
        return val.value
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    return val


def _coerce_python(col, raw: Any) -> Any:
    if raw is None or raw == "":
        return None
    # GUID (TypeDecorator) no implementa python_type y lanza NotImplementedError.
    # Tiene que quedar dentro del try: si no, ninguna lectura de ventas o cobros arranca.
    try:
        py_type = col.type.python_type
    except Exception:
        py_type = str
    if py_type is uuid.UUID:
        s = str(raw)
        if es_id_pocketbase(s):
            return s
        try:
            return uuid.UUID(s)
        except ValueError:
            return s
    if isinstance(col.type, Numeric):
        return Decimal(str(raw))
    if py_type is bool:
        if isinstance(raw, bool):
            return raw
        return str(raw).lower() in ("1", "true", "yes")
    if py_type is int:
        return int(raw)
    if py_type is float:
        return float(raw)
    if py_type is datetime:
        if isinstance(raw, datetime):
            return raw
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
    if py_type is date:
        if isinstance(raw, date):
            return raw
        return date.fromisoformat(str(raw)[:10])
    if isinstance(py_type, type) and issubclass(py_type, enum.Enum):
        texto = str(raw)
        try:
            return py_type(texto)
        except ValueError:
            for member in py_type:
                if member.value == texto or member.name == texto:
                    return member
            return texto
    return raw


def pb_field_type(col) -> str:
    if isinstance(col.type, Boolean):
        return "bool"
    if isinstance(col.type, (Integer, Numeric)):
        return "number"
    if isinstance(col.type, (DateTime, Date)):
        return "date"
    if isinstance(col.type, JSON):
        return "json"
    if isinstance(col.type, Text):
        return "editor"
    return "text"
