"""Pre-flight checks that decide whether each job should run today."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional, Tuple

import holidays

from config.holidays_config import COMPANY_HOLIDAYS
from mcp_servers.state_mcp.server import StateMCPServer

logger = logging.getLogger(__name__)


def _india_holidays_for(d: date) -> holidays.HolidayBase:
    return holidays.India(years=d.year)


def is_weekend(d: Optional[date] = None) -> bool:
    return (d or date.today()).weekday() >= 5


def is_national_holiday(d: Optional[date] = None) -> Tuple[bool, str]:
    today = d or date.today()
    cal = _india_holidays_for(today)
    name = cal.get(today)
    return (name is not None, name or "")


def is_company_holiday(d: Optional[date] = None) -> Tuple[bool, str]:
    today = d or date.today()
    name = COMPANY_HOLIDAYS.get(today.isoformat())
    return (name is not None, name or "")


async def _safe_today_state(state: StateMCPServer) -> dict:
    try:
        return await state.get_today_state()
    except Exception as exc:  # noqa: BLE001
        logger.warning("could not read today's state: %s", exc)
        return {}


async def _common_skip_reason(state: StateMCPServer) -> Optional[str]:
    today = date.today()

    if is_weekend(today):
        return f"weekend ({today.strftime('%A')})"

    is_national, national_name = is_national_holiday(today)
    if is_national:
        return f"national holiday ({national_name})"

    is_company, company_name = is_company_holiday(today)
    if is_company:
        return f"company holiday ({company_name})"

    today_state = await _safe_today_state(state)
    if today_state.get("is_leave_day") == 1:
        return "marked as leave day"

    return None


async def should_run_morning(state: StateMCPServer) -> Tuple[bool, str]:
    skip = await _common_skip_reason(state)
    if skip:
        return False, f"skipped: {skip}"

    today_state = await _safe_today_state(state)
    if today_state.get("morning_done") == 1:
        return False, "skipped: morning already completed"

    return True, "all checks passed"


async def should_run_evening(state: StateMCPServer) -> Tuple[bool, str]:
    skip = await _common_skip_reason(state)
    if skip:
        return False, f"skipped: {skip}"

    today_state = await _safe_today_state(state)
    if today_state.get("evening_done") == 1:
        return False, "skipped: evening already completed"
    if today_state.get("morning_done") != 1:
        return False, "blocked: morning workflow did not complete"

    return True, "all checks passed"


async def check_catch_up(state: StateMCPServer) -> Optional[str]:
    """If yesterday was a workday with morning done but evening not, return alert text."""
    yesterday = date.today() - timedelta(days=1)
    if is_weekend(yesterday):
        return None
    is_national, _ = is_national_holiday(yesterday)
    is_company, _ = is_company_holiday(yesterday)
    if is_national or is_company:
        return None

    try:
        prior = await state.get_historical_state(yesterday.isoformat())
    except Exception as exc:  # noqa: BLE001
        logger.warning("catch-up check failed: %s", exc)
        return None

    if not prior.get("exists"):
        return None
    if prior.get("morning_done") == 1 and prior.get("evening_done") == 0:
        subtask = prior.get("subtask_key", "UNKNOWN")
        day = prior.get("day_number", "?")
        return (
            f"⚠️ Yesterday's evening routine (Day {day}, {subtask}) was not completed. "
            "Please verify Jira and timesheet manually."
        )
    return None
