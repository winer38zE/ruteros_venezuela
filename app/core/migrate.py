"""Migraciones ligeras para SQLite (añade columnas nuevas sin borrar datos)."""
import unicodedata

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
            ("total_compras", "INTEGER DEFAULT 0"),
            ("monto_compras_usd", "NUMERIC(12, 2) DEFAULT 0"),
            ("total_pagos", "INTEGER DEFAULT 0"),
            ("monto_pagos_usd", "NUMERIC(12, 2) DEFAULT 0"),
            ("estado_morosidad", "VARCHAR(20) DEFAULT 'al_dia'"),
            ("clasificacion_credito", "VARCHAR(40) DEFAULT 'Bueno'"),
            ("latitud_residencia", "NUMERIC(10, 7)"),
            ("longitud_residencia", "NUMERIC(10, 7)"),
            ("latitud_trabajo", "NUMERIC(10, 7)"),
            ("longitud_trabajo", "NUMERIC(10, 7)"),
            ("dia_visita", "VARCHAR(20)"),
            ("orden_secuencial", "INTEGER"),
            ("dia_ruta", "VARCHAR(20)"),
            ("orden_ruta", "INTEGER"),
            ("tipo_visita_ruta", "VARCHAR(20) DEFAULT 'frecuente'"),
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
            ("activa", "BOOLEAN DEFAULT 1"),
            ("origen", "VARCHAR(20) DEFAULT 'manual'"),
        ],
        "empresas": [
            ("banco", "VARCHAR(120)"),
            ("tipo_cuenta", "VARCHAR(40)"),
            ("numero_cuenta", "VARCHAR(64)"),
            ("cedula_nit", "VARCHAR(32)"),
        ],
        "ventas": [
            ("tipo_tasa_usd", "VARCHAR(20) DEFAULT 'bcv'"),
            ("numero_cuotas", "INTEGER"),
            ("metodo_pago", "VARCHAR(20) DEFAULT 'efectivo'"),
            ("referencia_pago", "VARCHAR(80)"),
            ("comprobante_base64", "TEXT"),
        ],
        "cobros": [
            ("es_transferencia", "BOOLEAN DEFAULT 0"),
            ("verificado", "BOOLEAN DEFAULT 1"),
            ("referencia_pago", "VARCHAR(80)"),
            ("comprobante_base64", "TEXT"),
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
            _rellenar_dia_y_orden_ruta(conn)


def _clave_dia(valor: str) -> str:
    texto = unicodedata.normalize("NFD", valor.strip())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn").upper()


_ETIQUETA_POR_CLAVE = {
    "LUNES": "Lunes",
    "MARTES": "Martes",
    "MIERCOLES": "Miércoles",
    "JUEVES": "Jueves",
    "VIERNES": "Viernes",
    "SABADO": "Sábado",
    "DOMINGO": "Domingo",
}


def _rellenar_dia_y_orden_ruta(conn) -> None:
    """Copia dia_visita/orden_secuencial hacia dia_ruta/orden_ruta si faltan."""
    columnas = {row[1] for row in conn.execute(text("PRAGMA table_info(clientes)")).fetchall()}
    if "dia_ruta" not in columnas or "orden_ruta" not in columnas:
        return

    filas = conn.execute(
        text(
            "SELECT id, dia_visita, orden_secuencial, dia_ruta, orden_ruta FROM clientes"
        )
    ).fetchall()
    for fila in filas:
        cliente_id, dia_visita, orden_sec, dia_ruta, orden_ruta = fila
        nuevo_dia = dia_ruta
        nuevo_orden = orden_ruta
        if not nuevo_dia and dia_visita:
            nuevo_dia = _ETIQUETA_POR_CLAVE.get(_clave_dia(str(dia_visita)))
        if nuevo_orden is None and orden_sec is not None:
            nuevo_orden = orden_sec
        if nuevo_dia == dia_ruta and nuevo_orden == orden_ruta:
            continue
        conn.execute(
            text(
                "UPDATE clientes SET dia_ruta = :dia, orden_ruta = :orden WHERE id = :id"
            ),
            {"dia": nuevo_dia, "orden": nuevo_orden, "id": cliente_id},
        )
