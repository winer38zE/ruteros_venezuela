"""El cobro se guarda; el 500 estaba al leer la lista, no al escribir.

Causa: listar_mis_cobros devolvía el ORM. CobroResponse exige sincronizado,
fecha_creacion, es_transferencia y verificado. Esos defaults no se aplican al
construir el objeto (PocketBase tampoco los devuelve si no se guardaron) y
Pydantic responde ValidationError, que FastAPI convierte en HTTP 500.
El POST usaba _respuesta_cobro y por eso la app decía «Cobro registrado».
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.db import get_db
from app.core.deps import obtener_usuario_actual
from app.main import app
from app.models.core import (
    Cliente,
    Cobro,
    Empresa,
    EstadoVenta,
    FrecuenciaPago,
    MonedaPago,
    RolUsuario,
    Usuario,
    Venta,
)
from app.schemas.core import CobroResponse
from app.services.ai_voice_executor import _registrar_cobro


class _Q:
    def __init__(self, rows):
        self._rows = list(rows)

    def options(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self

    def first(self):
        return self._rows[0] if self._rows else None

    def all(self):
        return list(self._rows)


class Mem:
    def __init__(self, tablas):
        self.tablas = tablas

    def query(self, model):
        return _Q(self.tablas.get(model, []))

    def add(self, obj):
        self.tablas.setdefault(type(obj), []).append(obj)

    def flush(self):
        return None

    def commit(self):
        return None

    def rollback(self):
        return None

    def refresh(self, obj, attribute_names=None):
        return None


def _base():
    emp = "emp00000000001"
    dueno = Usuario(
        id="usr0000000000d",
        empresa_id=emp,
        nombre="Dueño",
        username="dueno",
        rol=RolUsuario.DUENO,
        password_hash="x",
        activo=True,
    )
    cliente = Cliente(
        id="cli00000000001",
        empresa_id=emp,
        nombre="Ana Pérez",
        identificacion="V1",
        telefono="04141234567",
        vendedor_id=dueno.id,
    )
    venta = Venta(
        id="ven00000000001",
        empresa_id=emp,
        cliente_id=cliente.id,
        vendedor_id=dueno.id,
        fecha=datetime(2026, 10, 1, 12, 0, 0),
        total_usd=Decimal("20.00"),
        tasa_usd_aplicada=Decimal("40"),
        tasa_eur_aplicada=Decimal("45"),
        frecuencia_pago=FrecuenciaPago.SEMANAL,
        estado=EstadoVenta.PENDIENTE,
        metodo_pago="efectivo",
    )
    venta.cliente = cliente
    venta.cobros = []
    venta.cuotas = []
    venta.detalles = []
    tablas = {
        Empresa: [Empresa(id=emp, nombre="ED NET", activa=True)],
        Usuario: [dueno],
        Cliente: [cliente],
        Venta: [venta],
        Cobro: [],
    }
    return dueno, venta, Mem(tablas)


def _client(db, usuario):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario
    return TestClient(app)


def test_orm_con_defaults_nulos_revienta_la_validacion_del_response():
    cobro = Cobro(
        id="cob00000000001",
        empresa_id="emp00000000001",
        venta_id="ven00000000001",
        cobrador_id="usr0000000000d",
        fecha=datetime(2026, 10, 30, 12, 0, 0),
        monto_usd=Decimal("10"),
        moneda_pago=MonedaPago.DOLAR,
        tasa_usd_aplicada=Decimal("40"),
        tasa_eur_aplicada=Decimal("45"),
    )
    with pytest.raises(ValidationError) as exc:
        CobroResponse.model_validate(cobro)
    texto = str(exc.value)
    assert "fecha_creacion" in texto
    assert "sincronizado" in texto
    assert "es_transferencia" in texto
    assert "verificado" in texto


def test_lista_tolera_cobro_sin_venta_ni_defaults():
    dueno, _venta, db = _base()
    huerfano = Cobro(
        id="cob00000000009",
        empresa_id=dueno.empresa_id,
        venta_id="vennoexiste0001",
        cobrador_id=dueno.id,
        fecha=datetime(2026, 10, 30, 8, 0, 0),
        monto_usd=Decimal("10"),
        moneda_pago=MonedaPago.DOLAR,
        tasa_usd_aplicada=Decimal("40"),
        tasa_eur_aplicada=Decimal("45"),
    )
    db.add(huerfano)
    client = _client(db, dueno)
    try:
        res = client.get("/api/v1/cobros/mis-cobros")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200, res.text
    body = res.json()
    assert len(body) == 1
    assert body[0]["venta_id"] == "vennoexiste0001"
    assert body[0]["estado_venta"] is None
    assert body[0]["monto_usd"] == 10.0


def test_formulario_registra_lista_y_el_reintento_no_duplica():
    dueno, venta, db = _base()
    client = _client(db, dueno)
    cuerpo = {
        "id": "cobform00000001",
        "venta_id": venta.id,
        "monto_usd": 10,
        "moneda_pago": "dolar",
        "tasa_usd_aplicada": 40,
        "tasa_eur_aplicada": 45,
    }
    try:
        alta = client.post("/api/v1/cobros/", json=cuerpo)
        assert alta.status_code == 200, alta.text
        lista = client.get("/api/v1/cobros/mis-cobros")
        assert lista.status_code == 200, lista.text
        assert len(lista.json()) == 1
        assert lista.json()[0]["monto_usd"] == 10
        assert lista.json()[0]["estado_venta"] == "parcial"
        otra = client.post("/api/v1/cobros/", json=cuerpo)
        assert otra.status_code == 200, otra.text
        assert otra.json()["id"] == alta.json()["id"]
        lista2 = client.get("/api/v1/cobros/mis-cobros")
    finally:
        app.dependency_overrides.clear()
    assert lista2.status_code == 200
    assert len(lista2.json()) == 1
    assert len(db.tablas[Cobro]) == 1
    assert Decimal(str(venta.total_usd)) - sum(Decimal(str(c.monto_usd)) for c in venta.cobros) == Decimal("10")


def test_voz_registra_y_la_lista_no_responde_500():
    dueno, venta, db = _base()
    ok, mensaje, detalle, _wa = _registrar_cobro(
        db,
        dueno,
        dueno.empresa_id,
        {
            "cliente_nombre": "Ana Pérez",
            "monto_usd": 10,
            "metodo_pago": "efectivo",
            "clave_idempotencia": "cobvoz000000001",
        },
    )
    assert ok is True, mensaje
    ok2, _msg2, detalle2, _wa2 = _registrar_cobro(
        db,
        dueno,
        dueno.empresa_id,
        {
            "cliente_nombre": "Ana Pérez",
            "monto_usd": 10,
            "metodo_pago": "efectivo",
            "clave_idempotencia": "cobvoz000000001",
        },
    )
    assert ok2 is True
    assert detalle2["cobro_id"] == detalle["cobro_id"]
    assert len(db.tablas[Cobro]) == 1
    client = _client(db, dueno)
    try:
        res = client.get("/api/v1/cobros/mis-cobros")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200, res.text
    assert len(res.json()) == 1
    assert res.json()[0]["venta_id"] == venta.id
