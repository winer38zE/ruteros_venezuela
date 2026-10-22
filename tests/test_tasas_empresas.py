"""Persistencia de tasas automáticas y empresas activas / legacy PocketBase."""
from __future__ import annotations

import asyncio
import uuid
from unittest.mock import MagicMock

import pytest

from app.core.tenant import empresas_destino_tasas
from app.models.core import Empresa, TasaCambio
from app.services.tasas_scraper import (
    TasasExternas,
    persistir_tasas_sincronizadas,
    sincronizar_tasas_automaticas,
)


def _empresa_legacy(nombre: str = "ED NET PRO") -> Empresa:
    return Empresa(id=uuid.uuid4(), nombre=nombre, activa=False)


def test_empresas_destino_tasas_sin_empresas_en_bd():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    db.query.return_value = q

    with pytest.raises(ValueError, match="No hay empresas registradas"):
        empresas_destino_tasas(db)


def test_empresas_destino_tasas_reactiva_legacy_pocketbase():
    emp = _empresa_legacy()
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = [emp]
    db.query.return_value = q

    resultado = empresas_destino_tasas(db)
    assert len(resultado) == 1
    assert emp.activa is True
    db.flush.assert_called()


def test_persistir_tasas_sin_empresas_falla_controlado():
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    db.query.return_value = q

    tasas = TasasExternas(usd_bcv_bs=80.0, usd_paralelo_bs=90.0, cop_usd=4000.0)
    with pytest.raises(ValueError, match="No hay empresas registradas"):
        persistir_tasas_sincronizadas(db, tasas)


def test_persistir_tasas_con_empresa_legacy():
    emp = _empresa_legacy()
    db = MagicMock()

    def query_side(model):
        q = MagicMock()
        if model is Empresa:
            q.filter.return_value = q
            q.all.return_value = [emp]
        elif model is TasaCambio:
            q.filter.return_value = q
            q.update.return_value = 0
        return q

    db.query.side_effect = query_side
    tasas = TasasExternas(usd_bcv_bs=80.0, usd_paralelo_bs=90.0, cop_usd=4000.0)

    creadas = persistir_tasas_sincronizadas(db, tasas, momento="manana")
    assert len(creadas) == 1
    db.commit.assert_called_once()


def test_sincronizar_sin_empresas_no_persiste(monkeypatch):
    db = MagicMock()
    q = MagicMock()
    q.filter.return_value = q
    q.all.return_value = []
    db.query.return_value = q

    async def _tasas_ok():
        return TasasExternas(usd_bcv_bs=80.0, usd_paralelo_bs=90.0, cop_usd=4000.0)

    monkeypatch.setattr(
        "app.services.tasas_scraper.obtener_tasas_externas",
        _tasas_ok,
    )

    creadas, externas, _fallback = asyncio.run(sincronizar_tasas_automaticas(db))
    assert creadas == []
    assert externas.fuentes.get("tasas_persistidas") is False
    assert "persistencia" in externas.fuentes
