#!/usr/bin/env python3
"""
Repara el campo password_hash en PocketBase y sincroniza usuarios demo.

Uso:
  python scripts/reparar_password_hash_usuarios.py
  python scripts/reparar_password_hash_usuarios.py --username vend --password 123

Requiere ADMIN_EMAIL y ADMIN_PASSWORD en el entorno (o .env).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

load_dotenv()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reparar password_hash en usuarios PocketBase")
    parser.add_argument("--username", help="Opcional: solo este usuario (clave en texto plano con --password)")
    parser.add_argument("--password", help="Nueva clave si usas --username")
    args = parser.parse_args()

    from sqlalchemy import func

    from app.api.auth import get_password_hash
    from app.core.bootstrap import asegurar_usuario_admin
    from app.core.config import POCKETBASE_URL
    from app.core.db import autenticar_admin_pocketbase, get_pocketbase_client
    from app.core.demo_hash_verificacion import verificar_hash_demo_usuario
    from app.core.pb_orm import mapper
    from app.core.pb_schema import preparar_esquema_pocketbase
    from app.core.pb_orm.session import SessionLocal
    from app.core.usuario_password_hash import hash_desde_modelo_usuario
    from app.models.core import Usuario

    print(f"PocketBase: {POCKETBASE_URL}")
    pb = get_pocketbase_client()
    autenticar_admin_pocketbase(pb)
    print("Esquema (campo password_hash)...")
    preparar_esquema_pocketbase(pb)

    if args.username:
        username = args.username.strip().lower()
        if not args.password:
            print("Error: --password es obligatorio con --username", file=sys.stderr)
            return 1
        db = SessionLocal()
        try:
            u = (
                db.query(Usuario)
                .filter(func.lower(Usuario.username) == username)
                .first()
            )
            if not u:
                print(f"No se encontró usuario {username!r}", file=sys.stderr)
                return 1
            u.password_hash = get_password_hash(args.password)
            db.commit()
            rid = mapper.record_id(u)
            verificar_hash_demo_usuario(pb, username=username, record_id=rid)
            print(f"OK: hash actualizado para {username!r} (id={rid})")
        finally:
            db.close()
        return 0

    print("Bootstrap demo (dueno, admin, vendedor, cobrador)...")
    asegurar_usuario_admin()

    db = SessionLocal()
    try:
        vacios = []
        for u in db.query(Usuario).all():
            if not hash_desde_modelo_usuario(u).strip():
                vacios.append(str(u.username))
        if vacios:
            print(
                "AVISO: usuarios sin hash tras bootstrap:",
                ", ".join(vacios),
                file=sys.stderr,
            )
            print(
                "Repara uno con: python scripts/reparar_password_hash_usuarios.py "
                "--username NOMBRE --password CLAVE",
                file=sys.stderr,
            )
            return 1
    finally:
        db.close()

    print("OK: esquema y usuarios demo con password_hash válido.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
