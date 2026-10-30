"""Nuevo Cobro lista ventas a crédito con saldo, sin exigir cuotas ni un estado exacto."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.deps import obtener_usuario_actual
from app.main import app
from app.models.core import (
    Cliente,
    CuotaAmortizacion,
    Empresa,
    EstadoCuota,
    EstadoVenta,
    FrecuenciaPago,
    RolUsuario,
    Usuario,
    Venta,
)
from app.services.amortizacion import asegurar_cuota_unica_si_falta, serializar_cuota


class _Q:
    def __init__(self, rows):
        self._rows = list(rows)

    def options(self, *a, **k):
        return self

    def filter(self, *a, **k):
        return self

    def order_by(self, *a, **k):
        return self

    def distinct(self):
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


def _venta(vid, cliente, vendedor, *, frecuencia, estado, total="20.00"):
    venta = Venta(
        id=vid,
        empresa_id=cliente.empresa_id,
        cliente_id=cliente.id,
        vendedor_id=vendedor.id,
        fecha=datetime(2026, 10, 12, 15, 30, 0),
        total_usd=Decimal(total),
        tasa_usd_aplicada=Decimal("40"),
        tasa_eur_aplicada=Decimal("45"),
        frecuencia_pago=frecuencia,
        estado=estado,
        metodo_pago="efectivo",
    )
    venta.cliente = cliente
    venta.cobros = []
    venta.cuotas = []
    venta.detalles = []
    return venta


def _mundo():
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
    admin = Usuario(
        id="usr0000000000a",
        empresa_id=emp,
        nombre="Admin",
        username="admin",
        rol=RolUsuario.ADMINISTRADOR,
        password_hash="x",
        activo=True,
    )
    cobrador = Usuario(
        id="usr0000000000c",
        empresa_id=emp,
        nombre="Cobro",
        username="cob",
        rol=RolUsuario.COBRADOR,
        password_hash="x",
        activo=True,
    )
    otro = Usuario(
        id="usr0000000000x",
        empresa_id=emp,
        nombre="Otro",
        username="otro",
        rol=RolUsuario.COBRADOR,
        password_hash="x",
        activo=True,
    )
    en_ruta = Cliente(
        id="cli00000000001",
        empresa_id=emp,
        nombre="Ana Pérez",
        identificacion="V1",
        telefono="04141111111",
        vendedor_id=cobrador.id,
    )
    fuera = Cliente(
        id="cli00000000002",
        empresa_id=emp,
        nombre="Luis Mora",
        identificacion="V2",
        telefono="04142222222",
        vendedor_id=otro.id,
    )
    sin_cuotas = _venta(
        "ven00000000001",
        en_ruta,
        dueno,
        frecuencia=FrecuenciaPago.SEMANAL,
        estado=EstadoVenta.PENDIENTE,
    )
    # Estado guardado como nombre del enum: el filtro SQL `pendiente` no lo veía.
    casilla = _venta(
        "ven00000000002",
        en_ruta,
        dueno,
        frecuencia=FrecuenciaPago.MENSUAL,
        estado=EstadoVenta.PENDIENTE,
        total="15.00",
    )
    casilla.estado = "PENDIENTE"
    de_otro = _venta(
        "ven00000000003",
        fuera,
        dueno,
        frecuencia=FrecuenciaPago.QUINCENAL,
        estado=EstadoVenta.PARCIAL,
        total="30.00",
    )
    cuota = CuotaAmortizacion(
        id="cuo00000000009",
        venta_id=de_otro.id,
        numero_cuota=1,
        fecha_vencimiento=datetime(2026, 10, 20, 12, 0, 0),
        monto_usd=Decimal("30.00"),
        monto_pagado_usd=None,
        estado=EstadoCuota.PENDIENTE,
    )
    de_otro.cuotas = [cuota]
    borrador = _venta(
        "ven00000000004",
        en_ruta,
        dueno,
        frecuencia=FrecuenciaPago.SEMANAL,
        estado=EstadoVenta.BORRADOR,
    )
    tablas = {
        Empresa: [Empresa(id=emp, nombre="ED NET", activa=True)],
        Usuario: [dueno, admin, cobrador, otro],
        Cliente: [en_ruta, fuera],
        Venta: [sin_cuotas, casilla, de_otro, borrador],
        CuotaAmortizacion: [cuota],
    }
    return {
        "db": Mem(tablas),
        "dueno": dueno,
        "admin": admin,
        "cobrador": cobrador,
        "sin_cuotas": sin_cuotas,
        "de_otro": de_otro,
        "cuota": cuota,
    }


@pytest.fixture
def mundo():
    return _mundo()


def _client(db, usuario):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario
    return TestClient(app)


def test_credito_sin_cuotas_y_estado_en_mayusculas_salen_en_nuevo_cobro(mundo):
    client = _client(mundo["db"], mundo["dueno"])
    try:
        res = client.get("/api/v1/cobros/ventas-pendientes")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200, res.text
    body = res.json()
    ids = {item["id"] for item in body}
    assert "ven00000000001" in ids
    assert "ven00000000002" in ids
    assert "ven00000000004" not in ids
    ana = next(item for item in body if item["id"] == "ven00000000001")
    assert ana["cliente_nombre"] == "Ana Pérez"
    assert ana["saldo_pendiente_usd"] == 20.0
    assert ana["fecha"].startswith("2026-10-12")
    # La cuota con monto_pagado nulo no tumba el listado.
    assert "ven00000000003" in ids


def test_cobrador_solo_ve_clientes_de_su_ruta(mundo):
    client = _client(mundo["db"], mundo["cobrador"])
    try:
        res = client.get("/api/v1/cobros/ventas-pendientes")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200, res.text
    ids = {item["id"] for item in res.json()}
    assert "ven00000000001" in ids
    assert "ven00000000003" not in ids


def test_administrador_ve_todas_las_ventas_cobrables(mundo):
    client = _client(mundo["db"], mundo["admin"])
    try:
        res = client.get("/api/v1/cobros/ventas-pendientes")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200, res.text
    ids = {item["id"] for item in res.json()}
    assert {"ven00000000001", "ven00000000002", "ven00000000003"} <= ids


def test_cuota_con_monto_pagado_nulo_se_serializa():
    cuota = CuotaAmortizacion(
        id="cuo00000000001",
        venta_id="ven00000000001",
        numero_cuota=1,
        fecha_vencimiento=datetime(2026, 10, 20),
        monto_usd=Decimal("20"),
        monto_pagado_usd=None,
        estado=EstadoCuota.PENDIENTE,
    )
    data = serializar_cuota(cuota, FrecuenciaPago.SEMANAL)
    assert data["monto_pagado_usd"] == 0.0


def test_credito_sin_plan_recibe_una_cuota_por_el_total(mundo):
    venta = mundo["sin_cuotas"]
    db = Mem({CuotaAmortizacion: []})
    creada = asegurar_cuota_unica_si_falta(db, venta)
    assert creada is not None
    assert creada.numero_cuota == 1
    assert Decimal(str(creada.monto_usd)) == Decimal("20.00")
    assert len(venta.cuotas) == 1
