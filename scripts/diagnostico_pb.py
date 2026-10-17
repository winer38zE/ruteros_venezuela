#!/usr/bin/env python3
"""Diagnóstico de latencia/códigos HTTP hacia PocketBase (/api/health)."""
from __future__ import annotations

import os
import sys
import time

import httpx

DEFAULT_URL = os.getenv("POCKETBASE_URL", "http://127.0.0.1:8090").rstrip("/")
INTENTOS = int(os.getenv("DIAG_PB_INTENTOS", "30"))
PAUSA_SEG = float(os.getenv("DIAG_PB_PAUSA", "1"))


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL).rstrip("/")
    url = f"{base}/api/health"
    print(f"POCKETBASE_URL={base}")
    print(f"GET {url} x{INTENTOS} (pausa {PAUSA_SEG}s)")
    transport = httpx.HTTPTransport(retries=0)
    timeout = httpx.Timeout(connect=10.0, read=15.0, write=15.0, pool=5.0)
    ok = 0
    with httpx.Client(transport=transport, timeout=timeout, follow_redirects=True) as client:
        for i in range(1, INTENTOS + 1):
            t0 = time.perf_counter()
            code = "ERR"
            try:
                res = client.get(url)
                code = str(res.status_code)
                if res.is_success:
                    ok += 1
            except httpx.HTTPError as exc:
                code = type(exc).__name__
            lat = (time.perf_counter() - t0) * 1000.0
            print(f"{i:02d}  {code:>12}  {lat:7.1f} ms")
            if i < INTENTOS:
                time.sleep(PAUSA_SEG)
    print(f"Resumen: {ok}/{INTENTOS} respuestas 2xx")
    return 0 if ok > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
