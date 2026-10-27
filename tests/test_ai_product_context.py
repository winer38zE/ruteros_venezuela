from app.services.ai_product_context import ContextoProductos, _extraer_nombre_producto
from app.models.core import Producto
from types import SimpleNamespace


def test_prompt_whisper_dinamico():
    ctx = ContextoProductos(nombres=("sábana", "almohada", "cobija"), total=3)
    prompt = ctx.prompt_whisper()
    assert prompt is not None
    assert "sábana" in prompt
    assert "clientes" in prompt


def test_inventario_vacio():
    ctx = ContextoProductos(nombres=(), total=0)
    assert ctx.vacio
    assert ctx.prompt_whisper() is None


def test_extraer_nombre_desde_orm():
    p = SimpleNamespace(nombre="  Sábana queen  ")
    assert _extraer_nombre_producto(p) == "Sábana queen"
    assert _extraer_nombre_producto(Producto(nombre="arroz", precio_usd=1)) == "arroz"
    assert _extraer_nombre_producto(("ventilador",)) == "ventilador"
    assert _extraer_nombre_producto("licuadora") == "licuadora"


def test_fallo_consulta_no_bloquea_vacio():
    ctx = ContextoProductos(nombres=(), total=0, consulta_ok=False)
    assert not ctx.vacio
    assert ctx.prompt_whisper() is not None


def test_bloque_llm_lista_productos():
    ctx = ContextoProductos(nombres=("ventilador", "licuadora"), total=50)
    bloque = ctx.bloque_inventario_llm()
    assert "ventilador" in bloque
    assert "50" in bloque
    assert "Producto no encontrado" in bloque
