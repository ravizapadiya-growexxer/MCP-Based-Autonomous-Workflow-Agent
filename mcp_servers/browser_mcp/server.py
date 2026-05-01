"""Playwright-driven timesheet portal automation.

Persists the Playwright/browser/page session across tool calls so the agent
can chain login -> sync -> confirm. Call `close()` when the workflow ends.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.async_api import (
    Browser,
    Page,
    Playwright,
    async_playwright,
)

from config.settings import settings

logger = logging.getLogger(__name__)

USERNAME_SELECTORS: List[str] = [
    "input[type='email']",
    "input[name='username']",
    "#username",
    "input[placeholder*='email' i]",
]
PASSWORD_SELECTORS: List[str] = [
    "input[type='password']",
    "input[name='password']",
    "#password",
]
SUBMIT_SELECTORS: List[str] = [
    "button[type='submit']",
    ".login-button",
    "button:has-text('Login')",
    "button:has-text('Sign In')",
]
SYNC_SELECTORS: List[str] = [
    "button:has-text('Sync from Jira')",
    "button:has-text('Sync')",
    "button[data-action='sync']",
    "#syncJira",
    ".sync-jira-btn",
]
HOURS_PATTERNS: List[str] = [
    r"\b8\s*h\b",
    r"\b8:00\b",
    r"\b08:00\b",
    r"\b480\s*min\b",
    r"\b8\.0\b",
    r"\b8h\b",
]


class BrowserMCPServer:
    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._lock = asyncio.Lock()
        self._screenshot_dir = Path(settings.log_dir) / "screenshots"

    # ---- session management ------------------------------------------------

    async def _ensure_browser(self) -> Page:
        async with self._lock:
            if self._page is None:
                self._screenshot_dir.mkdir(parents=True, exist_ok=True)
                self._playwright = await async_playwright().start()
                self._browser = await self._playwright.chromium.launch(headless=True)
                self._page = await self._browser.new_page()
            return self._page

    async def close(self) -> None:
        async with self._lock:
            if self._browser is not None:
                try:
                    await self._browser.close()
                except Exception:  # noqa: BLE001
                    logger.warning("browser close raised", exc_info=True)
            if self._playwright is not None:
                try:
                    await self._playwright.stop()
                except Exception:  # noqa: BLE001
                    logger.warning("playwright stop raised", exc_info=True)
            self._browser = None
            self._page = None
            self._playwright = None

    async def _screenshot(self, label: str) -> str:
        if self._page is None:
            return "no_browser_session"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self._screenshot_dir / f"{label}_{timestamp}.png"
        try:
            await self._page.screenshot(full_page=True, path=str(path))
            return str(path)
        except Exception as exc:  # noqa: BLE001
            return f"screenshot_failed: {exc}"

    @staticmethod
    async def _try_fill(page: Page, selectors: List[str], value: str) -> bool:
        for selector in selectors:
            try:
                if await page.query_selector(selector):
                    await page.fill(selector, value)
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    @staticmethod
    async def _try_click(page: Page, selectors: List[str]) -> bool:
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.click()
                    return True
            except Exception:  # noqa: BLE001
                continue
        return False

    # ---- tools -------------------------------------------------------------

    async def login_timesheet(self) -> Dict[str, Any]:
        settings.require("timesheet")
        try:
            page = await self._ensure_browser()
            await page.goto(settings.timesheet_url, wait_until="networkidle")

            if not await self._try_fill(page, USERNAME_SELECTORS, settings.timesheet_username):
                screenshot = await self._screenshot("login_username_notfound")
                return {"status": "failed", "error": "username field not found", "screenshot": screenshot}

            if not await self._try_fill(page, PASSWORD_SELECTORS, settings.timesheet_password):
                screenshot = await self._screenshot("login_password_notfound")
                return {"status": "failed", "error": "password field not found", "screenshot": screenshot}

            if not await self._try_click(page, SUBMIT_SELECTORS):
                screenshot = await self._screenshot("login_submit_notfound")
                return {"status": "failed", "error": "submit button not found", "screenshot": screenshot}

            try:
                await page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:  # noqa: BLE001
                logger.debug("networkidle timed out after login submit; continuing")

            if "login" in page.url.lower():
                screenshot = await self._screenshot("login_failed_still_on_login")
                return {"status": "failed", "error": "still on login page", "screenshot": screenshot}

            return {
                "status": "logged_in",
                "current_url": page.url,
                "page_title": await page.title(),
            }
        except Exception as exc:  # noqa: BLE001
            screenshot = await self._screenshot("login_exception")
            return {"status": "failed", "error": str(exc), "screenshot": screenshot}

    async def sync_jira_logs(self) -> Dict[str, Any]:
        if self._page is None:
            return {"status": "failed", "error": "browser not logged in"}
        try:
            if not await self._try_click(self._page, SYNC_SELECTORS):
                screenshot = await self._screenshot("sync_button_notfound")
                return {"status": "failed", "error": "sync button not found", "screenshot": screenshot}
            try:
                await self._page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:  # noqa: BLE001
                logger.debug("networkidle timed out after sync; continuing")
            await asyncio.sleep(1)
            content = await self._page.inner_text("body")
            return {"status": "synced", "confirmation_text": content[:500]}
        except Exception as exc:  # noqa: BLE001
            screenshot = await self._screenshot("sync_exception")
            return {"status": "failed", "error": str(exc), "screenshot": screenshot}

    async def confirm_hours(self) -> Dict[str, Any]:
        if self._page is None:
            return {"status": "failed", "error": "browser not logged in"}
        try:
            content = await self._page.inner_text("body")
            for pattern in HOURS_PATTERNS:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return {"status": "confirmed", "has_8h": True, "found_text": match.group(0)}
            return {"status": "not_confirmed", "has_8h": False}
        except Exception as exc:  # noqa: BLE001
            screenshot = await self._screenshot("confirm_hours_exception")
            return {"status": "failed", "error": str(exc), "screenshot": screenshot}

    async def take_screenshot(self, label: str = "debug") -> Dict[str, Any]:
        return {"status": "captured", "screenshot_path": await self._screenshot(label)}

    async def get_page_content(self) -> Dict[str, Any]:
        if self._page is None:
            return {"status": "failed", "error": "browser not logged in"}
        try:
            content = await self._page.inner_text("body")
            return {"status": "retrieved", "content": content[:2000]}
        except Exception as exc:  # noqa: BLE001
            return {"status": "failed", "error": str(exc)}


browser_server = BrowserMCPServer()
