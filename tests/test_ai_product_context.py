from app.services.ai_product_context import ContextoProductos


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


def test_bloque_llm_lista_productos():
    ctx = ContextoProductos(nombres=("ventilador", "licuadora"), total=50)
    bloque = ctx.bloque_inventario_llm()
    assert "ventilador" in bloque
    assert "50" in bloque
    assert "Producto no encontrado" in bloque
