"""Verifica que el hash demo quedó persistido en PocketBase (lectura directa GET)."""
from __future__ import annotations

import logging

from pocketbase import PocketBase

from app.api.auth import get_password_hash, obtener_demo_password, verify_password
from app.core.pb_orm import mapper
from app.core.usuario_password_hash import (
    hash_desde_payload_pocketbase,
    nombre_campo_hash_escritura,
    nombre_campo_hash_lectura_login,
    prefijo_bcrypt,
)

logger = logging.getLogger(__name__)

_COLECCION_USUARIOS = "usuarios"


def _leer_hash_en_pocketbase(pb: PocketBase, record_id: str) -> str | None:
    rec = pb.collection(_COLECCION_USUARIOS).get_one(record_id)
    data = mapper.record_payload(rec)
    return hash_desde_payload_pocketbase(data)


def _escribir_hash_directo(pb: PocketBase, record_id: str, hash_bcrypt: str) -> None:
    campo = nombre_campo_hash_escritura()
    pb.collection(_COLECCION_USUARIOS).update(record_id, {campo: hash_bcrypt})


def _log_resultado_verificacion(
    *,
    username: str,
    record_id: str,
    hash_leido: str | None,
    ok: bool,
    reintento: bool,
) -> None:
    campo_esc = nombre_campo_hash_escritura()
    campo_lec = nombre_campo_hash_lectura_login()
    longitud = len(hash_leido or "")
    pref = prefijo_bcrypt(hash_leido)
    etiqueta = "OK" if ok else "FALLO"
    msg = (
        "Verificación hash demo %s — username=%r id=%s campo_escritura=%r campo_lectura_login=%r "
        "hash_longitud=%d hash_bcrypt_prefijo=%r reintento=%s"
    )
    args = (etiqueta, username, record_id, campo_esc, campo_lec, longitud, pref, reintento)
    if ok:
        logger.info(msg, *args)
    else:
        logger.error(msg, *args)


def verificar_hash_demo_usuario(
    pb: PocketBase,
    *,
    username: str,
    record_id: str,
) -> None:
    """
    GET del registro, bcrypt.checkpw(DEMO_PASSWORD, hash_leído).
    Si falla, reescribe el hash una vez vía API admin y vuelve a comprobar.
    """
    clave_demo = obtener_demo_password()
    campo = nombre_campo_hash_escritura()

    def comprobar(reintento: bool) -> bool:
        hash_leido = _leer_hash_en_pocketbase(pb, record_id)
        if not hash_leido:
            _log_resultado_verificacion(
                username=username,
                record_id=record_id,
                hash_leido=hash_leido,
                ok=False,
                reintento=reintento,
            )
            return False
        ok = verify_password(clave_demo, hash_leido)
        _log_resultado_verificacion(
            username=username,
            record_id=record_id,
            hash_leido=hash_leido,
            ok=ok,
            reintento=reintento,
        )
        return ok

    if comprobar(reintento=False):
        return

    logger.error(
        "Reintento de escritura directa de %r para username=%r id=%s",
        campo,
        username,
        record_id,
    )
    _escribir_hash_directo(pb, record_id, get_password_hash(clave_demo))

    if comprobar(reintento=True):
        return

    raise RuntimeError(
        f"El hash demo no persistió en PocketBase para usuario {username!r} (id={record_id}). "
        f"Revisa que el campo {campo!r} exista en la colección usuarios."
    )


def verificar_hashes_usuarios_demo(pb: PocketBase, usuarios: list[tuple[str, str]]) -> None:
    """usuarios: lista de (username, record_id)."""
    for username, record_id in usuarios:
        verificar_hash_demo_usuario(pb, username=username, record_id=record_id)
