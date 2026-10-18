"""Sembrado del catálogo paises en PocketBase vía ORM."""
from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from app.data.catalogo_paises import CATALOGO_PAISES, PAIS_ISO_POR_DEFECTO
from app.models.core import Pais

logger = logging.getLogger(__name__)


def obtener_pais_por_iso(db: Session, codigo_iso: str) -> Pais | None:
    iso = codigo_iso.strip().upper()
    return db.query(Pais).filter(Pais.codigo_iso == iso).first()


def asegurar_catalogo_paises(db: Session) -> list[Pais]:
    """Inserta o actualiza los 7 países del catálogo."""
    guardados: list[Pais] = []
    for entrada in CATALOGO_PAISES:
        iso = entrada["codigo_iso"]
        existente = obtener_pais_por_iso(db, iso)
        if existente is None:
            existente = Pais(
                nombre=entrada["nombre"],
                codigo_iso=iso,
                moneda_principal=entrada["moneda_principal"],
                simbolo_moneda=entrada["simbolo_moneda"],
                locale=entrada.get("locale"),
                zona_horaria=entrada.get("zona_horaria"),
                activo=entrada.get("activo", True),
                configuracion_bancaria=entrada["configuracion_bancaria"],
                configuracion_fiscal=entrada.get("configuracion_fiscal"),
                configuracion_ui=entrada.get("configuracion_ui"),
            )
            db.add(existente)
        else:
            existente.nombre = entrada["nombre"]
            existente.moneda_principal = entrada["moneda_principal"]
            existente.simbolo_moneda = entrada["simbolo_moneda"]
            existente.locale = entrada.get("locale")
            existente.zona_horaria = entrada.get("zona_horaria")
            existente.activo = entrada.get("activo", True)
            existente.configuracion_bancaria = entrada["configuracion_bancaria"]
            existente.configuracion_fiscal = entrada.get("configuracion_fiscal")
            existente.configuracion_ui = entrada.get("configuracion_ui")
        guardados.append(existente)
    db.flush()
    logger.info("Catálogo paises: %d registro(s) sincronizado(s).", len(guardados))
    return guardados


def pais_por_defecto(db: Session) -> Pais | None:
    return obtener_pais_por_iso(db, PAIS_ISO_POR_DEFECTO)
