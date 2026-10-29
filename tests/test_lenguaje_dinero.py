"""Dólares, bolívares, efectivo, transferencia y pago móvil, por voz y por escrito."""
from app.services.ai_voice_confirmacion import construir_resumen_confirmacion
from app.services.ai_voice_session import enriquecer_cobro_desde_turno
from app.services.lenguaje_dinero import frase_cobro
from app.models.core import RolUsuario, Usuario


def test_dolares_no_se_confunden_con_el_metodo():
    args = enriquecer_cobro_desde_turno(
        "cobré 10 dólares en efectivo a Ana",
        {},
    )
    assert args["monto_usd"] == 10
    assert args["moneda"] == "dolar"
    assert args["metodo_pago"] == "efectivo"


def test_bolivares_y_pago_movil():
    args = enriquecer_cobro_desde_turno(
        "me pagó 500 bolívares por pago móvil",
        {"cliente_nombre": "Ana"},
    )
    assert args["moneda"] == "bolivar"
    assert args["metodo_pago"] == "pago_movil"
    assert "usd" not in frase_cobro(500, args["moneda"], args["metodo_pago"]).lower()


def test_confirmacion_escrita_no_dice_usd():
    usuario = Usuario(
        id="usr00000000001",
        empresa_id="emp00000000001",
        nombre="Dueño",
        username="dueno",
        rol=RolUsuario.DUENO,
        password_hash="x",
        activo=True,
    )
    texto, err = construir_resumen_confirmacion(
        None,
        usuario,
        "registrar_cobro",
        {
            "cliente_nombre": "Ana",
            "monto_usd": 10,
            "moneda": "dolar",
            "metodo_pago": "transferencia",
        },
    )
    assert err is None
    assert texto == "Voy a registrar un cobro de 10.00 dólares por transferencia a Ana. ¿Confirmas?"
    assert "USD" not in texto
    assert "pago_movil" not in (texto or "")
