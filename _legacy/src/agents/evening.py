"""
Evening workflow — runs at 7 PM, Mon–Fri, non-holidays.

Steps:
  1. Skip check (weekend / holiday / already done)
  2. Get today's story from state (must have morning_done=True)
  3. Mark subtask → Done
  4. Mark story → Done
  5. Add 8h worklog to story
  6. Browser: open timesheet portal → click Sync
  7. Save state, send WhatsApp alert
"""

from __future__ import annotations
from loguru import logger
from src.utils.logger import setup_logger
from src.utils.date_utils import should_skip, today_iso
from src.state.store import StateStore
from src.jira_client.client import JiraClient
from src.browser.timesheet import TimesheetBrowser
from src.notifications.whatsapp import (
    send_whatsapp,
    fmt_evening_success,
    fmt_error,
    fmt_skip,
)


async def run_evening() -> dict:
    setup_logger("evening")
    logger.info("=" * 50)
    logger.info(f"EVENING AGENT START — {today_iso()}")

    result = {
        "success": False,
        "worklog_id": None,
        "timesheet_synced": False,
        "screenshot_path": None,
        "error": None,
    }

    # ── 1. Skip guard ─────────────────────────────────────────────────────────
    skip, reason = should_skip()
    if skip:
        msg = fmt_skip("evening", reason)
        logger.info(msg)
        await send_whatsapp(msg)
        result["error"] = reason
        return result

    store = StateStore()
    await store.init()

    state = await store.get_today()

    if state and state.evening_done:
        logger.info("Evening workflow already completed today — skipping")
        result["success"] = True
        return result

    if not state or not state.morning_done:
        msg = "Evening skipped: morning workflow was not completed today"
        logger.warning(msg)
        await send_whatsapp(f"⚠️ {msg}")
        result["error"] = msg
        return result

    story_key = state.story_key
    subtask_keys = state.subtask_keys
    jira = JiraClient()
    ts_success = False
    screenshot_path = ""

    try:
        # ── 2. Mark subtasks Done ─────────────────────────────────────────────
        for key in subtask_keys:
            await store.log_step("evening", f"done_{key}", "running")
            await jira.mark_done(key)
            await store.log_step("evening", f"done_{key}", "success")
            logger.info(f"Marked {key} → Done")

        # ── 3. Mark story Done ────────────────────────────────────────────────
        await store.log_step("evening", "done_story", "running")
        await jira.mark_done(story_key)
        await store.log_step("evening", "done_story", "success")
        logger.info(f"Marked {story_key} → Done")

        # ── 4. Add 8h worklog ─────────────────────────────────────────────────
        await store.log_step("evening", "worklog", "running")
        worklog_id = await jira.add_worklog(story_key, hours=8)
        await store.upsert(worklog_id=worklog_id)
        await store.log_step("evening", "worklog", "success", worklog_id)
        result["worklog_id"] = worklog_id

        # ── 5. Timesheet browser sync ─────────────────────────────────────────
        await store.log_step("evening", "timesheet_sync", "running")
        browser = TimesheetBrowser()
        ts_success, screenshot_path = await browser.sync_timesheet()
        await store.upsert(timesheet_synced=ts_success, screenshot_path=screenshot_path)

        if ts_success:
            await store.log_step("evening", "timesheet_sync", "success", screenshot_path)
        else:
            await store.log_step("evening", "timesheet_sync", "failure", screenshot_path)
            logger.error("Timesheet sync failed — Jira steps were still successful")

        result["screenshot_path"] = screenshot_path
        result["timesheet_synced"] = ts_success

        # ── 6. Persist and notify ─────────────────────────────────────────────
        await store.upsert(evening_done=True)
        msg = fmt_evening_success(story_key, ts_success)
        await send_whatsapp(msg)
        logger.info("EVENING AGENT COMPLETE ✓")
        result["success"] = True

    except Exception as exc:
        err_msg = str(exc)
        logger.exception(f"Evening agent failed: {err_msg}")
        await store.append_error(err_msg)
        await store.log_step("evening", "fatal", "failure", err_msg)
        await send_whatsapp(fmt_error("evening", err_msg))
        result["error"] = err_msg

    return result
