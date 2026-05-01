from datetime import date, datetime
from zoneinfo import ZoneInfo
from config.settings import settings
from config.holidays import HOLIDAYS


def now_local() -> datetime:
    return datetime.now(ZoneInfo(settings.tz))


def today_iso() -> str:
    return now_local().date().isoformat()


def is_weekend() -> bool:
    return now_local().weekday() >= 5  # 5=Sat, 6=Sun


def is_holiday() -> bool:
    return today_iso() in HOLIDAYS


def should_skip() -> tuple[bool, str]:
    if is_weekend():
        return True, f"Weekend ({now_local().strftime('%A')})"
    if is_holiday():
        return True, f"Public Holiday ({today_iso()})"
    return False, ""


def jira_datetime_started() -> str:
    """Return Jira-format started timestamp for today at 9 AM."""
    d = now_local().date()
    return f"{d}T09:00:00.000+0530"
