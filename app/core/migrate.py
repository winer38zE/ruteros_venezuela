"""Migraciones ligeras para SQLite (añade columnas nuevas sin borrar datos)."""
import unicodedata
import uuid

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
            ("pais_id", "CHAR(36)"),
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
            ("pais_id", "CHAR(36)"),
        ],
        "ventas": [
            ("tipo_tasa_usd", "VARCHAR(20) DEFAULT 'bcv'"),
            ("numero_cuotas", "INTEGER"),
            ("metodo_pago", "VARCHAR(20) DEFAULT 'efectivo'"),
            ("referencia_pago", "VARCHAR(80)"),
            ("comprobante_base64", "TEXT"),
            ("cuenta_bancaria_id", "CHAR(36)"),
        ],
        "cobros": [
            ("es_transferencia", "BOOLEAN DEFAULT 0"),
            ("verificado", "BOOLEAN DEFAULT 1"),
            ("referencia_pago", "VARCHAR(80)"),
            ("comprobante_base64", "TEXT"),
            ("cuenta_bancaria_id", "CHAR(36)"),
        ],
        "proveedores": [
            ("saldo_deuda_usd", "NUMERIC(12, 2) DEFAULT 0"),
        ],
        "lotes_inventario": [
            ("proveedor_id", "CHAR(36)"),
            ("genera_deuda_proveedor", "BOOLEAN DEFAULT 0"),
            ("pais_id", "CHAR(36)"),
        ],
        "usuarios": [
            ("sueldo_base_usd", "NUMERIC(10, 2) DEFAULT 0"),
            ("pais_id", "CHAR(36)"),
        ],
        "configuracion_nomina": [
            ("comision_vendedor_por_venta_usd", "NUMERIC(10, 2) DEFAULT 10"),
            ("dias_periodo_nomina", "INTEGER DEFAULT 8"),
            ("fecha_ancla_periodo", "DATE"),
        ],
        "cuentas_bancarias": [
            ("pais_id", "CHAR(36)"),
        ],
        "cuentas_bancarias_empleados": [
            ("pais_id", "CHAR(36)"),
        ],
        "almacenes": [
            ("pais_id", "CHAR(36)"),
        ],
        "movimientos_inventario": [
            ("pais_id", "CHAR(36)"),
        ],
        "tasas_cambio": [
            ("pais_id", "CHAR(36)"),
        ],
        "movimientos_financieros": [
            ("pais_id", "CHAR(36)"),
        ],
        "pagos_nomina": [
            ("pais_id", "CHAR(36)"),
        ],
        "paises": [
            ("sueldo_base_legal", "NUMERIC(14, 2) NOT NULL DEFAULT 0"),
            ("porcentaje_comision_venta", "NUMERIC(5, 2) NOT NULL DEFAULT 0"),
            ("porcentaje_comision_cobro", "NUMERIC(5, 2) NOT NULL DEFAULT 0"),
            ("bono_incentivo", "NUMERIC(14, 2) NOT NULL DEFAULT 0"),
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

        _asegurar_tabla_cuentas_bancarias(conn)
        _ampliar_cuentas_bancarias(conn)
        if _tabla_sqlite(conn, "empresas") and _tabla_sqlite(conn, "cuentas_bancarias"):
            _sembrar_cuentas_bancarias(conn)

        _asegurar_tabla_cuentas_bancarias_empleados(conn)
        _asegurar_tabla_pagos_nomina(conn)
        _asegurar_tabla_paises(conn)


def _tabla_sqlite(conn, nombre: str) -> bool:
    fila = conn.execute(
        text("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = :nombre"),
        {"nombre": nombre},
    ).first()
    return fila is not None


def _asegurar_tabla_cuentas_bancarias(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS cuentas_bancarias (
                id CHAR(36) PRIMARY KEY,
                empresa_id CHAR(36) NOT NULL,
                banco VARCHAR(120) NOT NULL,
                tipo_cuenta VARCHAR(40) NOT NULL,
                numero_cuenta VARCHAR(64) NOT NULL,
                titular VARCHAR(160) NOT NULL,
                documento VARCHAR(32) NOT NULL,
                canal VARCHAR(20) NOT NULL DEFAULT 'transferencia',
                telefono VARCHAR(20),
                activa BOOLEAN NOT NULL DEFAULT 1,
                fecha_creacion DATETIME
            )
            """
        )
    )


def _ampliar_cuentas_bancarias(conn) -> None:
    if not _tabla_sqlite(conn, "cuentas_bancarias"):
        return
    existentes = {
        fila[1]
        for fila in conn.execute(text("PRAGMA table_info(cuentas_bancarias)")).fetchall()
    }
    if "canal" not in existentes:
        conn.execute(
            text(
                "ALTER TABLE cuentas_bancarias "
                "ADD COLUMN canal VARCHAR(20) DEFAULT 'transferencia'"
            )
        )
    if "telefono" not in existentes:
        conn.execute(text("ALTER TABLE cuentas_bancarias ADD COLUMN telefono VARCHAR(20)"))
    conn.execute(
        text(
            "UPDATE cuentas_bancarias SET canal = 'transferencia' "
            "WHERE canal IS NULL OR canal = ''"
        )
    )


def _sembrar_cuentas_bancarias(conn) -> None:
    columnas = {
        fila[1]
        for fila in conn.execute(text("PRAGMA table_info(empresas)")).fetchall()
    }
    if "numero_cuenta" not in columnas:
        return
    empresas = conn.execute(
        text(
            "SELECT id, nombre, banco, tipo_cuenta, numero_cuenta, cedula_nit FROM empresas"
        )
    ).fetchall()
    for empresa_id, nombre, banco, tipo, numero, documento in empresas:
        numero_limpio = (numero or "").strip()
        if not numero_limpio:
            continue
        ya = conn.execute(
            text("SELECT 1 FROM cuentas_bancarias WHERE empresa_id = :empresa_id LIMIT 1"),
            {"empresa_id": str(empresa_id)},
        ).first()
        if ya:
            continue
        conn.execute(
            text(
                """
                INSERT INTO cuentas_bancarias (
                    id, empresa_id, banco, tipo_cuenta, numero_cuenta,
                    titular, documento, canal, activa
                ) VALUES (
                    :id, :empresa_id, :banco, :tipo_cuenta, :numero_cuenta,
                    :titular, :documento, 'transferencia', 1
                )
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "empresa_id": str(empresa_id),
                "banco": (banco or "Banco").strip() or "Banco",
                "tipo_cuenta": (tipo or "Ahorro").strip() or "Ahorro",
                "numero_cuenta": numero_limpio,
                "titular": (nombre or "Titular").strip() or "Titular",
                "documento": (documento or "Sin documento").strip() or "Sin documento",
            },
        )


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


