"""First-time setup wizard.

Validates configuration, exercises Jira/Twilio connectivity, initializes the
SQLite state database, and creates required directories.

Run: `python scripts/setup.py`
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import date
from pathlib import Path
from typing import Awaitable, Callable, List, Tuple

from config.settings import settings
from mcp_servers.jira_mcp.server import jira_server
from mcp_servers.state_mcp.server import state_server
from notifications.twilio_client import send_twilio_notification

GREEN, RED, YELLOW, BLUE, RESET, BOLD = (
    "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[0m", "\033[1m"
)


def header(text: str) -> None:
    print(f"\n{BOLD}{BLUE}{text}{RESET}")
    print("=" * 60)


def ok(text: str) -> None:
    print(f"{GREEN}✅ {text}{RESET}")


def fail(text: str) -> None:
    print(f"{RED}❌ {text}{RESET}")


def warn(text: str) -> None:
    print(f"{YELLOW}⚠️  {text}{RESET}")


def info(text: str) -> None:
    print(f"{BLUE}ℹ️  {text}{RESET}")


async def validate_env() -> bool:
    header("Step 1: Configuration")
    issues = settings.validate_all()
    if not issues:
        ok("All required configuration is populated")
        return True
    for issue in issues:
        fail(f"{issue.field.upper()}: {issue.message}")
    info(f"\n{len(issues)} value(s) missing. Edit .env and re-run setup.")
    return False


async def validate_jira() -> bool:
    header("Step 2: Jira API")
    issues = settings.validate_jira()
    if issues:
        warn("Jira not fully configured; skipping connectivity test")
        return False
    try:
        me = await jira_server.get_my_account_id()
        if not me.get("accountId"):
            fail("Could not resolve account id")
            return False
        ok(f"Authenticated as {me.get('displayName')} ({me.get('emailAddress')})")
        info(f"Account ID: {me.get('accountId')}")

        parent = await jira_server.get_parent_story()
        if parent.get("error"):
            fail(parent["error"])
            return False
        ok(f"Parent story: {parent.get('issue_key')} — {parent.get('summary')}")
        info(f"Project: {parent.get('project_key')}, Status: {parent.get('status')}")
        return True
    except Exception as exc:  # noqa: BLE001
        fail(f"Jira validation failed: {exc}")
        return False


async def validate_twilio() -> bool:
    header("Step 3: Twilio")
    issues = settings.validate_twilio()
    if issues:
        warn("Twilio not fully configured; skipping send test")
        return False
    try:
        message = (
            "✅ Intern Automation setup verification\n"
            f"If you received this, Twilio is configured correctly.\n"
            f"Timestamp: {date.today().isoformat()}"
        )
        success = await send_twilio_notification(message)
        if success:
            ok("Test notification sent — check your phone")
            return True
        fail("send_twilio_notification returned False; check logs")
        return False
    except Exception as exc:  # noqa: BLE001
        fail(f"Twilio validation failed: {exc}")
        return False


async def setup_db() -> bool:
    header("Step 4: State database")
    try:
        await state_server.init_db()
        size_kb = os.path.getsize(settings.state_db_path) / 1024
        ok(f"Database ready: {settings.state_db_path} ({size_kb:.1f} KB)")
        return True
    except Exception as exc:  # noqa: BLE001
        fail(f"Database init failed: {exc}")
        return False


async def ensure_dirs() -> bool:
    header("Step 5: Directories")
    dirs = ["data", "data/backups", settings.log_dir, f"{settings.log_dir}/screenshots"]
    all_ok = True
    for path in dirs:
        Path(path).mkdir(parents=True, exist_ok=True)
        if Path(path).is_dir():
            ok(f"{path}/")
        else:
            fail(f"failed to create {path}/")
            all_ok = False
    return all_ok


async def main() -> int:
    print(f"""
{BOLD}{BLUE}╔══════════════════════════════════════════════════════════╗
║  🤖 Intern Automation — Setup Wizard                     ║
╚══════════════════════════════════════════════════════════╝{RESET}
""")

    steps: List[Tuple[str, Callable[[], Awaitable[bool]]]] = [
        ("Configuration", validate_env),
        ("Jira API", validate_jira),
        ("Twilio", validate_twilio),
        ("State database", setup_db),
        ("Directories", ensure_dirs),
    ]
    results = [(name, await fn()) for name, fn in steps]

    header("Summary")
    all_passed = True
    for name, passed in results:
        (ok if passed else fail)(name)
        all_passed = all_passed and passed

    if all_passed:
        print(f"\n{GREEN}{BOLD}✅ Setup complete. Run: python -m scheduler.main_scheduler{RESET}\n")
        return 0
    print(f"\n{YELLOW}{BOLD}⚠️  Setup incomplete — fix the items above and re-run.{RESET}\n")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
