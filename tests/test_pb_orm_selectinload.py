"""selectinload → nombres de relación para carga eager del ORM PocketBase."""
from __future__ import annotations

from unittest.mock import MagicMock

from sqlalchemy.orm import selectinload

from app.core.pb_orm.query import PbQuery, _eager_attr_names_from_loader_option
from app.models.core import Venta


def test_eager_names_desde_selectinload_cobros_y_cuotas():
    assert _eager_attr_names_from_loader_option(selectinload(Venta.cobros)) == ["cobros"]
    assert _eager_attr_names_from_loader_option(selectinload(Venta.cuotas)) == ["cuotas"]


def test_pb_query_options_no_lanza_con_selectinload():
    session = MagicMock()
    q = PbQuery(session, Venta)
    q.options(selectinload(Venta.cobros), selectinload(Venta.cuotas))
    assert q._eager == {"cobros", "cuotas"}
