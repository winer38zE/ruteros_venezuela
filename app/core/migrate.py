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
