"""State store for daily automation runs (SQLite via aiosqlite).

Exposed as a class so the agent's in-process tool registry can call it
directly. (The earlier `@server.tool()` decorator was non-functional on the
low-level mcp.Server class — see _legacy/ for context.)
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional

import aiosqlite
import holidays

from config.holidays_config import COMPANY_HOLIDAYS
from config.settings import settings

logger = logging.getLogger(__name__)


class StateMCPServer:
    """Persistent state for the morning/evening/notification jobs."""

    def __init__(self, db_path: Optional[str] = None, start_date: Optional[str] = None) -> None:
        self.db_path = db_path or settings.state_db_path
        # Lazy: validated on first call so import works without .env
        self._start_date_str = start_date or settings.intern_start_date
        self._start_date: Optional[date] = None
        self._india_holidays: Optional[holidays.HolidayBase] = None
        self._db_initialized = False

    # ---- helpers -----------------------------------------------------------

    def _get_start_date(self) -> date:
        if self._start_date is None:
            if not self._start_date_str:
                raise RuntimeError("INTERN_START_DATE is not configured")
            self._start_date = date.fromisoformat(self._start_date_str)
        return self._start_date

    def _get_india_holidays(self, year: int) -> holidays.HolidayBase:
        # holidays library caches per-instance; build once spanning likely years
        if self._india_holidays is None or year not in self._india_holidays.years:
            start = self._get_start_date().year
            self._india_holidays = holidays.India(years=range(start, year + 2))
        return self._india_holidays

    async def init_db(self) -> None:
        """Idempotent table creation. Safe to call repeatedly."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_runs (
                    run_date TEXT PRIMARY KEY,
                    day_number INTEGER,
                    subtask_key TEXT,
                    morning_done INTEGER DEFAULT 0,
                    evening_done INTEGER DEFAULT 0,
                    timesheet_done INTEGER DEFAULT 0,
                    notification_done INTEGER DEFAULT 0,
                    notification_channel TEXT,
                    notification_sid TEXT,
                    morning_duration_sec INTEGER,
                    evening_duration_sec INTEGER,
                    is_leave_day INTEGER DEFAULT 0,
                    skip_reason TEXT,
                    error_log TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
                """
            )
            await db.commit()
        self._db_initialized = True

    async def _ensure_db(self) -> None:
        if not self._db_initialized:
            await self.init_db()

    # ---- tools -------------------------------------------------------------

    async def get_today_state(self) -> Dict[str, Any]:
        await self._ensure_db()
        today = date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM daily_runs WHERE run_date = ?", (today,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {**dict(row), "exists": True}
                return {"exists": False}

    async def set_today_state(self, **kwargs: Any) -> Dict[str, Any]:
        await self._ensure_db()
        today = date.today().isoformat()
        now = datetime.now().isoformat()

        # Strip None values so we don't overwrite columns the caller didn't set
        updates = {k: v for k, v in kwargs.items() if v is not None}
        if not updates:
            return {"status": "noop"}

        allowed = {
            "day_number", "subtask_key", "morning_done", "evening_done",
            "timesheet_done", "notification_done", "notification_channel",
            "notification_sid", "morning_duration_sec", "evening_duration_sec",
            "is_leave_day", "skip_reason", "error_log",
        }
        unknown = set(updates) - allowed
        if unknown:
            raise ValueError(f"unknown state fields: {sorted(unknown)}")

        set_clause = ", ".join(f"{k} = ?" for k in updates)
        values = list(updates.values())

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO daily_runs (run_date, created_at, updated_at) VALUES (?, ?, ?)",
                (today, now, now),
            )
            await db.execute(
                f"UPDATE daily_runs SET {set_clause}, updated_at = ? WHERE run_date = ?",
                (*values, now, today),
            )
            await db.commit()
        return {"status": "updated", "fields": list(updates.keys())}

    async def get_day_number(self) -> Dict[str, int]:
        """Working days (Mon-Fri minus holidays) elapsed up to and including today."""
        await self._ensure_db()
        today = date.today()
        start = self._get_start_date()
        india = self._get_india_holidays(today.year)

        if today < start:
            return {"day_number": 0}

        day_count = 0
        current = start
        one_day = timedelta(days=1)
        while current <= today:
            is_weekend = current.weekday() >= 5
            is_national = current in india
            is_company = current.isoformat() in COMPANY_HOLIDAYS
            if not (is_weekend or is_national or is_company):
                day_count += 1
            current += one_day
        return {"day_number": day_count}

    async def get_config(self, key: str) -> Dict[str, Any]:
        await self._ensure_db()
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT value FROM config WHERE key = ?", (key,)
            ) as cursor:
                row = await cursor.fetchone()
                return {"key": key, "value": row[0] if row else None}

    async def set_config(self, key: str, value: str) -> Dict[str, str]:
        await self._ensure_db()
        now = datetime.now().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO config (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, now),
            )
            await db.commit()
        return {"status": "set", "key": key}

    async def log_error(self, message: str) -> Dict[str, str]:
        await self._ensure_db()
        today = date.today().isoformat()
        now = datetime.now().isoformat()
        # Make sure the row exists first so the UPDATE has something to hit.
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO daily_runs (run_date, created_at, updated_at) VALUES (?, ?, ?)",
                (today, now, now),
            )
            async with db.execute(
                "SELECT error_log FROM daily_runs WHERE run_date = ?", (today,)
            ) as cursor:
                row = await cursor.fetchone()
                current_log = row[0] if row and row[0] else ""
            entry = f"[{now}] {message}\n"
            new_log = (current_log + entry) if current_log else entry
            await db.execute(
                "UPDATE daily_runs SET error_log = ?, updated_at = ? WHERE run_date = ?",
                (new_log, now, today),
            )
            await db.commit()
        return {"status": "logged"}

    async def get_historical_state(self, target_date: str) -> Dict[str, Any]:
        await self._ensure_db()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM daily_runs WHERE run_date = ?", (target_date,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {**dict(row), "exists": True}
                return {"exists": False}


# Module-level singleton — imported by agent.client and scheduler.jobs
state_server = StateMCPServer()
