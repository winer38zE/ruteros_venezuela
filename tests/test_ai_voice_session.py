"""Memoria de turnos del asistente de voz."""
from __future__ import annotations

from app.services.ai_voice_session import (
    transcripcion_debe_rechazarse,
    _transcripcion_parece_eco_asistente,
    campos_faltantes_registrar_cliente,
    enriquecer_args_desde_turno,
    fusionar_args,
    guardar,
    historial_mensajes_para_llm,
    limpiar,
    mensaje_pendiente_registrar_cliente,
    preparar_ejecucion,
    registrar_intercambio,
    _es_nombre_cliente_valido,
)


def test_fusionar_no_borra_datos_previos():
    base = {"nombre": "Edwuar"}
    nuevos = {"telefono": "04141234567"}
    merged = fusionar_args(base, nuevos)
    assert merged["nombre"] == "Edwuar"
    assert merged["telefono"] == "04141234567"


def test_turnos_registrar_cliente_multiples_audios():
    uid = "usr-test-1"
    limpiar(uid)
    h, args, msg, listo = preparar_ejecucion(uid, None, {}, "Registrar cliente", None)
    assert listo is False
    assert "nombre" in msg.lower()

    guardar(uid, "registrar_cliente", {}, "Registrar cliente")
    h, args, msg, listo = preparar_ejecucion(uid, None, {}, "Edwuar", None)
    assert listo is False
    assert args.get("nombre") == "Edwuar"
    assert "teléfono" in msg.lower()

    h, args, msg, listo = preparar_ejecucion(uid, "registrar_cliente", {}, "04141234567", None)
    assert listo is True
    assert args["nombre"] == "Edwuar"
    assert "04141234567" in str(args["telefono"])
    limpiar(uid)


def test_un_solo_comando_con_todos_los_campos():
    uid = "usr-test-2"
    limpiar(uid)
    texto = "Registrar cliente Edwuar teléfono 04141234567 dirección Calle 123"
    merged = enriquecer_args_desde_turno("registrar_cliente", texto, {})
    assert campos_faltantes_registrar_cliente(merged) == []
    assert merged["nombre"] == "Edwuar"
    assert "04141234567" in merged["telefono"]
    assert "Calle" in merged["direccion"]


def test_mensaje_no_repite_nombre():
    msg = mensaje_pendiente_registrar_cliente({"nombre": "Edwuar"})
    assert "Edwuar" in msg
    assert "teléfono" in msg.lower()
    assert "nombre del cliente" not in msg.lower()


def test_solo_telefono_con_sesion_activa_no_pierde_nombre():
    uid = "usr-test-3"
    limpiar(uid)
    h, args, msg, listo = preparar_ejecucion(
        uid,
        None,
        {},
        "Registrar cliente Edwuar Cárdenas",
        "¿Cuál es el teléfono?",
    )
    assert listo is False
    assert args.get("nombre") == "Edwuar Cárdenas"

    registrar_intercambio(
        uid,
        intent="registrar_cliente",
        partial=args,
        transcripcion_usuario="Registrar cliente Edwuar Cárdenas",
        respuesta_asistente=msg,
    )
    h, args, msg, listo = preparar_ejecucion(
        uid,
        None,
        {},
        "04141234567",
        "¿Qué deseas hacer?",
    )
    assert listo is True
    assert args["nombre"] == "Edwuar Cárdenas"
    assert "04141234567" in str(args["telefono"])
    limpiar(uid)


def test_eco_tts_no_se_toma_como_nombre():
    eco = "Nombre aplauso anotado cuál es el teléfono del cliente"
    assert _transcripcion_parece_eco_asistente(eco)
    assert transcripcion_debe_rechazarse(eco)
    merged = enriquecer_args_desde_turno("registrar_cliente", eco, {})
    assert not merged.get("nombre")


def test_aplauso_no_se_toma_como_nombre():
    assert not _es_nombre_cliente_valido("aplauso")
    merged = enriquecer_args_desde_turno("registrar_cliente", "aplauso", {})
    assert not merged.get("nombre")


def test_ruido_con_nombre_pendiente_pide_telefono_claro():
    uid = "usr-test-aplauso"
    limpiar(uid)
    registrar_intercambio(
        uid,
        intent="registrar_cliente",
        partial={"nombre": "María"},
        transcripcion_usuario="Registrar cliente María",
        respuesta_asistente="¿Teléfono?",
    )
    _, args, msg, listo = preparar_ejecucion(uid, None, {}, "aplauso", None)
    assert listo is False
    assert args.get("nombre") == "María"
    assert "teléfono" in msg.lower()
    assert "aplauso" not in msg.lower()
    limpiar(uid)


def test_sesion_registro_cede_a_pedido():
    uid = "usr-test-pedido"
    limpiar(uid)
    preparar_ejecucion(uid, None, {}, "Registrar cliente Pedro", None)
    h, args, msg, listo = preparar_ejecucion(
        uid,
        "crear_pedido",
        {"cliente_nombre": "Ana", "productos": [{"nombre": "arroz", "cantidad": 1}]},
        "Pedido para Ana arroz uno",
        None,
    )
    assert listo is True
    assert h == "crear_pedido"
    limpiar(uid)


def test_turnos_crear_pedido_multiples_audios():
    uid = "usr-test-pedido-mt"
    limpiar(uid)
    h, args, msg, listo = preparar_ejecucion(
        uid, "crear_pedido", {}, "Quiero hacer una venta", None
    )
    assert listo is False
    assert "cliente" in msg.lower()

    h, args, msg, listo = preparar_ejecucion(
        uid, None, {}, "Cliente Pedro", None
    )
    assert listo is False
    assert args.get("cliente_nombre") == "Pedro"
    assert "producto" in msg.lower()

    h, args, msg, listo = preparar_ejecucion(
        uid,
        "crear_pedido",
        {"productos": [{"nombre": "arroz", "cantidad": 2}]},
        "2 arroz",
        None,
    )
    assert listo is True
    assert args["cliente_nombre"] == "Pedro"
    assert args["productos"][0]["nombre"] == "arroz"
    limpiar(uid)


def test_turnos_registrar_cobro_multiples_audios():
    uid = "usr-test-cobro-mt"
    limpiar(uid)
    h, args, msg, listo = preparar_ejecucion(
        uid, "registrar_cobro", {}, "Registrar un cobro", None
    )
    assert listo is False
    assert "cliente" in msg.lower()

    h, args, msg, listo = preparar_ejecucion(uid, None, {}, "de Luis", None)
    assert listo is False
    assert args.get("cliente_nombre") == "Luis"
    assert "dólar" in msg.lower() or "monto" in msg.lower()

    h, args, msg, listo = preparar_ejecucion(
        uid,
        "registrar_cobro",
        {"monto_usd": 50, "metodo_pago": "efectivo"},
        "50 dólares en efectivo",
        None,
    )
    assert listo is True
    assert args["cliente_nombre"] == "Luis"
    assert args["monto_usd"] == 50
    limpiar(uid)


def test_historial_mensajes_para_groq():
    uid = "usr-test-4"
    limpiar(uid)
    registrar_intercambio(
        uid,
        intent="registrar_cliente",
        partial={"nombre": "Edwuar"},
        transcripcion_usuario="Registrar cliente Edwuar",
        respuesta_asistente="¿Cuál es el teléfono?",
    )
    hist = historial_mensajes_para_llm(uid)
    assert len(hist) == 2
    assert hist[0]["role"] == "user"
    assert hist[1]["role"] == "assistant"
    limpiar(uid)
