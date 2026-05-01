"""APScheduler job definitions: morning, evening, notification, monthly."""

from __future__ import annotations

import logging
from datetime import date, datetime
from typing import Any, Dict

from agent.evening_agent import run_evening_agent
from agent.morning_agent import run_morning_agent
from mcp_servers.state_mcp.server import state_server
from notifications.twilio_client import send_twilio_notification
from scheduler.guards import (
    check_catch_up,
    should_run_evening,
    should_run_morning,
)

logger = logging.getLogger(__name__)


async def _record_skip(reason: str) -> None:
    try:
        await state_server.set_today_state(skip_reason=reason)
    except Exception:  # noqa: BLE001
        logger.exception("failed to record skip_reason")


async def morning_job() -> None:
    logger.info("Morning job triggered")
    try:
        await state_server.init_db()

        proceed, reason = await should_run_morning(state_server)
        if not proceed:
            logger.info("morning skipped: %s", reason)
            await _record_skip(reason)
            await send_twilio_notification(f"📅 {reason}. Automation skipped today.")
            return

        catch_up = await check_catch_up(state_server)
        if catch_up:
            await send_twilio_notification(catch_up)

        start = datetime.now()
        result = await run_morning_agent()
        duration = int((datetime.now() - start).total_seconds())
        await state_server.set_today_state(morning_duration_sec=duration)

        if result.get("status") == "completed":
            logger.info("morning job completed in %ds", duration)
        else:
            logger.error("morning job failed: %s", result.get("error"))
            await state_server.log_error(f"morning: {result.get('error')}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("morning job exception")
        await send_twilio_notification(f"🚨 Morning job error: {exc}")


async def evening_job() -> None:
    logger.info("Evening job triggered")
    try:
        await state_server.init_db()

        proceed, reason = await should_run_evening(state_server)
        if not proceed:
            logger.info("evening skipped: %s", reason)
            await _record_skip(reason)
            return

        start = datetime.now()
        result = await run_evening_agent()
        duration = int((datetime.now() - start).total_seconds())
        await state_server.set_today_state(evening_duration_sec=duration)

        if result.get("status") == "completed":
            logger.info("evening job completed in %ds", duration)
        else:
            logger.error("evening job failed: %s", result.get("error"))
            await state_server.log_error(f"evening: {result.get('error')}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("evening job exception")
        await send_twilio_notification(f"🚨 Evening job error: {exc}")


async def notification_job() -> None:
    """Pure-Python notification — no LLM, deterministic message from state."""
    logger.info("Notification job triggered")
    try:
        await state_server.init_db()
        today = await state_server.get_today_state()

        if not today.get("exists"):
            logger.info("no state for today; sending skip notice")
            await send_twilio_notification("📅 No automation ran today (holiday/weekend/leave).")
            return

        message = _build_notification_message(today)
        success = await send_twilio_notification(message)
        await state_server.set_today_state(
            notification_done=1 if success else 0,
            notification_channel="whatsapp" if success else "failed",
        )
        logger.info("notification sent" if success else "notification failed")
    except Exception:  # noqa: BLE001
        logger.exception("notification job exception")


def _build_notification_message(state: Dict[str, Any]) -> str:
    day_number = state.get("day_number") or "?"
    date_str = state.get("run_date") or date.today().isoformat()
    subtask = state.get("subtask_key") or "UNKNOWN"

    morning = bool(state.get("morning_done"))
    evening = bool(state.get("evening_done"))
    timesheet = bool(state.get("timesheet_done"))

    morning_line = f"✅ Subtask created: {subtask}" if morning else "❌ Subtask creation FAILED"
    evening_line = "✅ Worklog submitted (8h @ 11 AM)" if evening else "❌ Worklog submission FAILED"
    timesheet_line = (
        "✅ Timesheet synced (8h confirmed)" if timesheet
        else "⚠️ Timesheet sync not confirmed"
    )
    overall = "🎉 Today's routine completed!" if (morning and evening and timesheet) else "⚠️ Some steps failed — check logs"

    return (
        "📊 Daily Automation Report\n"
        f"📅 {date_str}\n"
        f"Internship Day {day_number}\n"
        "─────────────────────\n"
        f"{morning_line}\n\n"
        f"{evening_line}\n\n"
        f"{timesheet_line}\n"
        "─────────────────────\n"
        f"{overall}"
    )


async def monthly_reminder_job() -> None:
    logger.info("Monthly reminder triggered")
    message = (
        "📋 Monthly Intern Automation Check\n\n"
        "🔐 Security:\n"
        "• Jira API token age check (rotate if >90 days old)\n"
        "• Twilio credentials still valid?\n"
        "• .env file secured?\n\n"
        "📊 Progress:\n"
        "• Days automated this month?\n"
        "• Any persistent failures?\n\n"
        "Rotation:\n"
        "• Jira token: id.atlassian.com → Security → API Tokens\n"
        "• Twilio: console.twilio.com → Account → Security"
    )
    try:
        await send_twilio_notification(message)
    except Exception:  # noqa: BLE001
        logger.exception("monthly reminder failed")
