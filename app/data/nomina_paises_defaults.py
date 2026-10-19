"""
Parámetros de nómina por país (referencia legal / operativa 2026).

Montos en moneda local del país (moneda_principal). El dueño puede ajustarlos
después desde la app; el script setup_nomina_finanzas solo rellena si están en cero.
"""

NOMINA_POR_ISO: dict[str, dict[str, float]] = {
    "CO": {
        "sueldo_base_legal": 1_423_500,
        "porcentaje_comision_venta": 2.5,
        "porcentaje_comision_cobro": 3.0,
        "bono_incentivo": 0,
    },
    "VE": {
        "sueldo_base_legal": 130.0,
        "porcentaje_comision_venta": 2.0,
        "porcentaje_comision_cobro": 5.0,
        "bono_incentivo": 0,
    },
    "MX": {
        "sueldo_base_legal": 8_364.0,
        "porcentaje_comision_venta": 2.5,
        "porcentaje_comision_cobro": 3.5,
        "bono_incentivo": 0,
    },
    "EC": {
        "sueldo_base_legal": 482.0,
        "porcentaje_comision_venta": 2.5,
        "porcentaje_comision_cobro": 3.0,
        "bono_incentivo": 0,
    },
    "PE": {
        "sueldo_base_legal": 1_130.0,
        "porcentaje_comision_venta": 2.5,
        "porcentaje_comision_cobro": 3.0,
        "bono_incentivo": 0,
    },
    "BR": {
        "sueldo_base_legal": 1_518.0,
        "porcentaje_comision_venta": 2.0,
        "porcentaje_comision_cobro": 4.0,
        "bono_incentivo": 0,
    },
    "US": {
        "sueldo_base_legal": 2_900.0,
        "porcentaje_comision_venta": 3.0,
        "porcentaje_comision_cobro": 3.0,
        "bono_incentivo": 0,
    },
}
