"""
Morning workflow — runs at 11 AM, Mon–Fri, non-holidays.

Steps:
  1. Skip check (weekend / holiday / already done)
  2. Search Jira for today's story
  3. Create story if not found
  4. Create 1 subtask (format: name_surname - story title)
  5. Assign all tickets to self
  6. Set 8h estimate (done during create)
  7. Move story to In Progress
  8. Save state, send WhatsApp alert
"""

from __future__ import annotations
from loguru import logger
from src.utils.logger import setup_logger
from src.utils.date_utils import should_skip, today_iso
from src.state.store import StateStore
from src.jira_client.client import JiraClient
from src.notifications.whatsapp import (
    send_whatsapp,
    fmt_morning_success,
    fmt_error,
    fmt_skip,
)
from config.settings import settings


async def run_morning() -> dict:
    setup_logger("morning")
    logger.info("=" * 50)
    logger.info(f"MORNING AGENT START — {today_iso()}")

    result = {"success": False, "story_key": None, "subtask_keys": [], "error": None}

    # ── 1. Skip guard ─────────────────────────────────────────────────────────
    skip, reason = should_skip()
    if skip:
        msg = fmt_skip("morning", reason)
        logger.info(msg)
        await send_whatsapp(msg)
        result["error"] = reason
        return result

    store = StateStore()
    await store.init()

    state = await store.get_today()
    if state and state.morning_done:
        logger.info("Morning workflow already completed today — skipping")
        result["success"] = True
        result["story_key"] = state.story_key
        result["subtask_keys"] = state.subtask_keys
        return result

    jira = JiraClient()

    try:
        # ── 2. Check for existing story ───────────────────────────────────────
        await store.log_step("morning", "search_story", "running")
        story_key = await jira.search_story_today()
        await store.log_step("morning", "search_story", "success", story_key or "none")

        # ── 3. Create story if missing ────────────────────────────────────────
        if not story_key:
            await store.log_step("morning", "create_story", "running")
            story_key = await jira.create_story()
            await store.log_step("morning", "create_story", "success", story_key)
            await store.upsert(story_key=story_key)

        # ── 4. Create single subtask (name_surname - story title) ────────────
        await store.log_step("morning", "create_subtask", "running")
        story_summary = f"[{today_iso()}] Daily Development Work"
        subtask_keys = await jira.create_all_subtasks(story_key, story_summary)
        await store.log_step("morning", "create_subtask", "success", str(subtask_keys))
        await store.upsert(subtask_keys=subtask_keys)

        # ── 5. Assign all issues ──────────────────────────────────────────────
        for key in [story_key] + subtask_keys:
            await store.log_step("morning", f"assign_{key}", "running")
            await jira.assign_issue(key)
            await store.log_step("morning", f"assign_{key}", "success")

        # ── 6. Move story to In Progress ──────────────────────────────────────
        await store.log_step("morning", "in_progress", "running")
        await jira.move_to_in_progress(story_key)
        await store.log_step("morning", "in_progress", "success")

        # ── 7. Persist and notify ─────────────────────────────────────────────
        await store.upsert(morning_done=True)
        subtask_title = settings.subtask_title(story_summary)
        msg = fmt_morning_success(story_key, subtask_keys[0], subtask_title)
        await send_whatsapp(msg)
        logger.info("MORNING AGENT COMPLETE ✓")

        result.update(success=True, story_key=story_key, subtask_keys=subtask_keys)

    except Exception as exc:
        err_msg = str(exc)
        logger.exception(f"Morning agent failed: {err_msg}")
        await store.append_error(err_msg)
        await store.log_step("morning", "fatal", "failure", err_msg)
        await send_whatsapp(fmt_error("morning", err_msg))
        result["error"] = err_msg

    return result
