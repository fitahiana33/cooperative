import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.db.session import SessionLocal
from app.jobs.maintenance import run_with_lock

logger = logging.getLogger("cooperative.jobs")


def _maintenance_tick() -> None:
    try:
        with SessionLocal() as db:
            result = run_with_lock(db)
        if result and any(result.values()):
            logger.info("Maintenance : %s", result)
    except Exception:  # never let a failing tick stop the scheduler
        logger.exception("La maintenance planifiée a échoué.")


def start_scheduler() -> BackgroundScheduler | None:
    if not settings.scheduler_enabled:
        return None
    scheduler = BackgroundScheduler(timezone=settings.timezone)
    scheduler.add_job(
        _maintenance_tick, "interval", seconds=settings.maintenance_interval_seconds,
        id="maintenance", max_instances=1, coalesce=True,
    )
    scheduler.start()
    return scheduler
