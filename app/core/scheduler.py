"""Tareas programadas para sincronización automática de tasas."""
from __future__ import annotations

import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.db import SessionLocal
from app.services.tasas_scraper import sincronizar_tasas_automaticas

logger = logging.getLogger(__name__)

TZ_CARACAS = ZoneInfo("America/Caracas")
_scheduler: AsyncIOScheduler | None = None


async def _job_sincronizar_tasas(momento: str) -> None:
    db = SessionLocal()
    try:
        await sincronizar_tasas_automaticas(db, momento=momento)
    except Exception:
        logger.exception("Error en job automático de tasas (%s)", momento)
    finally:
        db.close()


def iniciar_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = AsyncIOScheduler(timezone=TZ_CARACAS)

    # Lunes a viernes, 9:00 AM (tasa de la mañana)
    scheduler.add_job(
        _job_sincronizar_tasas,
        CronTrigger(hour=9, minute=0, day_of_week="mon-fri", timezone=TZ_CARACAS),
        kwargs={"momento": "manana"},
        id="tasas_manana",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    # Lunes a viernes, 1:30 PM (tasa de la tarde)
    scheduler.add_job(
        _job_sincronizar_tasas,
        CronTrigger(hour=13, minute=30, day_of_week="mon-fri", timezone=TZ_CARACAS),
        kwargs={"momento": "tarde"},
        id="tasas_tarde",
        replace_existing=True,
        misfire_grace_time=3600,
    )

    scheduler.start()
    _scheduler = scheduler
    logger.info(
        "Scheduler de tasas iniciado (lun-vie 09:00 y 13:30, America/Caracas)"
    )
    return scheduler


def detener_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler de tasas detenido")
