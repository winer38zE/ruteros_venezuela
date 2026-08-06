"""Motor de localización fiscal multi-país (Fase 1)."""
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from typing import Optional

from app.models.core import MonedaPago, ConfiguracionFiscal


def _d(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# Presets legales base — la empresa puede sobrescribir vía ConfiguracionFiscal
PRESETS_PAIS: dict[str, dict] = {
    "VE": {
        "nombre": "Venezuela",
        "moneda_base": "USD",
        "iva_porcentaje": Decimal("16.00"),
        "igtf_porcentaje": Decimal("3.00"),
        "aplica_igtf_divisas": True,
        "notas": "IVA general 16% · IGTF 3% sobre pagos en divisas (LIVA)",
    },
    "CO": {
        "nombre": "Colombia",
        "moneda_base": "COP",
        "iva_porcentaje": Decimal("19.00"),
        "igtf_porcentaje": Decimal("0.00"),
        "aplica_igtf_divisas": False,
        "notas": "IVA general 19%",
    },
    "PA": {
        "nombre": "Panamá",
        "moneda_base": "USD",
        "iva_porcentaje": Decimal("7.00"),
        "igtf_porcentaje": Decimal("0.00"),
        "aplica_igtf_divisas": False,
        "notas": "ITBMS 7%",
    },
}


@dataclass
class ImpuestosCalculados:
    base_usd: Decimal
    iva_usd: Decimal
    total_usd: Decimal
    igtf_usd: Decimal
    neto_cobro_usd: Decimal


def listar_paises_disponibles() -> list[dict]:
    resultado = []
    for codigo, datos in PRESETS_PAIS.items():
        resultado.append({
            "codigo": codigo,
            "nombre": datos["nombre"],
            "moneda_base": datos["moneda_base"],
            "iva_porcentaje": float(datos["iva_porcentaje"]),
            "igtf_porcentaje": float(datos["igtf_porcentaje"]),
            "aplica_igtf_divisas": datos["aplica_igtf_divisas"],
            "notas": datos["notas"],
        })
    return resultado


def obtener_preset_pais(pais: str) -> dict:
    preset = PRESETS_PAIS.get(pais.upper())
    if not preset:
        raise ValueError(f"País '{pais}' no tiene preset fiscal configurado")
    return {
        "codigo": pais.upper(),
        "nombre": preset["nombre"],
        "moneda_base": preset["moneda_base"],
        "iva_porcentaje": float(preset["iva_porcentaje"]),
        "igtf_porcentaje": float(preset["igtf_porcentaje"]),
        "aplica_igtf_divisas": preset["aplica_igtf_divisas"],
        "notas": preset["notas"],
    }


def aplicar_preset_a_config(config: ConfiguracionFiscal, pais: str) -> ConfiguracionFiscal:
    preset = obtener_preset_pais(pais)
    config.pais = preset["codigo"]
    config.moneda_base = preset["moneda_base"]
    config.iva_porcentaje = preset["iva_porcentaje"]
    config.igtf_porcentaje = preset["igtf_porcentaje"]
    config.aplica_igtf_divisas = preset["aplica_igtf_divisas"]
    return config


def calcular_impuestos_venta(fiscal: ConfiguracionFiscal, total_usd) -> ImpuestosCalculados:
    base = _d(total_usd)
    iva = _d(base * _d(fiscal.iva_porcentaje) / Decimal("100"))
    total = _d(base + iva)
    return ImpuestosCalculados(
        base_usd=base,
        iva_usd=iva,
        total_usd=total,
        igtf_usd=Decimal("0"),
        neto_cobro_usd=Decimal("0"),
    )


def calcular_impuestos_cobro(
    fiscal: ConfiguracionFiscal,
    monto_usd,
    moneda_pago: MonedaPago,
) -> ImpuestosCalculados:
    monto = _d(monto_usd)
    aplica_igtf = (
        fiscal.aplica_igtf_divisas
        and moneda_pago in (MonedaPago.DOLAR, MonedaPago.EURO)
    )
    igtf = (
        _d(monto * _d(fiscal.igtf_porcentaje) / Decimal("100"))
        if aplica_igtf
        else Decimal("0")
    )
    return ImpuestosCalculados(
        base_usd=monto,
        iva_usd=Decimal("0"),
        total_usd=monto,
        igtf_usd=igtf,
        neto_cobro_usd=_d(monto - igtf),
    )


CUENTAS = {
    "CXC": ("1.2.01", "Cuentas por Cobrar"),
    "INGRESOS": ("4.1.01", "Ingresos por Ventas"),
    "IVA": ("2.1.01", "IVA por Pagar"),
    "IGTF": ("2.1.02", "IGTF por Pagar"),
    "CAJA_BS": ("1.1.01", "Caja Bolívares"),
    "CAJA_DIV": ("1.1.02", "Caja Divisas"),
}
