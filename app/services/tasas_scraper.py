"""Obtención automática de tasas BCV, paralelo y COP/TRM con fallbacks."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.core import Empresa, TasaCambio

logger = logging.getLogger(__name__)

HTTP_TIMEOUT = 20.0
USER_AGENT = (
    "Mozilla/5.0 (compatible; RuterosBot/1.0; +https://ednetpro.local/tasas)"
)

DOLARAPI_OFICIAL = "https://ve.dolarapi.com/v1/dolares/oficial"
DOLARAPI_PARALELO = "https://ve.dolarapi.com/v1/dolares/paralelo"
BCV_URL = "https://www.bcv.org.ve/"
TRM_USD_COP_URL = "https://open.er-api.com/v6/latest/USD"

# Fallback si todas las fuentes fallan (aprox. mercado)
FALLBACK_BCV = 75.0
FALLBACK_PARALELO = 85.0
FALLBACK_COP_USD = 4000.0


@dataclass
class TasasExternas:
    usd_bcv_bs: float
    usd_paralelo_bs: float
    cop_usd: float
    eur_bs: float = 0.0
    fuentes: dict = field(default_factory=dict)


def _parse_ves_number(text: str) -> Optional[float]:
    if not text:
        return None
    cleaned = text.strip().replace("\xa0", "").replace(" ", "")
    cleaned = cleaned.replace(",", ".")
    match = re.search(r"[\d.]+", cleaned)
    if not match:
        return None
    try:
        value = float(match.group())
        return value if value > 0 else None
    except ValueError:
        return None


async def _fetch_json(client: httpx.AsyncClient, url: str) -> Optional[dict]:
    try:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("No se pudo obtener JSON de %s: %s", url, exc)
        return None


async def obtener_tasa_bcv_api(client: httpx.AsyncClient) -> tuple[Optional[float], str]:
    data = await _fetch_json(client, DOLARAPI_OFICIAL)
    if not data:
        return None, "dolarapi_oficial_error"
    promedio = data.get("promedio") or data.get("venta") or data.get("compra")
    if promedio:
        return float(promedio), "dolarapi_oficial"
    return None, "dolarapi_oficial_sin_dato"


async def obtener_tasa_bcv_scraping(client: httpx.AsyncClient) -> tuple[Optional[float], str]:
    try:
        response = await client.get(BCV_URL)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        for element_id in ("dolar", "usd", "USD"):
            node = soup.find(id=element_id)
            if node:
                value = _parse_ves_number(node.get_text(" ", strip=True))
                if value:
                    return value, "bcv_scraping"

        for strong in soup.find_all("strong"):
            parent_id = getattr(strong.parent, "id", "") or ""
            if "dolar" in parent_id.lower() or "usd" in parent_id.lower():
                value = _parse_ves_number(strong.get_text())
                if value:
                    return value, "bcv_scraping"
    except Exception as exc:
        logger.warning("Scraping BCV falló: %s", exc)
    return None, "bcv_scraping_error"


async def obtener_tasa_bcv(client: httpx.AsyncClient) -> tuple[float, str]:
    value, source = await obtener_tasa_bcv_api(client)
    if value:
        return value, source
    value, source = await obtener_tasa_bcv_scraping(client)
    if value:
        return value, source
    return FALLBACK_BCV, "fallback_bcv"


async def obtener_tasa_paralelo(client: httpx.AsyncClient) -> tuple[float, str]:
    data = await _fetch_json(client, DOLARAPI_PARALELO)
    if data:
        promedio = data.get("promedio") or data.get("venta") or data.get("compra")
        if promedio:
            return float(promedio), "dolarapi_paralelo"
    return FALLBACK_PARALELO, "fallback_paralelo"


async def obtener_cop_por_usd(client: httpx.AsyncClient) -> tuple[float, str]:
    data = await _fetch_json(client, TRM_USD_COP_URL)
    if data:
        rates = data.get("rates") or {}
        cop = rates.get("COP")
        if cop:
            return float(cop), "open_er_api_trm"
    return FALLBACK_COP_USD, "fallback_cop"


async def obtener_tasas_externas() -> TasasExternas:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9"}
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT, headers=headers, follow_redirects=True) as client:
        bcv, src_bcv = await obtener_tasa_bcv(client)
        paralelo, src_paralelo = await obtener_tasa_paralelo(client)
        cop, src_cop = await obtener_cop_por_usd(client)

    return TasasExternas(
        usd_bcv_bs=bcv,
        usd_paralelo_bs=paralelo,
        cop_usd=cop,
        fuentes={
            "usd_bcv": src_bcv,
            "usd_paralelo": src_paralelo,
            "cop_usd": src_cop,
            "obtenido_en": datetime.utcnow().isoformat(),
        },
    )


def momento_actual() -> str:
    return "manana" if datetime.now().hour < 12 else "tarde"


def persistir_tasas_sincronizadas(
    db: Session,
    tasas: TasasExternas,
    momento: Optional[str] = None,
    empresa_id=None,
) -> list[TasaCambio]:
    momento = momento or momento_actual()
    cop_ves = tasas.usd_bcv_bs / tasas.cop_usd if tasas.cop_usd else None

    query = db.query(Empresa).filter(Empresa.activa.is_(True))
    if empresa_id:
        query = query.filter(Empresa.id == empresa_id)
    empresas = query.all()

    if not empresas:
        raise ValueError("No hay empresas activas para registrar tasas")

    creadas: list[TasaCambio] = []
    for empresa in empresas:
        db.query(TasaCambio).filter(
            TasaCambio.empresa_id == empresa.id,
            TasaCambio.activa.is_(True),
        ).update({"activa": False})

        nueva = TasaCambio(
            empresa_id=empresa.id,
            momento=momento,
            usd_bs=tasas.usd_bcv_bs,
            usd_bcv_bs=tasas.usd_bcv_bs,
            usd_paralelo_bs=tasas.usd_paralelo_bs,
            eur_bs=tasas.eur_bs,
            cop_usd=tasas.cop_usd,
            cop_ves=cop_ves,
            activa=True,
            origen="auto",
            fecha=datetime.utcnow(),
        )
        db.add(nueva)
        creadas.append(nueva)

    db.commit()
    for tasa in creadas:
        db.refresh(tasa)
    return creadas


async def sincronizar_tasas_automaticas(
    db: Session,
    momento: Optional[str] = None,
    empresa_id=None,
) -> tuple[list[TasaCambio], TasasExternas]:
    tasas = await obtener_tasas_externas()
    creadas = persistir_tasas_sincronizadas(db, tasas, momento=momento, empresa_id=empresa_id)
    logger.info(
        "Tasas sincronizadas (%s): BCV=%.4f Paralelo=%.4f COP/USD=%.2f empresas=%d",
        momento or momento_actual(),
        tasas.usd_bcv_bs,
        tasas.usd_paralelo_bs,
        tasas.cop_usd,
        len(creadas),
    )
    return creadas, tasas
