#!/usr/bin/env python3
"""Crea/actualiza la colección paises y los 7 países del catálogo Ruteros."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.db import get_pocketbase_client
from app.core.config import POCKETBASE_URL
from app.core.pb_orm.session import SessionLocal
from app.core.pb_schema import preparar_esquema_pocketbase, verificar_colecciones_completas
from app.services.paises_seed import asegurar_catalogo_paises

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_paises")


def main() -> int:
    pb = get_pocketbase_client(POCKETBASE_URL)
    logger.info("Sincronizando esquema PocketBase (incluye paises + pais_id)...")
    preparar_esquema_pocketbase(pb)
    verificar_colecciones_completas(pb)

    db = SessionLocal()
    try:
        paises = asegurar_catalogo_paises(db)
        db.commit()
        for p in paises:
            logger.info("  %s (%s) — %s %s", p.nombre, p.codigo_iso, p.simbolo_moneda, p.moneda_principal)
        logger.info("Listo: %d país(es) en PocketBase.", len(paises))
        return 0
    except Exception:
        db.rollback()
        logger.exception("Fallo al sembrar paises")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
