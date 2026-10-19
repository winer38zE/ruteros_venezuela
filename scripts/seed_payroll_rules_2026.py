#!/usr/bin/env python3
"""Semilla idempotente: metadatos de países + payroll_rules 2026."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import POCKETBASE_URL
from app.core.db import get_pocketbase_client
from app.core.pb_orm.session import SessionLocal
from app.core.pb_schema import preparar_esquema_pocketbase
from app.services.paises_seed import asegurar_catalogo_paises
from app.services.payroll_seed import asegurar_payroll_rules_2026

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_payroll_rules_2026")


def main() -> int:
    pb = get_pocketbase_client(POCKETBASE_URL)
    preparar_esquema_pocketbase(pb)
    db = SessionLocal()
    try:
        asegurar_catalogo_paises(db)
        reglas = asegurar_payroll_rules_2026(db)
        db.commit()
        logger.info("Listo: %d regla(s) payroll 2026.", len(reglas))
        return 0
    except Exception:
        db.rollback()
        logger.exception("Fallo seed payroll_rules")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
