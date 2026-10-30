"""Historial con el nombre del cliente, recibo por WhatsApp y seguimiento GPS."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.deps import obtener_usuario_actual
from app.main import app
from app.models.core import (
    Cliente,
    Cobro,
    CuotaAmortizacion,
    DetalleVenta,
    Empresa,
    EstadoVenta,
    FrecuenciaPago,
    Producto,
    RolUsuario,
    Usuario,
    Venta,
)


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


def _usuario(uid, emp, nombre, rol):
    return Usuario(
        id=uid,
        empresa_id=emp,
        nombre=nombre,
        username=uid,
        rol=rol,
        password_hash="x",
        activo=True,
    )


def _venta(vid, cliente, vendedor, total="20.00"):
    venta = Venta(
        id=vid,
        empresa_id=cliente.empresa_id,
        cliente_id=cliente.id,
        vendedor_id=vendedor.id,
        fecha=datetime(2026, 10, 12, 15, 30, 0),
        total_usd=Decimal(total),
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
    return venta


def _client(db, usuario):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[obtener_usuario_actual] = lambda: usuario
    return TestClient(app)


def _mundo_ventas():
    emp = "emp00000000001"
    dueno = _usuario("usr0000000000d", emp, "Dueño", RolUsuario.DUENO)
    ana = Cliente(
        id="cli00000000001",
        empresa_id=emp,
        nombre="Ana Pérez",
        identificacion="V1",
        telefono="04141234567",
        email=None,
        vendedor_id=dueno.id,
    )
    luis = Cliente(
        id="cli00000000002",
        empresa_id=emp,
        nombre="Luis Mora",
        identificacion="V2",
        telefono="04147654321",
        email="luis@example.com",
        vendedor_id=dueno.id,
    )
    sin_tel = Cliente(
        id="cli00000000003",
        empresa_id=emp,
        nombre="Sin Telefono",
        identificacion="V3",
        telefono="",
        email=None,
        vendedor_id=dueno.id,
    )
    producto = Producto(
        id="prd00000000001",
        empresa_id=emp,
        nombre="Router",
        precio_usd=Decimal("20"),
        costo_usd=Decimal("8"),
    )
    venta_ana = _venta("ven00000000001", ana, dueno)
    detalle = DetalleVenta(
        id="det00000000001",
        venta_id=venta_ana.id,
        producto_id=producto.id,
        cantidad=1,
        precio_unitario_usd=Decimal("20"),
    )
    venta_ana.detalles = [detalle]
    venta_luis = _venta("ven00000000002", luis, dueno)
    venta_sin = _venta("ven00000000003", sin_tel, dueno)
    tablas = {
        Empresa: [Empresa(id=emp, nombre="ED NET", activa=True)],
        Usuario: [dueno],
        Cliente: [ana, luis, sin_tel],
        Venta: [venta_ana, venta_luis, venta_sin],
        Producto: [producto],
        DetalleVenta: [detalle],
        Cobro: [],
        CuotaAmortizacion: [],
    }
    return dueno, venta_ana, venta_sin, Mem(tablas)


def test_historial_devuelve_nombre_apellido_telefono_y_busca():
    dueno, venta_ana, _sin, db = _mundo_ventas()
    client = _client(db, dueno)
    try:
        todas = client.get("/api/v1/ventas/mis-ventas")
        assert todas.status_code == 200, todas.text
        ana = next(v for v in todas.json() if v["id"] == venta_ana.id)
        assert ana["cliente_nombre"] == "Ana"
        assert ana["cliente_apellido"] == "Pérez"
        assert ana["cliente_telefono"] == "04141234567"
        assert ana["saldo_pendiente_usd"] == 20.0
        assert "Router" in ana["productos_resumen"]
        assert ana["detalles"][0]["producto_nombre"] == "Router"
        busqueda = client.get("/api/v1/ventas/mis-ventas", params={"q": "pérez"})
        assert busqueda.status_code == 200, busqueda.text
        ids = [v["id"] for v in busqueda.json()]
        assert ids == [venta_ana.id]
        por_tel = client.get("/api/v1/ventas/mis-ventas", params={"q": "04147654321"})
        assert [v["cliente_nombre"] for v in por_tel.json()] == ["Luis"]
    finally:
        app.dependency_overrides.clear()


def test_recibo_whatsapp_sin_telefono_es_400():
    dueno, _ana, venta_sin, db = _mundo_ventas()
    client = _client(db, dueno)
    try:
        res = client.post(f"/api/v1/ventas/{venta_sin.id}/recibo/whatsapp")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 400, res.text
    assert "teléfono" in res.json()["detail"]


def test_recibo_whatsapp_envia_el_texto_del_cliente(monkeypatch):
    dueno, venta_ana, _sin, db = _mundo_ventas()
    enviados = {}

    def falso_enviar(numero, texto):
        enviados["numero"] = numero
        enviados["texto"] = texto
        return True, "enviado"

    monkeypatch.setattr("app.api.ventas.enviar_texto", falso_enviar)
    client = _client(db, dueno)
    try:
        res = client.post(f"/api/v1/ventas/{venta_ana.id}/recibo/whatsapp")
    finally:
        app.dependency_overrides.clear()
    assert res.status_code == 200, res.text
    assert res.json()["enviado"] is True
    assert "Ana Pérez" in enviados["texto"]
    assert "04141234567" in (enviados["numero"] + res.json()["telefono"])


def test_cobro_con_gps_sin_gps_y_seguimiento_solo_dueno_o_admin():
    emp = "emp00000000001"
    dueno = _usuario("usr0000000000d", emp, "Dueño", RolUsuario.DUENO)
    admin = _usuario("usr0000000000a", emp, "Admin", RolUsuario.ADMINISTRADOR)
    cobrador = _usuario("usr0000000000c", emp, "Cobro Calle", RolUsuario.COBRADOR)
    vendedor = _usuario("usr0000000000v", emp, "Vende", RolUsuario.VENDEDOR)
    cliente = Cliente(
        id="cli00000000001",
        empresa_id=emp,
        nombre="Ana Pérez",
        identificacion="V1",
        telefono="04141234567",
        vendedor_id=cobrador.id,
    )
    venta = _venta("ven00000000001", cliente, cobrador, total="20.00")
    db = Mem(
        {
            Empresa: [Empresa(id=emp, nombre="ED NET", activa=True)],
            Usuario: [dueno, admin, cobrador, vendedor],
            Cliente: [cliente],
            Venta: [venta],
            Cobro: [],
            CuotaAmortizacion: [],
            Producto: [],
        }
    )
    cuerpo_gps = {
        "id": "cobgps000000001",
        "venta_id": venta.id,
        "monto_usd": 10,
        "moneda_pago": "dolar",
        "tasa_usd_aplicada": 40,
        "tasa_eur_aplicada": 45,
        "fecha": "2026-10-30T10:00:00",
        "latitud": 10.48,
        "longitud": -66.90,
        "precision_metros": 12.5,
    }
    cuerpo_sin = {
        "id": "cobsin000000001",
        "venta_id": venta.id,
        "monto_usd": 10,
        "moneda_pago": "bolivar",
        "tasa_usd_aplicada": 40,
        "tasa_eur_aplicada": 45,
        "fecha": "2026-10-30T11:15:00",
    }
    client = _client(db, dueno)
    try:
        con = client.post("/api/v1/cobros/", json=cuerpo_gps)
        assert con.status_code == 200, con.text
        assert con.json()["sin_ubicacion"] is False
        assert con.json()["latitud"] == 10.48
        assert con.json()["cliente_nombre"] == "Ana Pérez"
        otra = client.post("/api/v1/cobros/", json=cuerpo_gps)
        assert otra.status_code == 200, otra.text
        assert otra.json()["id"] == con.json()["id"]
        sin = client.post("/api/v1/cobros/", json=cuerpo_sin)
        assert sin.status_code == 200, sin.text
        assert sin.json()["sin_ubicacion"] is True
        assert sin.json()["latitud"] is None
        assert len(db.tablas[Cobro]) == 2

        ruta = client.get(
            "/api/v1/cobros/seguimiento",
            params={"cobrador_id": dueno.id, "fecha": "2026-10-30"},
        )
        assert ruta.status_code == 200, ruta.text
        puntos = ruta.json()["puntos"]
        assert [p["cobro_id"] for p in puntos] == [con.json()["id"], sin.json()["id"]]
        assert puntos[0]["sin_ubicacion"] is False
        assert puntos[0]["cliente_nombre"] == "Ana Pérez"
        assert puntos[0]["metodo"] == "dolar"
        assert puntos[1]["sin_ubicacion"] is True
        assert puntos[1]["metodo"] == "bolivar"
        assert puntos[0]["latitud"] == 10.48
        assert puntos[0]["longitud"] == -66.90

        personas = client.get("/api/v1/cobros/seguimiento/cobradores")
        assert personas.status_code == 200, personas.text
        assert any(p["id"] == cobrador.id and p["nombre"] == "Cobro Calle" for p in personas.json())

        faltante = client.get(
            "/api/v1/cobros/seguimiento",
            params={"cobrador_id": "usrnoexiste0001", "fecha": "2026-10-30"},
        )
        assert faltante.status_code == 404
    finally:
        app.dependency_overrides.clear()

    for quien, codigo in ((cobrador, 403), (vendedor, 403), (admin, 200)):
        client = _client(db, quien)
        try:
            res = client.get(
                "/api/v1/cobros/seguimiento",
                params={"cobrador_id": dueno.id, "fecha": "2026-10-30"},
            )
        finally:
            app.dependency_overrides.clear()
        assert res.status_code == codigo, (quien.rol, res.text)
