from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional
import keyring


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Jira ──────────────────────────────────────────────────────
    jira_url: str = ""                          # https://company.atlassian.net
    jira_username: str = ""                     # your.email@company.com
    jira_api_token: str = ""                    # Jira API token
    jira_project_key: str = ""                  # e.g. DEV
    jira_assignee_account_id: str = ""          # Your Jira accountId
    jira_in_progress_transition_id: str = "21"  # Discover via /transitions endpoint
    jira_done_transition_id: str = "31"         # Discover via /transitions endpoint
    story_estimate_hours: int = 8               # originalEstimate in hours

    # Assignee name used to build the single subtask title (firstname_lastname)
    jira_assignee_name: str = "name_surname"   # e.g. ravi_zapadiya

    # ── Timesheet Portal ──────────────────────────────────────────
    timesheet_url: str = ""                     # https://timesheet.company.com
    timesheet_username: str = ""
    timesheet_password: str = ""                # Or stored in keyring
    timesheet_sync_button_text: str = "Sync"   # Exact button label

    # CSS/XPath selectors (override if portal changes)
    ts_username_selector: str = "input[name='username'], input[type='email']"
    ts_password_selector: str = "input[name='password'], input[type='password']"
    ts_login_button_selector: str = "button[type='submit']"
    ts_success_selector: str = ".success, .alert-success, [class*='success']"

    # ── User ──────────────────────────────────────────────────────
    user_email: str = "creatorx1235@gmail.com"

    # ── Scheduler ─────────────────────────────────────────────────
    tz: str = "Asia/Kolkata"
    morning_hour: int = 11
    morning_minute: int = 0
    evening_hour: int = 19
    evening_minute: int = 0

    # ── Browser ───────────────────────────────────────────────────
    browser_headless: bool = True

    # ── WhatsApp — CallMeBot (Free for personal use) ──────────────
    # Setup: Add +34 644 59 71 28 in WhatsApp, send "I allow callmebot..."
    # Get API key from https://www.callmebot.com/blog/free-api-whatsapp-messages/
    whatsapp_phone: Optional[str] = None        # +91XXXXXXXXXX (with country code)
    whatsapp_apikey: Optional[str] = None       # Provided by CallMeBot after activation

    # ── WhatsApp — Twilio (Premium, optional) ─────────────────────
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_whatsapp_from: Optional[str] = None  # whatsapp:+14155238886
    twilio_whatsapp_to: Optional[str] = None    # whatsapp:+91XXXXXXXXXX

    # ── Behavior ──────────────────────────────────────────────────
    dry_run: bool = False                       # True = log only, no actual changes
    require_human_approval: bool = False

    # ── Logging ───────────────────────────────────────────────────
    log_level: str = "INFO"
    log_dir: str = "logs"

    # ── Database ──────────────────────────────────────────────────
    db_path: str = "data/agent.db"

    # ── Retry ─────────────────────────────────────────────────────
    retry_max_attempts: int = 3
    retry_wait_seconds: int = 5

    # ── MCP Server ────────────────────────────────────────────────
    mcp_server_host: str = "127.0.0.1"
    mcp_server_port: int = 8000

    def subtask_title(self, story_summary: str) -> str:
        """Build the single subtask name: name_surname - story title."""
        return f"{self.jira_assignee_name} - {story_summary}"

    def get_jira_api_token(self) -> str:
        """Try keyring first, then env."""
        token = keyring.get_password("mcp-agent", "JIRA_API_TOKEN")
        return token or self.jira_api_token

    def get_timesheet_password(self) -> str:
        """Try keyring first, then env."""
        pwd = keyring.get_password("mcp-agent", "TIMESHEET_PASSWORD")
        return pwd or self.timesheet_password


settings = Settings()
