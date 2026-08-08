"""Migraciones ligeras para SQLite (añade columnas nuevas sin borrar datos)."""
from sqlalchemy import inspect, text


def _columnas_existentes(engine, tabla: str) -> set[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info({tabla})")).fetchall()
    return {row[1] for row in rows}


def aplicar_migraciones_sqlite(engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    insp = inspect(engine)
    alteraciones: dict[str, list[tuple[str, str]]] = {
        "clientes": [
            ("tipo_cliente", "VARCHAR(20) DEFAULT 'detal'"),
            ("identificacion", "VARCHAR(32)"),
            ("telefono_secundario", "VARCHAR(32)"),
            ("punto_referencia", "VARCHAR(255)"),
            ("empresa_trabajo", "VARCHAR(255)"),
            ("direccion_laboral", "TEXT"),
            ("ref_familiar_nombre", "VARCHAR(255)"),
            ("ref_familiar_parentesco", "VARCHAR(64)"),
            ("ref_familiar_telefono", "VARCHAR(32)"),
            ("email", "VARCHAR(255)"),
            ("score_credito", "INTEGER DEFAULT 70"),
        ],
        "movimientos_financieros": [
            ("monto_original", "NUMERIC(14, 2)"),
            ("moneda", "VARCHAR(10) DEFAULT 'usd'"),
            ("metodo_pago", "VARCHAR(20)"),
            ("tasa_aplicada", "NUMERIC(12, 4)"),
            ("proveedor_id", "CHAR(36)"),
            ("comprobante_base64", "TEXT"),
        ],
        "productos": [
            ("sku", "VARCHAR(64)"),
            ("precio_ves", "NUMERIC(14, 2)"),
            ("precio_cop", "NUMERIC(14, 2)"),
            ("costo_usd", "NUMERIC(10, 2) DEFAULT 0"),
            ("stock_minimo", "INTEGER DEFAULT 0"),
            ("proveedor_id", "CHAR(36)"),
        ],
        "tasas_cambio": [
            ("usd_bcv_bs", "NUMERIC(12, 4)"),
            ("usd_paralelo_bs", "NUMERIC(12, 4)"),
            ("cop_usd", "NUMERIC(12, 4)"),
            ("cop_ves", "NUMERIC(14, 4)"),
        ],
        "ventas": [
            ("tipo_tasa_usd", "VARCHAR(20) DEFAULT 'bcv'"),
            ("numero_cuotas", "INTEGER"),
        ],
        "proveedores": [
            ("saldo_deuda_usd", "NUMERIC(12, 2) DEFAULT 0"),
        ],
        "lotes_inventario": [
            ("proveedor_id", "CHAR(36)"),
            ("genera_deuda_proveedor", "BOOLEAN DEFAULT 0"),
        ],
    }

    with engine.begin() as conn:
        for tabla, columnas in alteraciones.items():
            if not insp.has_table(tabla):
                continue
            existentes = _columnas_existentes(engine, tabla)
            for nombre, definicion in columnas:
                if nombre not in existentes:
                    conn.execute(
                        text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}")
                    )

        if insp.has_table("clientes"):
            conn.execute(
                text(
                    "UPDATE clientes SET identificacion = 'TMP-' || id "
                    "WHERE identificacion IS NULL OR identificacion = ''"
                )
            )
            conn.execute(
                text(
                    "UPDATE clientes SET score_credito = 70 "
                    "WHERE score_credito IS NULL"
                )
            )
