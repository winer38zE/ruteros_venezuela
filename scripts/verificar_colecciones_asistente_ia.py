#!/usr/bin/env python3
"""Verifica colecciones PocketBase usadas por POST /api/ai/audio-comando."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import POCKETBASE_URL
from app.core.db import get_pocketbase_client
from app.core.pb_schema import confirmar_acceso_registros, preparar_esquema_pocketbase

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("verificar_ia_pb")

# pedidos de voz → ventas + detalles_venta (no existe colección "pedidos")
COLECCIONES_ASISTENTE = (
    "clientes",
    "productos",
    "ventas",
    "detalles_venta",
    "cobros",
)


def main() -> int:
    logger.info("PocketBase: %s", POCKETBASE_URL)
    pb = get_pocketbase_client(POCKETBASE_URL)
    logger.info("Sincronizando esquema (solo asegura colecciones del ORM)...")
    preparar_esquema_pocketbase(pb)
    logger.info("Comprobando lectura de colecciones del asistente IA...")
    confirmar_acceso_registros(pb, COLECCIONES_ASISTENTE)
    logger.info("OK: %s", ", ".join(COLECCIONES_ASISTENTE))
    logger.info(
        "Nota: los pedidos por voz se guardan en ventas + detalles_venta, no en 'pedidos'."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
