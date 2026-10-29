"""Guía de intenciones por palabras clave, sin inventar datos."""
from __future__ import annotations

from app.services.ai_llm_tools import (
    SYSTEM_PROMPT,
    intencion_de_flujo,
    mensaje_si_ambiguo,
)


def test_palabras_clave_eligen_una_intencion():
    assert intencion_de_flujo("le vendí dos sábanas") == "crear_pedido"
    assert intencion_de_flujo("vendí") == "crear_pedido"
    assert intencion_de_flujo("compró arroz") == "crear_pedido"
    assert intencion_de_flujo("cobré diez dólares") == "registrar_cobro"
    assert intencion_de_flujo("me pagó") == "registrar_cobro"
    assert intencion_de_flujo("abonó la deuda") == "registrar_cobro"
    assert intencion_de_flujo("agrega un cliente") == "registrar_cliente"
    assert intencion_de_flujo("nuevo cliente") == "registrar_cliente"


def test_frase_ambigua_ofrece_dos_opciones_sin_inventar():
    msg = mensaje_si_ambiguo("vendí y también cobré")
    assert msg is not None
    assert "venta" in msg
    assert "cobro" in msg
    assert intencion_de_flujo("vendí y también cobré") is None
    assert "10" not in msg
    assert mensaje_si_ambiguo("cuánto hay de") == "¿De qué producto quieres saber cuánto hay?"
    assert "reporte" in (mensaje_si_ambiguo("envíame el reporte") or "")


def test_la_guia_esta_en_el_prompt():
    for frase in ("vendí", "le vendí", "compró", "cobré", "me pagó", "abonó", "cuánto hay de", "me queda", "tengo en inventario", "agrega un cliente", "nuevo cliente", "envíame el reporte"):
        assert frase in SYSTEM_PROMPT
    assert "dos intenciones" in SYSTEM_PROMPT
    assert "Nunca inventes" in SYSTEM_PROMPT
