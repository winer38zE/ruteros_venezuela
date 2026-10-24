"""Consultas de productos: filtros y ORDER BY compatibles con SQLAlchemy 2."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

from app.core.pb_orm import filter_compiler
from app.core.pb_orm.query import PbQuery
from app.models.core import Producto


def test_filtro_listado_productos_compila():
    empresa_id = uuid.uuid4()
    filt = filter_compiler.compile_filters(
        Producto,
        (Producto.empresa_id == empresa_id, Producto.activo.is_(True)),
    )
    assert "empresa_id" in filt
    assert "activo" in filt


def test_order_by_nombre_asc_resuelve_columna():
    q = PbQuery(MagicMock(), Producto)
    q.order_by(Producto.nombre.asc())
    assert q._order == [("nombre", False)]


def test_order_by_nombre_sin_asc_resuelve_columna():
    q = PbQuery(MagicMock(), Producto)
    q.order_by(Producto.nombre)
    assert q._order == [("nombre", False)]


def test_listado_productos_query_params_sin_mapper():
    pb = MagicMock()
    coll = MagicMock()
    pb.collection.return_value = coll
    coll.get_list.return_value = MagicMock(items=[], totalItems=0, page=1, perPage=200)

    session = MagicMock()
    session.pb = pb
    empresa_id = uuid.uuid4()
    q = (
        PbQuery(session, Producto)
        .filter(Producto.empresa_id == empresa_id, Producto.activo.is_(True))
        .order_by(Producto.nombre.asc())
    )
    assert q.all() == []
    _args, kwargs = coll.get_list.call_args
    params = kwargs["query_params"]
    assert "Mapper" not in params["sort"]
    assert params["sort"] == "+nombre"
    assert "empresa_id" in params["filter"]
    assert "activo" in params["filter"]
