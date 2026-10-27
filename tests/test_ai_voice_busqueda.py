"""Búsqueda de cliente/producto para asistente de voz."""
from __future__ import annotations

from types import SimpleNamespace

from app.services.ai_voice_executor import (
    _elegir_cliente_entre_candidatos,
    _elegir_producto_entre_candidatos,
    _fold_texto,
)


def _cliente(nombre: str) -> SimpleNamespace:
    return SimpleNamespace(nombre=nombre)


def _producto(nombre: str) -> SimpleNamespace:
    return SimpleNamespace(nombre=nombre)


def test_fold_texto_ignora_mayusculas_y_acentos():
    assert _fold_texto("María") == _fold_texto("maria")
    assert _fold_texto("  Arroz  ") == "arroz"


def test_cliente_unico_por_nombre_parcial():
    candidatos = [_cliente("María Pérez"), _cliente("José García")]
    elegido, err = _elegir_cliente_entre_candidatos(candidatos, "María Pérez")
    assert err is None
    assert elegido.nombre == "María Pérez"


def test_cliente_ambiguo_mismo_nombre():
    candidatos = [_cliente("María"), _cliente("María")]
    elegido, err = _elegir_cliente_entre_candidatos(candidatos, "María")
    assert elegido is None
    assert err is not None
    assert "varios clientes" in err.lower()


def test_cliente_no_encontrado_mensaje_amigable():
    elegido, err = _elegir_cliente_entre_candidatos([], "María")
    assert elegido is None
    assert "no encontré" in err.lower()
    assert "registrarlo" in err.lower()


def test_producto_exacto_case_insensitive():
    candidatos = [_producto("Arroz Premium"), _producto("Arroz Integral")]
    elegido, err = _elegir_producto_entre_candidatos(candidatos, "arroz premium")
    assert err is None
    assert elegido.nombre == "Arroz Premium"


def test_producto_no_encontrado():
    elegido, err = _elegir_producto_entre_candidatos([], "Harina")
    assert elegido is None
    assert "no encontré" in err.lower()
