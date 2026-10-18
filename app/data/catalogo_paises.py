"""Catálogo maestro de países Ruteros SaaS (Fase 1 multiregión)."""

CATALOGO_PAISES: list[dict] = [
    {
        "nombre": "Colombia",
        "codigo_iso": "CO",
        "moneda_principal": "COP",
        "simbolo_moneda": "$",
        "locale": "es-CO",
        "zona_horaria": "America/Bogota",
        "activo": True,
        "configuracion_bancaria": {
            "version": 1,
            "tipos_cuenta": [
                {"id": "ahorro", "label": "Ahorros"},
                {"id": "corriente", "label": "Corriente"},
            ],
            "tipos_identificacion": [
                {"id": "nit", "label": "NIT", "pattern": "^[0-9]{9,10}(-[0-9])?$"},
                {"id": "cc", "label": "Cédula de ciudadanía", "pattern": "^[0-9]{6,10}$"},
            ],
            "canales_pago": [
                {"id": "transferencia", "label": "Transferencia", "requiere_numero_cuenta": True},
                {"id": "pse", "label": "PSE", "requiere_numero_cuenta": False},
            ],
        },
        "configuracion_fiscal": {"moneda_base": "COP", "iva_porcentaje": 19},
        "configuracion_ui": {
            "monedas_visibles": ["COP", "USD"],
            "mostrar_conversion_ves_bcv": False,
            "mostrar_conversion_ves_paralelo": False,
        },
    },
    {
        "nombre": "Venezuela",
        "codigo_iso": "VE",
        "moneda_principal": "VES",
        "simbolo_moneda": "Bs.",
        "locale": "es-VE",
        "zona_horaria": "America/Caracas",
        "activo": True,
        "configuracion_bancaria": {
            "version": 1,
            "tipos_cuenta": [
                {"id": "ahorro", "label": "Ahorro"},
                {"id": "corriente", "label": "Corriente"},
            ],
            "tipos_identificacion": [
                {"id": "rif", "label": "RIF", "pattern": "^[VEJGPvejgp]-[0-9]{8}-[0-9]$"},
                {"id": "cedula", "label": "Cédula", "pattern": "^[VEve]-?[0-9]{6,9}$"},
            ],
            "canales_pago": [
                {"id": "transferencia", "label": "Transferencia", "requiere_numero_cuenta": True},
                {"id": "pago_movil", "label": "Pago móvil", "requiere_telefono": True},
            ],
        },
        "configuracion_fiscal": {"moneda_base": "USD", "iva_porcentaje": 16, "igtf_porcentaje": 3},
        "configuracion_ui": {
            "monedas_visibles": ["USD", "VES", "COP"],
            "mostrar_conversion_ves_bcv": True,
            "mostrar_conversion_ves_paralelo": True,
        },
    },
    {
        "nombre": "Brasil",
        "codigo_iso": "BR",
        "moneda_principal": "BRL",
        "simbolo_moneda": "R$",
        "locale": "pt-BR",
        "zona_horaria": "America/Sao_Paulo",
        "activo": True,
        "configuracion_bancaria": {
            "version": 1,
            "tipos_cuenta": [
                {"id": "corrente", "label": "Conta corrente"},
                {"id": "poupanca", "label": "Poupança"},
            ],
            "tipos_identificacion": [
                {"id": "cpf", "label": "CPF", "pattern": "^[0-9]{11}$"},
                {"id": "cnpj", "label": "CNPJ", "pattern": "^[0-9]{14}$"},
            ],
            "canales_pago": [
                {"id": "transferencia", "label": "TED/DOC", "requiere_numero_cuenta": True},
                {"id": "pix", "label": "PIX", "requiere_clave_pix": True},
            ],
        },
        "configuracion_fiscal": {"moneda_base": "BRL", "iva_porcentaje": 0},
        "configuracion_ui": {"monedas_visibles": ["BRL", "USD"], "mostrar_conversion_ves_bcv": False},
    },
    {
        "nombre": "Ecuador",
        "codigo_iso": "EC",
        "moneda_principal": "USD",
        "simbolo_moneda": "$",
        "locale": "es-EC",
        "zona_horaria": "America/Guayaquil",
        "activo": True,
        "configuracion_bancaria": {
            "version": 1,
            "tipos_identificacion": [
                {"id": "ruc", "label": "RUC", "pattern": "^[0-9]{13}$"},
                {"id": "cedula", "label": "Cédula", "pattern": "^[0-9]{10}$"},
            ],
            "canales_pago": [{"id": "transferencia", "label": "Transferencia", "requiere_numero_cuenta": True}],
        },
        "configuracion_fiscal": {"moneda_base": "USD", "iva_porcentaje": 15},
        "configuracion_ui": {"monedas_visibles": ["USD"], "mostrar_conversion_ves_bcv": False},
    },
    {
        "nombre": "Perú",
        "codigo_iso": "PE",
        "moneda_principal": "PEN",
        "simbolo_moneda": "S/",
        "locale": "es-PE",
        "zona_horaria": "America/Lima",
        "activo": True,
        "configuracion_bancaria": {
            "version": 1,
            "tipos_identificacion": [
                {"id": "ruc", "label": "RUC", "pattern": "^[0-9]{11}$"},
                {"id": "dni", "label": "DNI", "pattern": "^[0-9]{8}$"},
            ],
            "canales_pago": [{"id": "transferencia", "label": "Transferencia", "requiere_numero_cuenta": True}],
        },
        "configuracion_fiscal": {"moneda_base": "PEN", "iva_porcentaje": 18},
        "configuracion_ui": {"monedas_visibles": ["PEN", "USD"], "mostrar_conversion_ves_bcv": False},
    },
    {
        "nombre": "México",
        "codigo_iso": "MX",
        "moneda_principal": "MXN",
        "simbolo_moneda": "$",
        "locale": "es-MX",
        "zona_horaria": "America/Mexico_City",
        "activo": True,
        "configuracion_bancaria": {
            "version": 1,
            "tipos_identificacion": [
                {"id": "rfc", "label": "RFC", "pattern": "^[A-ZÑ&]{3,4}[0-9]{6}[A-Z0-9]{3}$"},
                {"id": "curp", "label": "CURP", "pattern": "^[A-Z]{4}[0-9]{6}[A-Z]{6}[0-9]{2}$"},
            ],
            "canales_pago": [
                {"id": "transferencia", "label": "SPEI", "requiere_numero_cuenta": True},
                {"id": "clabe", "label": "CLABE", "requiere_clabe": True},
            ],
        },
        "configuracion_fiscal": {"moneda_base": "MXN", "iva_porcentaje": 16},
        "configuracion_ui": {"monedas_visibles": ["MXN", "USD"], "mostrar_conversion_ves_bcv": False},
    },
    {
        "nombre": "Estados Unidos",
        "codigo_iso": "US",
        "moneda_principal": "USD",
        "simbolo_moneda": "$",
        "locale": "en-US",
        "zona_horaria": "America/New_York",
        "activo": True,
        "configuracion_bancaria": {
            "version": 1,
            "tipos_identificacion": [
                {"id": "ein", "label": "EIN", "pattern": "^[0-9]{2}-[0-9]{7}$"},
                {"id": "ssn", "label": "SSN (últimos 4)", "pattern": "^[0-9]{4}$"},
            ],
            "canales_pago": [
                {"id": "ach", "label": "ACH", "requiere_routing_number": True},
                {"id": "wire", "label": "Wire transfer", "requiere_numero_cuenta": True},
            ],
        },
        "configuracion_fiscal": {"moneda_base": "USD", "iva_porcentaje": 0},
        "configuracion_ui": {"monedas_visibles": ["USD"], "mostrar_conversion_ves_bcv": False},
    },
]

PAIS_ISO_POR_DEFECTO = "VE"
