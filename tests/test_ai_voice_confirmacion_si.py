"""Sí/no de confirmación: variantes, puntuación y un solo reintento."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.models.core import RolUsuario, Usuario
from app.services.ai_voice_confirmacion import (
    MENSAJE_CANCELAR_TRAS_REINTENTO,
    MENSAJE_REPETIR_CONFIRMACION,
    _TTL_SEGUNDOS,
    evaluar_respuesta_confirmacion,
    guardar_pendiente_confirmacion,
    limpiar_confirmacion,
    obtener_pendiente_confirmacion,
)
from app.api.ai import _procesar_confirmacion_pendiente


_SI = (
    "sí",
    "Sí.",
    "SI!",
    "si",
    "dale",
    "confirmo",
    "confirmado",
    "correcto",
    "claro",
    "ok",
    "listo",
    "adelante",
)
_NO = ("no", "No.", "cancela", "cancelar", "déjalo", "olvídalo")


def test_variantes_de_si_y_no():
    for frase in _SI:
        assert evaluar_respuesta_confirmacion(frase) == "confirmar", frase
    for frase in _NO:
        assert evaluar_respuesta_confirmacion(frase) == "rechazar", frase
    assert evaluar_respuesta_confirmacion("tal vez") == "ambiguo"


def test_pendiente_dura_dos_minutos_y_no_se_borra_al_hablar():
    assert _TTL_SEGUNDOS == 120
    uid = "usr-confirm-vivo"
    limpiar_confirmacion(uid)
    guardar_pendiente_confirmacion(
        uid,
        herramienta="registrar_gasto",
        args={"monto": 3},
        resumen="Voy a registrar un gasto de 3.00 dólares. ¿Confirmas?",
        transcripcion_origen="un gasto",
    )
    assert obtener_pendiente_confirmacion(uid) is not None
    assert evaluar_respuesta_confirmacion("Sí.") == "confirmar"
    assert obtener_pendiente_confirmacion(uid) is not None
    limpiar_confirmacion(uid)


def test_segunda_frase_ambigua_cancela_sin_releer_el_resumen():
    uid = "usr-confirm-loop"
    limpiar_confirmacion(uid)
    resumen = "Voy a registrar al cliente Ana con teléfono 04141234567. ¿Confirmas?"
    guardar_pendiente_confirmacion(
        uid,
        herramienta="registrar_cliente",
        args={"nombre": "Ana", "telefono": "04141234567"},
        resumen=resumen,
        transcripcion_origen="registrar cliente Ana",
    )
    usuario = Usuario(
        id=uid,
        empresa_id="emp0000000000001",
        nombre="Dueño",
        username="dueno",
        rol=RolUsuario.DUENO,
        activo=True,
    )
    db = MagicMock()
    with patch("app.api.ai.registrar_orden_voz"):
        primera = _procesar_confirmacion_pendiente(db, usuario, uid, "eh")
    assert primera is not None
    assert primera.mensaje == MENSAJE_REPETIR_CONFIRMACION
    assert "Ana" not in primera.mensaje
    assert obtener_pendiente_confirmacion(uid) is not None

    with patch("app.api.ai.registrar_orden_voz"):
        segunda = _procesar_confirmacion_pendiente(db, usuario, uid, "mmm")
    assert segunda is not None
    assert segunda.mensaje == MENSAJE_CANCELAR_TRAS_REINTENTO
    assert "04141234567" not in segunda.mensaje
    assert obtener_pendiente_confirmacion(uid) is None
