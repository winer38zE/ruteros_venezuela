"""Inferencia de modelo y orden secuencial en PbORM (SQLAlchemy 2 + PocketBase)."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from sqlalchemy import func

from app.api.clientes import crear_cliente
from app.core.pb_orm.query import PbQuery
from app.core.pb_orm.session import PbSession, _infer_model_from_expression
from app.models.core import Cliente, CuentaBancaria, DiaVisita, Empresa, RolUsuario, Usuario
from app.schemas.core import ClienteCreate
from app.services.rutas import siguiente_orden_secuencial


def test_infer_model_desde_clase_cliente():
    assert _infer_model_from_expression(Cliente) is Cliente


def test_infer_model_func_count_cliente_id():
    assert _infer_model_from_expression(func.count(Cliente.id)) is Cliente


def test_infer_model_func_coalesce_solo():
    expr = func.coalesce(Cliente.orden_ruta, Cliente.orden_secuencial)
    assert _infer_model_from_expression(expr) is Cliente


def test_infer_model_max_coalesce_cliente():
    expr = func.max(func.coalesce(Cliente.orden_ruta, Cliente.orden_secuencial))
    assert _infer_model_from_expression(expr) is Cliente


def test_infer_model_columna_instrumentada():
    assert _infer_model_from_expression(CuentaBancaria.id) is CuentaBancaria


def test_pb_session_query_scalar_no_lanza_con_max_coalesce():
    pb = MagicMock()
    coll = MagicMock()
    pb.collection.return_value = coll
    coll.get_list.return_value = MagicMock(items=[], totalItems=0, page=1, perPage=200)

    session = PbSession(pb)
    expr = func.max(func.coalesce(Cliente.orden_ruta, Cliente.orden_secuencial))
    q = session.query(expr)
    assert q._model is Cliente
    assert q.scalar() is None


def test_siguiente_orden_sin_clientes_previos():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.scalar.return_value = None
    db.query.return_value = q

    vid = uuid.uuid4()
    eid = uuid.uuid4()
    orden = siguiente_orden_secuencial(db, vid, DiaVisita.LUNES, eid)
    assert orden == 1
    db.query.assert_called_once()


def test_siguiente_orden_aislamiento_pasa_empresa_id_en_filtro():
    db = MagicMock()
    capturados: list = []
    q = MagicMock()

    def capturar_filtro(*args, **kwargs):
        capturados.extend(args)
        return q

    q.filter.side_effect = capturar_filtro
    q.scalar.return_value = 2
    db.query.return_value = q

    eid = uuid.uuid4()
    siguiente_orden_secuencial(db, uuid.uuid4(), DiaVisita.LUNES, eid)
    assert capturados, "Debe aplicar filtros sobre Cliente"
    assert any(
        getattr(arg, "key", None) == "empresa_id" or "empresa_id" in str(arg)
        for arg in capturados
    )


def test_siguiente_orden_con_max_existente():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.scalar.return_value = 5
    db.query.return_value = q

    orden = siguiente_orden_secuencial(
        db, uuid.uuid4(), DiaVisita.MARTES, uuid.uuid4()
    )
    assert orden == 6


def test_siguiente_orden_con_ordenes_2_y_5():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.scalar.return_value = 5
    db.query.return_value = q
    assert siguiente_orden_secuencial(db, uuid.uuid4(), DiaVisita.VIERNES, uuid.uuid4()) == 6


def test_eval_scalar_max_coalesce_sobre_filas_cargadas():
    session = MagicMock()
    q = PbQuery(session, Cliente)
    q._scalar_expr = func.max(func.coalesce(Cliente.orden_ruta, Cliente.orden_secuencial))
    c1 = Cliente(
        id=uuid.uuid4(),
        empresa_id=uuid.uuid4(),
        nombre="A",
        identificacion="V11111111",
        orden_ruta=2,
        orden_secuencial=None,
    )
    c2 = Cliente(
        id=uuid.uuid4(),
        empresa_id=uuid.uuid4(),
        nombre="B",
        identificacion="V22222222",
        orden_ruta=None,
        orden_secuencial=7,
    )
    q.all = MagicMock(return_value=[c1, c2])
    assert q.scalar() == 7


def test_crear_cliente_rechaza_identificacion_duplicada(monkeypatch):
    empresa = Empresa(id=uuid.uuid4(), nombre="E", activa=True)
    usuario = Usuario(
        id=uuid.uuid4(),
        empresa_id=empresa.id,
        nombre="V",
        username="vendedor",
        password_hash="x",
        rol=RolUsuario.VENDEDOR,
        activo=True,
    )
    db = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is Empresa:
            q.filter.return_value = q
            q.first.return_value = empresa
        elif model is Cliente:
            q.filter.return_value = q
            q.first.return_value = Cliente(
                id=uuid.uuid4(),
                empresa_id=empresa.id,
                nombre="Existente",
                identificacion="V12345678",
            )
        return q

    db.query.side_effect = query_side
    monkeypatch.setattr("app.api.clientes.obtener_empresa_tenant", lambda _db, _u: empresa)

    body = ClienteCreate(
        nombre_completo="Nuevo",
        identificacion="V12345678",
        telefono="04120000000",
    )
    with pytest.raises(HTTPException) as exc_info:
        crear_cliente(body, db=db, usuario=usuario)
    assert exc_info.value.status_code == 400


def test_crear_cliente_asigna_siguiente_orden(monkeypatch):
    empresa = Empresa(id=uuid.uuid4(), nombre="E", activa=True)
    usuario = Usuario(
        id=uuid.uuid4(),
        empresa_id=empresa.id,
        nombre="V",
        username="vendedor",
        password_hash="x",
        rol=RolUsuario.VENDEDOR,
        activo=True,
    )
    db = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is Empresa:
            q.filter.return_value = q
            q.first.return_value = empresa
        elif model is Cliente:
            q.filter.return_value = q
            q.first.return_value = None
        return q

    db.query.side_effect = query_side
    monkeypatch.setattr("app.api.clientes.obtener_empresa_tenant", lambda _db, _u: empresa)
    monkeypatch.setattr(
        "app.api.clientes.siguiente_orden_secuencial",
        lambda *_a, **_k: 3,
    )
    monkeypatch.setattr("app.api.clientes.sincronizar_score_inicial", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "app.api.clientes.actualizar_historial_comportamiento", lambda *_a, **_k: None
    )

    body = ClienteCreate(
        nombre_completo="Nuevo Cliente",
        identificacion="V87654321",
        telefono="04121111111",
    )
    resp = crear_cliente(body, db=db, usuario=usuario)
    assert resp.orden_ruta == 3
    assert resp.orden_secuencial == 3
    db.add.assert_called_once()
    db.commit.assert_called_once()
