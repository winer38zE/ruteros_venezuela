"""Perfil de empresa y memoria de cliente, aislados por tenant."""
from __future__ import annotations

from types import SimpleNamespace

from app.models.core import Cliente, RolUsuario
from app.services.ai_perfil_empresa import (
    BORRADOR_ED_NET_PRO,
    bloque_memoria_cliente_llm,
    clientes_mencionados,
    resumen_factual,
)
from app.services.ai_voice_models import MemoriaCliente, PerfilEmpresa


def test_borrador_ed_net_es_editable_y_factual():
    assert "borrador" in BORRADOR_ED_NET_PRO["descripcion"].lower()
    assert "fiado" in BORRADOR_ED_NET_PRO["glosario"]
    assert resumen_factual(
        "crear_pedido",
        {"productos": [{"nombre": "sábana", "cantidad": 2}]},
    ) == "Compró 2 sábana."
    assert resumen_factual("registrar_cobro", {}) == ""
    assert PerfilEmpresa.__tablename__ == "perfil_empresa"
    assert MemoriaCliente.__tablename__ == "memoria_cliente"


def test_memoria_solo_del_cliente_mencionado_en_su_empresa():
    propio = Cliente(nombre="Ana Pérez", empresa_id="emp-a", id="cli-a")
    ajeno = Cliente(nombre="Ana Pérez", empresa_id="emp-b", id="cli-b")
    dichos = clientes_mencionados("cobré a Ana Pérez", [propio])
    assert dichos == [propio]
    assert ajeno not in dichos

    class _Filtro:
        def __init__(self):
            self.texto: list[str] = []

        def filter(self, *args):
            self.texto.extend(str(a) for a in args)
            return self

        def all(self):
            return []

        def first(self):
            return None

    class _Db:
        def __init__(self):
            self.q = _Filtro()

        def query(self, model):
            return self.q

    usuario = SimpleNamespace(empresa_id="emp-a", id="usr-a", rol=RolUsuario.VENDEDOR)
    db = _Db()
    assert bloque_memoria_cliente_llm(db, usuario, "Ana Pérez") == ""
    assert any("empresa_id" in t for t in db.q.texto)


def test_vendedor_no_ve_clientes_de_otro_rol_en_el_filtro():
    class _Filtro:
        def __init__(self):
            self.texto: list[str] = []

        def filter(self, *args):
            self.texto.extend(str(a) for a in args)
            return self

        def all(self):
            return [Cliente(nombre="Ana Pérez", empresa_id="emp-a", id="cli-a", vendedor_id="usr-a")]

    class _Db:
        def __init__(self):
            self.q = _Filtro()

        def query(self, model):
            return self.q

    from app.services.ai_perfil_empresa import _clientes_visibles

    usuario = SimpleNamespace(empresa_id="emp-a", id="usr-a", rol=RolUsuario.VENDEDOR)
    db = _Db()
    _clientes_visibles(db, usuario)
    texto = " ".join(db.q.texto)
    assert "empresa_id" in texto
    assert "vendedor_id" in texto
