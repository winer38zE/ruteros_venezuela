"""Números y montos a palabras, para que el TTS no lea cifras sueltas."""
from __future__ import annotations

import re

_UNIDADES = (
    "cero",
    "uno",
    "dos",
    "tres",
    "cuatro",
    "cinco",
    "seis",
    "siete",
    "ocho",
    "nueve",
)
_DIEZ = (
    "diez",
    "once",
    "doce",
    "trece",
    "catorce",
    "quince",
    "dieciseis",
    "diecisiete",
    "dieciocho",
    "diecinueve",
)
_DECENAS = (
    "",
    "",
    "veinte",
    "treinta",
    "cuarenta",
    "cincuenta",
    "sesenta",
    "setenta",
    "ochenta",
    "noventa",
)
_CIENTOS = (
    "",
    "ciento",
    "doscientos",
    "trescientos",
    "cuatrocientos",
    "quinientos",
    "seiscientos",
    "setecientos",
    "ochocientos",
    "novecientos",
)
_DIGITOS = {
    "0": "cero",
    "1": "uno",
    "2": "dos",
    "3": "tres",
    "4": "cuatro",
    "5": "cinco",
    "6": "seis",
    "7": "siete",
    "8": "ocho",
    "9": "nueve",
}


def entero_a_palabras(n: int) -> str:
    if n < 0:
        return f"menos {entero_a_palabras(-n)}"
    if n < 1000:
        return _hasta_999(n)
    if n < 1_000_000:
        miles, resto = divmod(n, 1000)
        pref = "mil" if miles == 1 else f"{_hasta_999(miles)} mil"
        if resto == 0:
            return pref
        return f"{pref} {_hasta_999(resto)}"
    return " ".join(_DIGITOS[d] for d in str(n))


def _hasta_999(n: int) -> str:
    if n < 10:
        return _UNIDADES[n]
    if n < 20:
        return _DIEZ[n - 10]
    if n < 30:
        if n == 20:
            return "veinte"
        return "veinti" + _UNIDADES[n - 20]
    if n < 100:
        dec, uni = divmod(n, 10)
        if uni == 0:
            return _DECENAS[dec]
        return f"{_DECENAS[dec]} y {_UNIDADES[uni]}"
    if n == 100:
        return "cien"
    cientos, resto = divmod(n, 100)
    pref = _CIENTOS[cientos]
    if resto == 0:
        return pref
    return f"{pref} {_hasta_999(resto)}"


def _digitos_a_palabras(texto: str) -> str:
    return " ".join(_DIGITOS[d] for d in texto if d.isdigit())


def _monto_a_palabras(entero: str, fraccion: str | None) -> str:
    pesos = entero_a_palabras(int(entero))
    if not fraccion:
        return f"{pesos} dolares"
    centavos = fraccion.ljust(2, "0")[:2]
    if centavos == "00":
        return f"{pesos} dolares"
    return f"{pesos} dolares con {entero_a_palabras(int(centavos))} centavos"


def numeros_a_palabras(texto: str) -> str:
    """Convierte cifras y montos. Los teléfonos (8+ dígitos) se deletrean."""
    if not texto:
        return texto

    def _telefono(m: re.Match[str]) -> str:
        return _digitos_a_palabras(m.group(0))

    salida = re.sub(r"(?<!\d)\d{8,}(?!\d)", _telefono, texto)

    def _monto(m: re.Match[str]) -> str:
        return _monto_a_palabras(m.group(1), m.group(2))

    salida = re.sub(
        r"(?<!\d)(\d{1,6})(?:[.,](\d{1,2}))?\s*(?:d[oó]lares|usd|\$)",
        _monto,
        salida,
        flags=re.IGNORECASE,
    )

    def _numero(m: re.Match[str]) -> str:
        return entero_a_palabras(int(m.group(0)))

    return re.sub(r"(?<!\d)\d{1,6}(?!\d)", _numero, salida)
