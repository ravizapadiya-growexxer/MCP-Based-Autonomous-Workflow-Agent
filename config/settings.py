"""Application settings loaded from .env.

Credential fields default to empty strings so the codebase imports cleanly
before .env is populated. Call `settings.validate()` to surface missing
values before performing any I/O against external services.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ValidationIssue:
    field: str
    message: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Jira
    jira_base_url: str = ""
    jira_email: str = ""
    jira_api_token: str = ""
    jira_parent_key: str = ""
    jira_project_key: str = ""
    my_jira_label: str = ""
    my_username_prefix: str = ""

    # Timesheet portal
    timesheet_url: str = ""
    timesheet_username: str = ""
    timesheet_password: str = ""

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_from_number: str = ""
    twilio_to_number: str = ""
    twilio_channel: str = "whatsapp"

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Application
    state_db_path: str = str(PROJECT_ROOT / "data" / "automation_state.db")
    intern_start_date: str = ""
    timezone: str = "Asia/Kolkata"
    human_approval_mode: bool = False
    dry_run: bool = False
    log_level: str = "INFO"
    log_dir: str = str(PROJECT_ROOT / "logs")

    # Observability
    dashboard_port: int = 5050
    dashboard_token: str = ""

    # Required-for-runtime field groups. Each group is validated independently
    # so we can fail fast for the path the caller actually exercises.
    _JIRA_FIELDS = (
        "jira_base_url", "jira_email", "jira_api_token",
        "jira_parent_key", "jira_project_key", "my_jira_label",
        "my_username_prefix",
    )
    _TIMESHEET_FIELDS = ("timesheet_url", "timesheet_username", "timesheet_password")
    _TWILIO_FIELDS = (
        "twilio_account_sid", "twilio_auth_token",
        "twilio_from_number", "twilio_to_number",
    )
    _ANTHROPIC_FIELDS = ("anthropic_api_key",)
    _APP_FIELDS = ("intern_start_date", "dashboard_token")

    def _missing(self, fields: tuple[str, ...]) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for f in fields:
            value = getattr(self, f, "")
            if not value or value.startswith("<") or value.lower().startswith("sk-ant-api03-..."):
                issues.append(ValidationIssue(f, "missing or placeholder"))
        return issues

    def validate_jira(self) -> List[ValidationIssue]:
        return self._missing(self._JIRA_FIELDS)

    def validate_timesheet(self) -> List[ValidationIssue]:
        return self._missing(self._TIMESHEET_FIELDS)

    def validate_twilio(self) -> List[ValidationIssue]:
        return self._missing(self._TWILIO_FIELDS)

    def validate_anthropic(self) -> List[ValidationIssue]:
        return self._missing(self._ANTHROPIC_FIELDS)

    def validate_app(self) -> List[ValidationIssue]:
        return self._missing(self._APP_FIELDS)

    def validate_all(self) -> List[ValidationIssue]:
        return (
            self.validate_jira()
            + self.validate_timesheet()
            + self.validate_twilio()
            + self.validate_anthropic()
            + self.validate_app()
        )

    def require(self, *groups: str) -> None:
        """Raise RuntimeError if any required group has missing values."""
        validators = {
            "jira": self.validate_jira,
            "timesheet": self.validate_timesheet,
            "twilio": self.validate_twilio,
            "anthropic": self.validate_anthropic,
            "app": self.validate_app,
        }
        issues: List[ValidationIssue] = []
        for g in groups:
            if g not in validators:
                raise ValueError(f"Unknown settings group: {g}")
            issues.extend(validators[g]())
        if issues:
            details = ", ".join(f"{i.field} ({i.message})" for i in issues)
            raise RuntimeError(f"Configuration incomplete for {list(groups)}: {details}")


settings = Settings()
