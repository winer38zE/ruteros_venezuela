"""Pruebas de resiliencia Coolify: reintentos, caché y health."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from pocketbase.errors import ClientResponseError

from app.core import pb_collections_cache
from app.core.pb_retry import es_error_transitorio, ejecutar_con_reintentos, pausa_reintento
from app.main import app


def test_es_error_transitorio_502_503_504():
    assert es_error_transitorio(ClientResponseError("x", url="", status=502, data={}))
    assert es_error_transitorio(ClientResponseError("x", url="", status=503, data={}))
    assert not es_error_transitorio(ClientResponseError("x", url="", status=401, data={}))


def test_pausa_reintento_creciente():
    assert pausa_reintento(1) == 0.5
    assert pausa_reintento(2) == 1.0
    assert pausa_reintento(4) == 4.0
    assert pausa_reintento(10) == 4.0


def test_ejecutar_con_reintentos_recupera_tras_502():
    intentos = {"n": 0}

    def flaky():
        intentos["n"] += 1
        if intentos["n"] < 3:
            raise ClientResponseError("bad gateway", url="", status=502, data={})
        return "ok"

    with patch("app.core.pb_retry.time.sleep"):
        assert ejecutar_con_reintentos(flaky, max_intentos=5) == "ok"
    assert intentos["n"] == 3


def test_cache_colecciones_evita_llamadas_repetidas():
    pb = MagicMock()
    pb.base_url = "https://pb.test"
    pb._ruteros_cache_colecciones = False
    coll = MagicMock()
    coll.name = "usuarios"
    coll.id = "abc123"
    llamadas: list[int] = []

    def get_full_list(*_args, **_kwargs):
        llamadas.append(1)
        return [coll]

    pb.collections.get_full_list = get_full_list

    pb_collections_cache.invalidar_cache_colecciones(pb)
    pb_collections_cache.instalar_cache_colecciones(pb)

    pb_collections_cache.mapa_colecciones_por_nombre(pb)
    pb_collections_cache.mapa_colecciones_por_nombre(pb)

    assert len(llamadas) == 1


def test_health_liveness_sin_pocketbase():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_health_ready_503_si_sonda_falla():
    client = TestClient(app)
    with patch(
        "app.api.health.sondear_pocketbase",
        side_effect=ClientResponseError("x", url="", status=502, data={}),
    ):
        res = client.get("/health/ready")
    assert res.status_code == 503


def test_health_ready_200_si_sonda_ok():
    client = TestClient(app)
    with patch(
        "app.api.health.sondear_pocketbase",
        return_value={
            "disponible": True,
            "ultima_latencia_ms": 12.3,
            "ultimo_exito_utc": "2026-01-01T00:00:00+00:00",
            "ultimo_error": None,
        },
    ):
        res = client.get("/health/ready")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ready"
