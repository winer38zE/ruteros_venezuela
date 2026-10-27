"""Memoria de turnos del asistente de voz."""
from __future__ import annotations

from app.services.ai_voice_session import (
    campos_faltantes_registrar_cliente,
    enriquecer_args_desde_turno,
    fusionar_args,
    guardar,
    historial_mensajes_para_llm,
    limpiar,
    mensaje_pendiente_registrar_cliente,
    preparar_ejecucion,
    registrar_intercambio,
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
