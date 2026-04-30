"""
FastMCP server — exposes agent tools for manual trigger via Claude Desktop.

Run separately:   python mcp_server/server.py
Claude config:    Add to claude_desktop_config.json (see below)
"""

from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from typing import Annotated
from fastmcp import FastMCP
from loguru import logger

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import agents
from src.agents.morning import run_morning
from src.agents.evening import run_evening
from src.state.store import StateStore
from src.jira_client.client import JiraClient
from src.browser.timesheet import TimesheetBrowser
from src.notifications.whatsapp import send_whatsapp
from src.utils.date_utils import today_iso
from config.settings import settings

mcp = FastMCP(
    name="JiraTimesheetAgent",
    description=(
        "Automates daily Jira story creation (11 AM) and timesheet sync (7 PM). "
        "Can also be triggered manually via these tools."
    ),
)


@mcp.tool()
async def run_morning_workflow(dry_run: bool = False) -> dict:
    """
    Run the morning Jira workflow:
    Check/create today's story → create subtasks → assign → estimate → In Progress.
    Set dry_run=True to simulate without making changes.
    """
    if dry_run:
        settings.dry_run = True
    result = await run_morning()
    settings.dry_run = False
    return result


@mcp.tool()
async def run_evening_workflow(dry_run: bool = False) -> dict:
    """
    Run the evening workflow:
    Mark tasks Done → add 8h worklog → open timesheet portal → click Sync.
    Set dry_run=True to simulate without making changes.
    """
    if dry_run:
        settings.dry_run = True
    result = await run_evening()
    settings.dry_run = False
    return result


@mcp.tool()
async def get_daily_status() -> dict:
    """Get today's workflow execution status from the SQLite database."""
    store = StateStore()
    await store.init()
    state = await store.get_today()
    if not state:
        return {"date": today_iso(), "status": "No run recorded today"}
    return {
        "date": state.date,
        "story_key": state.story_key,
        "subtask_keys": state.subtask_keys,
        "morning_done": state.morning_done,
        "evening_done": state.evening_done,
        "worklog_id": state.worklog_id,
        "timesheet_synced": state.timesheet_synced,
        "errors": state.errors,
        "screenshot_path": state.screenshot_path,
    }


@mcp.tool()
async def list_jira_transitions(issue_key: str) -> list[dict]:
    """
    List all available transitions for a Jira issue.
    Use this to find the correct 'In Progress' and 'Done' transition IDs
    for your project — then set them in JIRA_IN_PROGRESS_TRANSITION_ID
    and JIRA_DONE_TRANSITION_ID in your .env file.
    """
    jira = JiraClient()
    transitions = await jira.get_transitions(issue_key)
    return transitions


@mcp.tool()
async def send_test_whatsapp(message: str = "Test from MCP Agent") -> dict:
    """Send a test WhatsApp message to verify your CallMeBot setup."""
    success = await send_whatsapp(f"🧪 Test: {message}")
    return {"sent": success}


@mcp.tool()
async def reset_today_state() -> dict:
    """
    Reset today's state in SQLite — allows re-running morning/evening workflows.
    WARNING: Use only for testing. Does NOT undo Jira changes.
    """
    store = StateStore()
    await store.init()
    await store.reset_today()
    return {"reset": True, "date": today_iso()}


@mcp.tool()
async def take_timesheet_screenshot() -> dict:
    """Navigate to the timesheet portal and take a screenshot (no Sync click)."""
    original = settings.dry_run
    settings.dry_run = True
    browser = TimesheetBrowser()
    success, path = await browser.sync_timesheet()
    settings.dry_run = original
    return {"screenshot_path": path}


if __name__ == "__main__":
    mcp.run()
