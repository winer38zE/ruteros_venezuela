"""Cómo se dicen los montos y el medio de pago, por escrito y por voz."""
from __future__ import annotations

import re
import unicodedata


def _fold(texto: str) -> str:
    base = (texto or "").strip().casefold()
    sin_tilde = unicodedata.normalize("NFKD", base)
    return "".join(c for c in sin_tilde if not unicodedata.combining(c))


def frase_monto(monto: float, moneda: str | None = None) -> str:
    """10.00 dólares o 500.00 bolívares. Nunca la sigla USD."""
    codigo = _fold(moneda or "dolar")
    if codigo in ("bolivar", "bolivares", "ves", "bs"):
        unidad = "bolívares"
    elif codigo in ("peso", "pesos", "cop"):
        unidad = "pesos"
    else:
        unidad = "dólares"
    return f"{float(monto):.2f} {unidad}"


def frase_metodo(metodo: str | None) -> str:
    codigo = _fold(metodo or "efectivo").replace(" ", "_")
    if "movil" in codigo:
        return "pago móvil"
    if "transfer" in codigo:
        return "transferencia"
    return "efectivo"


def frase_cobro(monto: float, moneda: str | None, metodo: str | None) -> str:
    medio = frase_metodo(metodo)
    conector = "en" if medio == "efectivo" else "por"
    return f"{frase_monto(monto, moneda)} {conector} {medio}"


def detectar_moneda(texto: str) -> str | None:
    baja = _fold(texto)
    if re.search(r"\bbolivares?\b|\bbs\b|\bves\b", baja):
        return "bolivar"
    if re.search(r"\bdolares?\b|\bdolar\b", baja):
        return "dolar"
    return None


def detectar_metodo(texto: str) -> str | None:
    """Efectivo, transferencia o pago móvil. Dólares y bolívares no son un método."""
    baja = _fold(texto)
    if "pago movil" in baja or "pagomovil" in baja:
        return "pago_movil"
    if "transferencia" in baja:
        return "transferencia"
    if re.search(r"\befectivo\b", baja):
        return "efectivo"
    return None
