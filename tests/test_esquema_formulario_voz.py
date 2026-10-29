"""Campos del formulario, un dato por turno, y coincidencias aisladas por empresa."""
from __future__ import annotations

from types import SimpleNamespace

from app.models.core import Cliente, RolUsuario
from app.services.ai_llm_tools import HERRAMIENTAS_OPENAI
from app.services.ai_voice_parecido import (
    _nombres_cliente_visibles,
    coincidencia_parecida,
)
from app.services.esquema_formulario import (
    FORMULARIO_EXIGE_CEDULA,
    cedula_exigida,
    claves_obligatorias,
    faltantes_cliente,
)


def _tool(nombre: str) -> dict:
    return next(t for t in HERRAMIENTAS_OPENAI if t["function"]["name"] == nombre)


def test_venta_y_cobro_usan_el_esquema_del_formulario():
    assert _tool("crear_pedido")["function"]["parameters"]["required"] == list(
        claves_obligatorias("crear_pedido")
    )
    assert _tool("registrar_cobro")["function"]["parameters"]["required"] == list(
        claves_obligatorias("registrar_cobro")
    )
    props = _tool("registrar_cliente")["function"]["parameters"]["properties"]
    for clave in claves_obligatorias("registrar_cliente"):
        assert clave in props


def test_cliente_pide_un_dato_y_no_inventa():
    assert FORMULARIO_EXIGE_CEDULA is True
    assert cedula_exigida("VE") is True
    vacio: dict = {}
    assert faltantes_cliente(vacio)[0] == "nombre"
    solo_nombre = faltantes_cliente({"nombre": "Ana"})
    assert solo_nombre[0] == "apellido"
    assert "telefono" in solo_nombre
    assert vacio == {}
    completo = {
        "nombre": "Ana Pérez",
        "telefono": "04141234567",
        "whatsapp": "+584141234567",
        "direccion": "Calle 1",
        "identificacion": "V12345678",
    }
    assert faltantes_cliente(completo) == []


def test_coincidencia_parecida_confirma_un_solo_nombre():
    assert coincidencia_parecida("Juan Peres", ["Juan Pérez", "Luis Gómez"]) == "Juan Pérez"
    assert coincidencia_parecida("Juan Pérez", ["Juan Pérez"]) is None
    assert coincidencia_parecida("Juan", ["Juan Pérez", "Juan López"]) is None


def test_busqueda_de_clientes_filtra_por_empresa_y_rol():
    class _Query:
        def __init__(self):
            self.filtros: list[str] = []

        def filter(self, *args):
            self.filtros.extend(str(a) for a in args)
            return self

        def all(self):
            return []

    class _Db:
        def __init__(self):
            self.q = _Query()

        def query(self, model):
            assert model is Cliente
            return self.q

    dueno = SimpleNamespace(empresa_id="emp-1", id="usr-1", rol=RolUsuario.DUENO)
    db = _Db()
    assert _nombres_cliente_visibles(db, dueno) == []
    assert any("empresa_id" in f for f in db.q.filtros)

    vendedor = SimpleNamespace(empresa_id="emp-1", id="usr-2", rol=RolUsuario.VENDEDOR)
    db_v = _Db()
    _nombres_cliente_visibles(db_v, vendedor)
    texto = " ".join(db_v.q.filtros)
    assert "empresa_id" in texto
    assert "vendedor_id" in texto
