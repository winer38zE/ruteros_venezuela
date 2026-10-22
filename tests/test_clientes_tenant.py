"""Listado de clientes: auth JWT, tenant y aislamiento entre empresas."""
from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException
from app.api.clientes import listar_clientes, obtener_cliente
from app.core.deps import obtener_usuario_actual
from app.core.tenant import obtener_empresa_tenant
from app.models.core import Cliente, Empresa, RolUsuario, Usuario


def _usuario(empresa_id: uuid.UUID, rol=RolUsuario.VENDEDOR) -> Usuario:
    return Usuario(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        nombre="Vendedor",
        username="vendedor",
        password_hash="x",
        rol=rol,
        activo=True,
    )


def _empresa(nombre: str = "Empresa A") -> Empresa:
    return Empresa(id=uuid.uuid4(), nombre=nombre, activa=True)


def _cliente(empresa_id: uuid.UUID, nombre: str) -> Cliente:
    return Cliente(
        id=uuid.uuid4(),
        empresa_id=empresa_id,
        nombre=nombre,
        identificacion="V12345678",
        telefono="04120000000",
    )


def test_listar_clientes_no_unbound_local_con_usuario_autenticado():
    """Regression: del usuario + obtener_empresa_tenant(db, usuario) rompía el listado."""
    emp_a = _empresa("A")
    usuario = _usuario(emp_a.id)
    c1 = _cliente(emp_a.id, "Cliente A")

    db = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is Empresa:
            q.filter.return_value = q
            q.first.return_value = emp_a
        elif model is Cliente:
            q.filter.return_value = q
            q.order_by.return_value = q
            q.all.return_value = [c1]
        return q

    db.query.side_effect = query_side

    resultado = listar_clientes(db=db, q=None, usuario=usuario)
    assert len(resultado) == 1
    assert resultado[0].nombre == "Cliente A"


def test_obtener_empresa_tenant_usa_empresa_del_usuario():
    emp_a = _empresa("A")
    usuario_a = _usuario(emp_a.id)

    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.first.return_value = emp_a
    db.query.return_value = q

    empresa = obtener_empresa_tenant(db, usuario_a)
    assert empresa.id == emp_a.id
    assert empresa.id == usuario_a.empresa_id


def test_obtener_cliente_otra_empresa_retorna_404():
    emp_a = _empresa("A")
    emp_b = _empresa("B")
    usuario = _usuario(emp_a.id)
    cliente_b = _cliente(emp_b.id, "Ajeno")

    db = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is Empresa:
            q.filter.return_value = q
            q.first.return_value = emp_a
        elif model is Cliente:
            q.filter.return_value = q
            q.first.return_value = None
        return q

    db.query.side_effect = query_side

    with pytest.raises(HTTPException) as exc_info:
        obtener_cliente(cliente_id=cliente_b.id, db=db, usuario=usuario)
    assert exc_info.value.status_code == 404


def test_aislamiento_dos_empresas_solo_ve_clientes_propios():
    emp_a, emp_b = _empresa("A"), _empresa("B")
    usuario_b = _usuario(emp_b.id)
    solo_b = _cliente(emp_b.id, "Cliente B")

    db = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is Empresa:
            q.filter.return_value = q
            q.first.return_value = emp_b
        elif model is Cliente:
            q.filter.return_value = q
            q.order_by.return_value = q
            q.all.return_value = [solo_b]
        return q

    db.query.side_effect = query_side

    resultado = listar_clientes(db=db, q=None, usuario=usuario_b)
    assert len(resultado) == 1
    assert resultado[0].nombre == "Cliente B"
    assert solo_b.empresa_id == emp_b.id
    assert solo_b.empresa_id != emp_a.id


def test_listar_clientes_requiere_sesion_valida():
    with pytest.raises(HTTPException) as exc_info:
        obtener_usuario_actual(
            x_usuario_id=str(uuid.uuid4()),
            authorization=None,
            db=MagicMock(),
        )
    assert exc_info.value.status_code == 401
