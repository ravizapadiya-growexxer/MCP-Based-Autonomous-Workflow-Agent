from __future__ import annotations
import asyncio
from pathlib import Path
from datetime import datetime
from loguru import logger
from playwright.async_api import async_playwright, Page, TimeoutError as PwTimeout
from config.settings import settings
from src.utils.date_utils import today_iso


class TimesheetBrowser:
    """Playwright-based automation for the company timesheet portal."""

    SCREENSHOT_DIR = Path(settings.log_dir) / "screenshots"

    def __init__(self) -> None:
        self.SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    async def _screenshot(self, page: Page, name: str) -> str:
        ts = datetime.now().strftime("%H%M%S")
        path = str(self.SCREENSHOT_DIR / f"{today_iso()}_{name}_{ts}.png")
        await page.screenshot(path=path, full_page=True)
        logger.info(f"Screenshot saved: {path}")
        return path

    async def _click_by_text(self, page: Page, text: str, timeout: int = 10_000) -> bool:
        """Try to click a button by its visible text, return True on success."""
        try:
            # Try button with exact text
            btn = page.get_by_role("button", name=text, exact=False)
            await btn.wait_for(timeout=timeout)
            await btn.click()
            return True
        except PwTimeout:
            pass
        try:
            # Fallback: any element containing the text
            elem = page.locator(f"text={text}").first
            await elem.wait_for(timeout=5_000)
            await elem.click()
            return True
        except PwTimeout:
            return False

    async def _login(self, page: Page) -> None:
        """Fill login form if it's present."""
        try:
            # Check if login form exists
            username_field = page.locator(settings.ts_username_selector).first
            await username_field.wait_for(timeout=5_000)

            pwd = settings.get_timesheet_password()
            await username_field.fill(settings.timesheet_username)
            await page.locator(settings.ts_password_selector).first.fill(pwd)
            await page.locator(settings.ts_login_button_selector).first.click()

            # Wait for dashboard / redirect away from login
            await page.wait_for_load_state("networkidle", timeout=20_000)
            logger.info("Login successful")
        except PwTimeout:
            logger.info("No login form detected — assuming already authenticated")

    async def sync_timesheet(self) -> tuple[bool, str]:
        """
        Navigate to timesheet portal, click Sync button, take screenshots.
        Returns (success: bool, screenshot_path: str)
        """
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=settings.browser_headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent=(
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()
            screenshot_path = ""

            try:
                logger.info(f"Navigating to {settings.timesheet_url}")
                await page.goto(settings.timesheet_url, wait_until="domcontentloaded", timeout=30_000)
                await self._login(page)

                # Screenshot: before sync
                screenshot_path = await self._screenshot(page, "before_sync")

                if settings.dry_run:
                    logger.info(f"[DRY RUN] Would click '{settings.timesheet_sync_button_text}' button")
                    return True, screenshot_path

                # Click the Sync button
                clicked = await self._click_by_text(page, settings.timesheet_sync_button_text)
                if not clicked:
                    screenshot_path = await self._screenshot(page, "sync_button_not_found")
                    raise RuntimeError(
                        f"Sync button '{settings.timesheet_sync_button_text}' not found on page"
                    )

                logger.info(f"Clicked '{settings.timesheet_sync_button_text}' button")

                # Wait for response (network idle or success indicator)
                await page.wait_for_load_state("networkidle", timeout=20_000)

                # Screenshot: after sync
                screenshot_path = await self._screenshot(page, "after_sync_success")
                logger.info("Timesheet sync completed successfully")
                return True, screenshot_path

            except Exception as exc:
                logger.error(f"Timesheet sync failed: {exc}")
                try:
                    screenshot_path = await self._screenshot(page, "error")
                except Exception:
                    pass
                return False, screenshot_path

            finally:
                await browser.close()
