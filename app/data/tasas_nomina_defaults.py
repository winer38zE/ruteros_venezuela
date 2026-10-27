"""Tasas de referencia para nómina (fallback si no hay registro en BD)."""

from datetime import date

# Referencia operativa 27/10/2026
FECHA_REFERENCIA = date(2026, 10, 27)
USD_TO_VES_BCV = 887.30
USD_TO_COP = 3144.00

# Salarios mínimos / referencia nómina 2026
SALARIO_REFERENCIA_CO_COP = 2_000_000.0
SALARIO_REFERENCIA_VE_USD = 240.0


def tasas_por_defecto() -> dict[str, float]:
    return {
        "USD_TO_VES": USD_TO_VES_BCV,
        "USD_TO_COP": USD_TO_COP,
        "fecha_referencia": FECHA_REFERENCIA.isoformat(),
    }
