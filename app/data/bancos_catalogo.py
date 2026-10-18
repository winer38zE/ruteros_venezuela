"""Listas maestras de bancos y documentos legales por país (SaaS multiregión)."""

from __future__ import annotations

BANCOS_POR_ISO: dict[str, dict[str, list[str]]] = {
    "CO": {
        "bancos": ["Nequi", "Daviplata", "Bancolombia", "Davivienda", "Banco de Bogotá"],
        "documentos_legales": ["CC", "NIT", "CE"],
    },
    "VE": {
        "bancos": [
            "Pago Móvil",
            "Banco de Venezuela",
            "Banesco",
            "Mercantil",
            "Provincial",
        ],
        "documentos_legales": ["V", "J", "E", "G"],
    },
    "BR": {
        "bancos": ["Pix", "Nubank", "Itaú", "Bradesco", "Banco do Brasil"],
        "documentos_legales": ["CPF", "CNPJ"],
    },
    "EC": {
        "bancos": [
            "Banco Pichincha",
            "Banco Guayaquil",
            "Banco del Pacífico",
            "Produbanco",
        ],
        "documentos_legales": ["CI", "RUC"],
    },
    "PE": {
        "bancos": ["Yape", "Plin", "BCP", "BBVA", "Interbank"],
        "documentos_legales": ["DNI", "RUC"],
    },
    "MX": {
        "bancos": ["SPEI", "BBVA México", "Santander", "Banorte", "OXXO Pay"],
        "documentos_legales": ["RFC"],
    },
    "US": {
        "bancos": ["Zelle", "CashApp", "Chase", "Bank of America", "Wells Fargo"],
        "documentos_legales": ["SSN", "EIN"],
    },
}


def fusionar_configuracion_bancaria(
    config_existente: dict | None,
    codigo_iso: str,
) -> dict:
    """Conserva canales/tipos de cuenta previos e inyecta bancos y documentos del catálogo."""
    entrada = BANCOS_POR_ISO.get(codigo_iso.upper())
    if entrada is None:
        raise KeyError(f"ISO no soportado: {codigo_iso}")

    base = dict(config_existente or {})
    base["version"] = max(int(base.get("version") or 1), 2)
    base["bancos"] = list(entrada["bancos"])
    base["documentos_legales"] = list(entrada["documentos_legales"])
    base["tipos_identificacion"] = [
        {"id": doc.lower().replace(" ", "_"), "label": doc}
        for doc in entrada["documentos_legales"]
    ]
    return base
