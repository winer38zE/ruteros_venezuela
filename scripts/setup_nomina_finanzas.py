#!/usr/bin/env python3
"""
Fase 1 — Nómina multiregión: esquema PocketBase + parámetros por país.

Conecta como administrador PocketBase (ADMIN_EMAIL / ADMIN_PASSWORD) y:

1. Amplía la colección `paises` con:
   sueldo_base_legal, porcentaje_comision_venta, porcentaje_comision_cobro, bono_incentivo.

2. Crea o verifica `pagos_nomina` (ORM Ruteros: usuario_id = empleado, montos en
   sueldo_base_usd / comision_usd / total_calculado_usd, estado pendiente|realizado).

3. Crea o verifica `movimientos_financieros` (tipo entrada|salida, categoría, monto, pais_id).

Uso local o vía SSH en el VPS (desde la raíz del repo, con .env o variables exportadas):

    python scripts/setup_nomina_finanzas.py

Requisitos previos: catálogo de países (`python scripts/seed_paises.py`).
"""
from __future__ import annotations

import logging
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import POCKETBASE_URL
from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
from app.core.pb_orm.session import SessionLocal
from app.core.pb_schema import (
    colecciones_faltantes,
    preparar_esquema_pocketbase,
    verificar_colecciones_completas,
)
from app.data.nomina_paises_defaults import NOMINA_POR_ISO
from app.models.core import Pais
from app.services.paises_seed import asegurar_catalogo_paises

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("setup_nomina_finanzas")

_COLECCIONES_NOMINA = ("paises", "pagos_nomina", "movimientos_financieros")


def _d(val) -> Decimal:
    return Decimal(str(val or 0))


def _pais_sin_parametros(pais: Pais) -> bool:
    return (
        _d(pais.sueldo_base_legal) == 0
        and _d(pais.porcentaje_comision_venta) == 0
        and _d(pais.porcentaje_comision_cobro) == 0
        and _d(pais.bono_incentivo) == 0
    )


def aplicar_defaults_nomina_paises(db) -> int:
    """Rellena parámetros de nómina solo en países que aún están en cero."""
    actualizados = 0
    for pais in db.query(Pais).order_by(Pais.codigo_iso).all():
        defaults = NOMINA_POR_ISO.get(pais.codigo_iso.upper())
        if defaults is None:
            logger.warning(
                "  %s (%s): sin defaults en nomina_paises_defaults; déjalo en cero o edítalo en PB.",
                pais.nombre,
                pais.codigo_iso,
            )
            continue
        if not _pais_sin_parametros(pais):
            logger.info(
                "  %s (%s): ya tiene parámetros (sueldo=%s); no se sobrescribe.",
                pais.nombre,
                pais.codigo_iso,
                pais.sueldo_base_legal,
            )
            continue
        pais.sueldo_base_legal = defaults["sueldo_base_legal"]
        pais.porcentaje_comision_venta = defaults["porcentaje_comision_venta"]
        pais.porcentaje_comision_cobro = defaults["porcentaje_comision_cobro"]
        pais.bono_incentivo = defaults["bono_incentivo"]
        actualizados += 1
        logger.info(
            "  %s (%s): sueldo=%s %s, com. venta=%s%%, com. cobro=%s%%, bono=%s",
            pais.nombre,
            pais.codigo_iso,
            pais.sueldo_base_legal,
            pais.moneda_principal,
            pais.porcentaje_comision_venta,
            pais.porcentaje_comision_cobro,
            pais.bono_incentivo,
        )
    return actualizados


def _verificar_colecciones_nomina(pb) -> None:
    faltantes = [c for c in _COLECCIONES_NOMINA if c in colecciones_faltantes(pb)]
    if faltantes:
        raise RuntimeError(
            "Tras sincronizar el esquema siguen faltando colecciones de nómina: "
            + ", ".join(faltantes)
        )
    for nombre in _COLECCIONES_NOMINA:
        pb.collection(nombre).get_list(1, 1)
        logger.info("Colección '%s' accesible.", nombre)


def main() -> int:
    url = POCKETBASE_URL
    logger.info("PocketBase: %s", url)
    pb = get_pocketbase_client(url)
    autenticar_admin_pocketbase(pb)
    logger.info("Sesión administrador OK.")

    logger.info("Sincronizando esquema (paises, pagos_nomina, movimientos_financieros)...")
    preparar_esquema_pocketbase(pb)
    verificar_colecciones_completas(pb)
    _verificar_colecciones_nomina(pb)

    db = SessionLocal()
    try:
        asegurar_catalogo_paises(db)
        n = aplicar_defaults_nomina_paises(db)
        db.commit()
        logger.info(
            "Listo: %d país(es) con defaults de nómina 2026. "
            "Colección movimientos_financieros lista para egresos de 'Pago Nómina'.",
            n,
        )
        return 0
    except Exception:
        db.rollback()
        logger.exception("Fallo al aplicar parámetros de nómina en paises")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
