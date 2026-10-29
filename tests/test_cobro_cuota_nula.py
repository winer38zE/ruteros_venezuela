"""Una cuota sin monto_pagado no debe tumbar el cobro ni dejar la cuota intacta."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from app.api.cobros import _registrar_cobro_interno
from app.models.core import (
    Cliente,
    Cobro,
    CuotaAmortizacion,
    Empresa,
    EstadoCuota,
    EstadoVenta,
    FrecuenciaPago,
    RolUsuario,
    Usuario,
    Venta,
)
from app.schemas.core import CobroCreate
from app.services.ai_voice_executor import _registrar_cobro
from app.services.amortizacion import aplicar_abono_a_cuotas


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
        if isinstance(obj, Venta) and attribute_names and "cobros" in attribute_names:
            obj.cobros = [c for c in self.tablas.get(Cobro, []) if c.venta_id == obj.id]


def _escenario():
    emp = "emp00000000001"
    usuario = Usuario(
        id="usr00000000001",
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
        identificacion="V12345678",
        telefono="04141234567",
    )
    venta = Venta(
        id="ven00000000001",
        empresa_id=emp,
        cliente_id=cliente.id,
        vendedor_id=usuario.id,
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
    cuota = CuotaAmortizacion(
        id="cuo00000000001",
        venta_id=venta.id,
        numero_cuota=1,
        fecha_vencimiento=datetime(2026, 10, 8, 12, 0, 0),
        monto_usd=Decimal("20.00"),
        monto_pagado_usd=None,
        estado=EstadoCuota.PENDIENTE,
    )
    venta.cuotas = [cuota]
    tablas = {
        Empresa: [Empresa(id=emp, nombre="ED NET", activa=True)],
        Usuario: [usuario],
        Cliente: [cliente],
        Venta: [venta],
        CuotaAmortizacion: [cuota],
        Cobro: [],
    }
    return usuario, venta, cuota, Mem(tablas)


def test_abono_con_monto_pagado_nulo_no_revienta():
    _, venta, cuota, db = _escenario()
    aplicar_abono_a_cuotas(db, venta, Decimal("10"))
    assert Decimal(str(cuota.monto_pagado_usd)) == Decimal("10")
    assert cuota.estado == EstadoCuota.PARCIAL


def test_api_registra_cobro_aunque_la_cuota_no_traiga_pagado():
    usuario, venta, cuota, db = _escenario()
    resp = _registrar_cobro_interno(
        db,
        CobroCreate(
            venta_id=venta.id,
            monto_usd=10,
            moneda_pago="dolar",
            tasa_usd_aplicada=40,
            tasa_eur_aplicada=45,
        ),
        usuario,
    )
    assert resp.monto_usd == 10
    assert Decimal(str(cuota.monto_pagado_usd)) == Decimal("10")
    assert cuota.estado == EstadoCuota.PARCIAL


def test_voz_registra_cobro_aunque_la_cuota_no_traiga_pagado():
    usuario, venta, cuota, db = _escenario()
    ok, mensaje, detalle, _wa = _registrar_cobro(
        db,
        usuario,
        usuario.empresa_id,
        {"cliente_nombre": "Ana Pérez", "monto_usd": 10, "metodo_pago": "efectivo"},
    )
    assert ok is True, mensaje
    assert detalle["venta_id"] == str(venta.id)
    assert Decimal(str(cuota.monto_pagado_usd)) == Decimal("10")
