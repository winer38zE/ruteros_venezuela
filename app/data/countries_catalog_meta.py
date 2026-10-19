"""Metadatos de catálogo (bandera, formatos, monedas de pago) por ISO."""

COUNTRY_META: dict[str, dict] = {
    "CO": {
        "bandera": "🇨🇴",
        "prefijo_telefonico": "+57",
        "formato_numero": "#,##0.##",
        "formato_fecha": "dd/MM/yyyy",
        "payment_currencies": ["COP"],
    },
    "VE": {
        "bandera": "🇻🇪",
        "prefijo_telefonico": "+58",
        "formato_numero": "#,##0.##",
        "formato_fecha": "dd/MM/yyyy",
        "payment_currencies": ["USD", "VES"],
        "tasas_cambio_referencia": {
            "BCV": {"moneda_par": "VES", "descripcion": "Tasa oficial BCV"},
            "PARALELO": {"moneda_par": "VES", "descripcion": "Referencia mercado paralelo"},
        },
    },
    "MX": {
        "bandera": "🇲🇽",
        "prefijo_telefonico": "+52",
        "formato_numero": "#,##0.##",
        "formato_fecha": "dd/MM/yyyy",
        "payment_currencies": ["MXN"],
    },
    "EC": {
        "bandera": "🇪🇨",
        "prefijo_telefonico": "+593",
        "formato_numero": "#,##0.##",
        "formato_fecha": "dd/MM/yyyy",
        "payment_currencies": ["USD"],
    },
    "PE": {
        "bandera": "🇵🇪",
        "prefijo_telefonico": "+51",
        "formato_numero": "#,##0.##",
        "formato_fecha": "dd/MM/yyyy",
        "payment_currencies": ["PEN"],
    },
    "BR": {
        "bandera": "🇧🇷",
        "prefijo_telefonico": "+55",
        "formato_numero": "#,##0.##",
        "formato_fecha": "dd/MM/yyyy",
        "payment_currencies": ["BRL"],
    },
    "US": {
        "bandera": "🇺🇸",
        "prefijo_telefonico": "+1",
        "formato_numero": "#,##0.##",
        "formato_fecha": "MM/dd/yyyy",
        "payment_currencies": ["USD"],
    },
}
