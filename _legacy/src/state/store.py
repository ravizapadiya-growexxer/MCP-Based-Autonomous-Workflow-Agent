from __future__ import annotations
import json
import aiosqlite
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger
from config.settings import settings
from src.utils.date_utils import today_iso


@dataclass
class DailyState:
    date: str = ""
    story_key: Optional[str] = None
    subtask_keys: list[str] = field(default_factory=list)
    morning_done: bool = False
    evening_done: bool = False
    worklog_id: Optional[str] = None
    timesheet_synced: bool = False
    errors: list[str] = field(default_factory=list)
    screenshot_path: Optional[str] = None


_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_runs (
    date              TEXT PRIMARY KEY,
    story_key         TEXT,
    subtask_keys      TEXT  DEFAULT '[]',
    morning_done      INTEGER DEFAULT 0,
    evening_done      INTEGER DEFAULT 0,
    worklog_id        TEXT,
    timesheet_synced  INTEGER DEFAULT 0,
    errors            TEXT  DEFAULT '[]',
    screenshot_path   TEXT,
    created_at        TEXT  DEFAULT CURRENT_TIMESTAMP,
    updated_at        TEXT  DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS run_log (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    date    TEXT NOT NULL,
    phase   TEXT NOT NULL,
    step    TEXT NOT NULL,
    status  TEXT NOT NULL,
    detail  TEXT,
    ts      TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


class StateStore:
    def __init__(self, db_path: str = settings.db_path):
        self._path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    async def init(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.executescript(_SCHEMA)
            await db.commit()

    async def get_today(self) -> Optional[DailyState]:
        today = today_iso()
        async with aiosqlite.connect(self._path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM daily_runs WHERE date = ?", (today,)
            ) as cur:
                row = await cur.fetchone()
        if not row:
            return None
        return DailyState(
            date=row["date"],
            story_key=row["story_key"],
            subtask_keys=json.loads(row["subtask_keys"]),
            morning_done=bool(row["morning_done"]),
            evening_done=bool(row["evening_done"]),
            worklog_id=row["worklog_id"],
            timesheet_synced=bool(row["timesheet_synced"]),
            errors=json.loads(row["errors"]),
            screenshot_path=row["screenshot_path"],
        )

    async def upsert(self, **patch) -> None:
        today = today_iso()
        existing = await self.get_today() or DailyState(date=today)
        for k, v in patch.items():
            setattr(existing, k, v)

        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                """
                INSERT INTO daily_runs
                    (date, story_key, subtask_keys, morning_done, evening_done,
                     worklog_id, timesheet_synced, errors, screenshot_path, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(date) DO UPDATE SET
                    story_key        = excluded.story_key,
                    subtask_keys     = excluded.subtask_keys,
                    morning_done     = excluded.morning_done,
                    evening_done     = excluded.evening_done,
                    worklog_id       = excluded.worklog_id,
                    timesheet_synced = excluded.timesheet_synced,
                    errors           = excluded.errors,
                    screenshot_path  = excluded.screenshot_path,
                    updated_at       = excluded.updated_at
                """,
                (
                    existing.date,
                    existing.story_key,
                    json.dumps(existing.subtask_keys),
                    int(existing.morning_done),
                    int(existing.evening_done),
                    existing.worklog_id,
                    int(existing.timesheet_synced),
                    json.dumps(existing.errors),
                    existing.screenshot_path,
                ),
            )
            await db.commit()

    async def log_step(self, phase: str, step: str, status: str, detail: str = "") -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute(
                "INSERT INTO run_log (date, phase, step, status, detail) VALUES (?, ?, ?, ?, ?)",
                (today_iso(), phase, step, status, detail),
            )
            await db.commit()

    async def append_error(self, error: str) -> None:
        state = await self.get_today() or DailyState(date=today_iso())
        errors = state.errors + [error]
        await self.upsert(errors=errors)

    async def reset_today(self) -> None:
        async with aiosqlite.connect(self._path) as db:
            await db.execute("DELETE FROM daily_runs WHERE date = ?", (today_iso(),))
            await db.commit()
        logger.warning(f"Today's state ({today_iso()}) has been reset")