def _asegurar_tabla_paises(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS paises (
                id CHAR(36) PRIMARY KEY,
                nombre VARCHAR(80) NOT NULL,
                codigo_iso VARCHAR(3) NOT NULL UNIQUE,
                moneda_principal VARCHAR(3) NOT NULL,
                simbolo_moneda VARCHAR(8) NOT NULL,
                locale VARCHAR(10),
                zona_horaria VARCHAR(40),
                activo BOOLEAN NOT NULL DEFAULT 1,
                configuracion_bancaria TEXT NOT NULL,
                configuracion_fiscal TEXT,
                configuracion_ui TEXT,
                fecha_creacion DATETIME
            )
            """
        )
    )


def _asegurar_tabla_cuentas_bancarias_empleados(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS cuentas_bancarias_empleados (
                id CHAR(36) PRIMARY KEY,
                empresa_id CHAR(36) NOT NULL,
                usuario_id CHAR(36) NOT NULL UNIQUE,
                banco VARCHAR(120) NOT NULL,
                tipo_cuenta VARCHAR(40) NOT NULL,
                numero_cuenta VARCHAR(64),
                titular VARCHAR(160) NOT NULL,
                documento_identidad VARCHAR(32) NOT NULL,
                canal VARCHAR(20) NOT NULL DEFAULT 'transferencia',
                telefono_pago_movil VARCHAR(20),
                activa BOOLEAN NOT NULL DEFAULT 1,
                verificada_por_dueno BOOLEAN NOT NULL DEFAULT 0,
                fecha_actualizacion DATETIME,
                fecha_creacion DATETIME
            )
            """
        )
    )


def _asegurar_tabla_pagos_nomina(conn) -> None:
    conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS pagos_nomina (
                id CHAR(36) PRIMARY KEY,
                empresa_id CHAR(36) NOT NULL,
                usuario_id CHAR(36) NOT NULL,
                rol VARCHAR(20) NOT NULL,
                periodo_desde DATE NOT NULL,
                periodo_hasta DATE NOT NULL,
                num_ventas INTEGER NOT NULL DEFAULT 0,
                total_cobrado_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                sueldo_base_usd NUMERIC(10, 2) NOT NULL DEFAULT 0,
                comision_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                total_calculado_usd NUMERIC(12, 2) NOT NULL DEFAULT 0,
                estado VARCHAR(20) NOT NULL DEFAULT 'pendiente',
                movimiento_financiero_id CHAR(36),
                fecha_pago DATETIME,
                pagado_por_id CHAR(36),
                notas VARCHAR(500),
                fecha_creacion DATETIME,
                UNIQUE (empresa_id, usuario_id, periodo_desde, periodo_hasta)
            )
            """
        )
    )
