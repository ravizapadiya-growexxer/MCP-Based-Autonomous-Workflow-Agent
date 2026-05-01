"""APScheduler entry point. Registers the morning, evening, notification,
and monthly reminder jobs in IST and runs alongside the status server."""

from __future__ import annotations

import asyncio
import logging
import signal
from logging.handlers import RotatingFileHandler
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone

from config.settings import settings
from observability.status_server import run_status_server
from scheduler.jobs import (
    evening_job,
    monthly_reminder_job,
    morning_job,
    notification_job,
)


def _configure_logging() -> None:
    log_dir = Path(settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "automation.log"
    formatter = logging.Formatter(
        "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    )
    file_handler = RotatingFileHandler(
        log_path, maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())
    # Reset to avoid duplicate handlers on re-run
    root.handlers = [file_handler, stream_handler]


logger = logging.getLogger(__name__)


def _build_scheduler() -> AsyncIOScheduler:
    tz = timezone(settings.timezone)
    scheduler = AsyncIOScheduler(timezone=tz)
    scheduler.add_job(
        morning_job,
        CronTrigger(hour=11, minute=0, day_of_week="mon-fri", timezone=tz),
        id="morning_job",
        name="Morning routine (11:00 AM IST)",
        misfire_grace_time=7200,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        evening_job,
        CronTrigger(hour=19, minute=0, day_of_week="mon-fri", timezone=tz),
        id="evening_job",
        name="Evening routine (7:00 PM IST)",
        misfire_grace_time=7200,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        notification_job,
        CronTrigger(hour=19, minute=30, day_of_week="mon-fri", timezone=tz),
        id="notification_job",
        name="Notification summary (7:30 PM IST)",
        misfire_grace_time=1800,
        coalesce=True,
        max_instances=1,
    )
    scheduler.add_job(
        monthly_reminder_job,
        CronTrigger(day=1, hour=9, minute=0, timezone=tz),
        id="monthly_reminder",
        name="Monthly health check (1st @ 9 AM IST)",
        coalesce=True,
        max_instances=1,
    )
    return scheduler


async def main() -> None:
    _configure_logging()
    logger.info("Initializing intern automation scheduler")
    logger.info(
        "timezone=%s parent=%s start_date=%s",
        settings.timezone, settings.jira_parent_key, settings.intern_start_date,
    )

    scheduler = _build_scheduler()
    stop_event = asyncio.Event()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            # Windows doesn't support signal handlers in asyncio loop.
            pass

    status_task = asyncio.create_task(run_status_server(), name="status_server")
    scheduler.start()
    logger.info("Scheduler started; jobs registered: %s", [j.id for j in scheduler.get_jobs()])

    try:
        await stop_event.wait()
    finally:
        logger.info("Shutting down scheduler...")
        scheduler.shutdown(wait=False)
        status_task.cancel()
        try:
            await status_task
        except (asyncio.CancelledError, Exception):  # noqa: BLE001
            pass
        logger.info("Shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
