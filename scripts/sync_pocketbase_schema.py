#!/usr/bin/env python3
"""Sincroniza colecciones PocketBase con los modelos SQLAlchemy de Ruteros."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import POCKETBASE_URL
from app.core.db import get_pocketbase_client
from app.core.pb_schema import (
    colecciones_faltantes,
    nombres_colecciones_requeridas,
    preparar_esquema_pocketbase,
    verificar_colecciones_completas,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("sync_pb_schema")


def main() -> int:
    url = POCKETBASE_URL
    logger.info("PocketBase: %s", url)
    pb = get_pocketbase_client(url)
    antes = colecciones_faltantes(pb)
    if antes:
        logger.info("Colecciones faltantes (%d): %s", len(antes), ", ".join(antes))
    else:
        logger.info("Todas las colecciones requeridas existen (%d).", len(nombres_colecciones_requeridas()))

    preparar_esquema_pocketbase(pb)
    verificar_colecciones_completas(pb)

    despues = colecciones_faltantes(pb)
    if despues:
        logger.error("Siguen faltando: %s", ", ".join(despues))
        return 1

    logger.info("Esquema PocketBase sincronizado correctamente.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
