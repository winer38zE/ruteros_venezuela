#!/usr/bin/env python3
"""
Actualiza configuracion_bancaria en la colección `paises` (PocketBase vía ORM admin).

Uso (desde la raíz del repo, con ADMIN_EMAIL / ADMIN_PASSWORD en el entorno):

    python scripts/actualizar_bancos.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import POCKETBASE_URL
from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
from app.core.pb_orm.session import SessionLocal
from app.data.bancos_catalogo import BANCOS_POR_ISO, fusionar_configuracion_bancaria
from app.models.core import Pais
from app.services.paises_seed import obtener_pais_por_iso

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("actualizar_bancos")


def main() -> int:
    pb = get_pocketbase_client(POCKETBASE_URL)
    autenticar_admin_pocketbase(pb)
    logger.info("Sesión admin PocketBase OK (%s)", POCKETBASE_URL)

    db = SessionLocal()
    try:
        actualizados = 0
        for iso in BANCOS_POR_ISO:
            pais = obtener_pais_por_iso(db, iso)
            if pais is None:
                logger.warning("País %s no existe en PocketBase; ejecuta seed_paises.py primero.", iso)
                continue
            nueva = fusionar_configuracion_bancaria(pais.configuracion_bancaria, iso)
            pais.configuracion_bancaria = nueva
            actualizados += 1
            logger.info(
                "  %s (%s): %d banco(s), docs %s",
                pais.nombre,
                iso,
                len(nueva["bancos"]),
                ", ".join(nueva["documentos_legales"]),
            )
        db.commit()
        logger.info("Listo: %d país(es) actualizado(s).", actualizados)
        return 0 if actualizados else 1
    except Exception:
        db.rollback()
        logger.exception("Fallo al actualizar bancos")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
