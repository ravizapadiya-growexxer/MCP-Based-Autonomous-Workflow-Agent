"""
Main entry point.

Starts:
  - APScheduler with morning (11 AM) and evening (7 PM) cron jobs
  - Logs to console + files

Run:  python src/main.py
"""

from __future__ import annotations
import asyncio
import signal
import sys
from pathlib import Path
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Ensure project root is on path when running directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings
from src.utils.logger import setup_logger
from src.agents.morning import run_morning
from src.agents.evening import run_evening


def _ensure_dirs() -> None:
    for d in ["logs/morning", "logs/evening", "logs/error", "logs/screenshots", "data"]:
        Path(d).mkdir(parents=True, exist_ok=True)


async def morning_job() -> None:
    logger.info("Scheduler triggered: MORNING job")
    try:
        await run_morning()
    except Exception as exc:
        logger.exception(f"Unhandled exception in morning job: {exc}")


async def evening_job() -> None:
    logger.info("Scheduler triggered: EVENING job")
    try:
        await run_evening()
    except Exception as exc:
        logger.exception(f"Unhandled exception in evening job: {exc}")


async def main() -> None:
    _ensure_dirs()
    setup_logger("main")

    scheduler = AsyncIOScheduler(timezone=settings.tz)

    scheduler.add_job(
        morning_job,
        trigger=CronTrigger(
            hour=settings.morning_hour,
            minute=settings.morning_minute,
            day_of_week="mon-fri",
            timezone=settings.tz,
        ),
        id="morning",
        name="Morning Jira Workflow",
        replace_existing=True,
        misfire_grace_time=300,   # Fire up to 5 min late if system was asleep
    )

    scheduler.add_job(
        evening_job,
        trigger=CronTrigger(
            hour=settings.evening_hour,
            minute=settings.evening_minute,
            day_of_week="mon-fri",
            timezone=settings.tz,
        ),
        id="evening",
        name="Evening Timesheet Workflow",
        replace_existing=True,
        misfire_grace_time=300,
    )

    scheduler.start()

    logger.info("=" * 60)
    logger.info("MCP Workflow Agent started")
    logger.info(f"Timezone      : {settings.tz}")
    logger.info(f"Morning job   : {settings.morning_hour:02d}:{settings.morning_minute:02d} Mon-Fri")
    logger.info(f"Evening job   : {settings.evening_hour:02d}:{settings.evening_minute:02d} Mon-Fri")
    logger.info(f"Dry run       : {settings.dry_run}")
    logger.info(f"WhatsApp      : {'configured' if settings.whatsapp_phone else 'not configured'}")
    logger.info("=" * 60)

    # Graceful shutdown on SIGINT/SIGTERM
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _shutdown(sig):
        logger.info(f"Received {sig.name} — shutting down scheduler")
        scheduler.shutdown(wait=False)
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _shutdown, sig)

    await stop_event.wait()
    logger.info("Agent stopped")


if __name__ == "__main__":
    asyncio.run(main())
