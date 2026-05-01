from __future__ import annotations
import base64
from datetime import date
from typing import Optional
import httpx
from loguru import logger
from config.settings import settings
from src.utils.retry import make_retry
from src.utils.date_utils import today_iso, jira_datetime_started


class JiraClient:
    """Thin async wrapper around Jira REST API v3."""

    def __init__(self) -> None:
        token = settings.get_jira_api_token()
        creds = base64.b64encode(
            f"{settings.jira_username}:{token}".encode()
        ).decode()
        self._headers = {
            "Authorization": f"Basic {creds}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._base = settings.jira_url.rstrip("/") + "/rest/api/3"

    # ─── Internal helpers ─────────────────────────────────────────────────────

    async def _get(self, path: str, params: dict = None) -> dict:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.get(f"{self._base}{path}", headers=self._headers, params=params)
            r.raise_for_status()
            return r.json()

    async def _post(self, path: str, body: dict) -> dict:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{self._base}{path}", headers=self._headers, json=body)
            r.raise_for_status()
            return r.json()

    async def _put(self, path: str, body: dict) -> None:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.put(f"{self._base}{path}", headers=self._headers, json=body)
            r.raise_for_status()

    # ─── Story operations ─────────────────────────────────────────────────────

    @make_retry()
    async def search_story_today(self) -> Optional[str]:
        """Return issue key if a story for today already exists, else None."""
        today = today_iso()
        jql = (
            f'project = "{settings.jira_project_key}" '
            f'AND summary ~ "{today}" '
            f'AND issuetype = Story '
            f'AND created >= "{today}"'
        )
        data = await self._get("/search", params={"jql": jql, "maxResults": 1})
        issues = data.get("issues", [])
        if issues:
            key = issues[0]["key"]
            logger.info(f"Found existing story for today: {key}")
            return key
        return None

    @make_retry()
    async def create_story(self) -> str:
        """Create a daily story and return its key."""
        today = today_iso()
        summary = f"[{today}] Daily Development Work"

        body = {
            "fields": {
                "project": {"key": settings.jira_project_key},
                "summary": summary,
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [
                        {"type": "text", "text": f"Daily development tasks for {today}."}
                    ]}],
                },
                "issuetype": {"name": "Story"},
                "timetracking": {
                    "originalEstimate": f"{settings.story_estimate_hours}h"
                },
            }
        }

        if settings.dry_run:
            logger.info(f"[DRY RUN] Would create story: {summary}")
            return "DRY-RUN-STORY"

        data = await self._post("/issue", body)
        key = data["key"]
        logger.info(f"Created story: {key}")
        return key

    @make_retry()
    async def create_subtask(self, parent_key: str, story_summary: str) -> str:
        """Create a single subtask under the parent story.

        Name format: name_surname - <story summary>
        e.g.  ravi_zapadiya - [2026-04-28] Daily Development Work
        """
        title = settings.subtask_title(story_summary)
        body = {
            "fields": {
                "project": {"key": settings.jira_project_key},
                "parent": {"key": parent_key},
                "summary": title,
                "issuetype": {"name": "Subtask"},
            }
        }

        if settings.dry_run:
            logger.info(f"[DRY RUN] Would create subtask: {title}")
            return "DRY-RUN-SUBTASK"

        data = await self._post("/issue", body)
        key = data["key"]
        logger.info(f"Created subtask: {key} — {title}")
        return key

    async def create_all_subtasks(self, parent_key: str, story_summary: str) -> list[str]:
        """Create the single required subtask and return a one-element list."""
        key = await self.create_subtask(parent_key, story_summary)
        return [key]

    # ─── Assignment ───────────────────────────────────────────────────────────

    @make_retry()
    async def assign_issue(self, issue_key: str) -> None:
        """Assign issue to the configured account ID."""
        if settings.dry_run:
            logger.info(f"[DRY RUN] Would assign {issue_key}")
            return
        await self._put(
            f"/issue/{issue_key}/assignee",
            {"accountId": settings.jira_assignee_account_id},
        )
        logger.info(f"Assigned {issue_key} to {settings.jira_assignee_account_id}")

    # ─── Transitions ─────────────────────────────────────────────────────────

    async def get_transitions(self, issue_key: str) -> list[dict]:
        """Return available transitions — use this once to find the right IDs."""
        data = await self._get(f"/issue/{issue_key}/transitions")
        return [{"id": t["id"], "name": t["name"]} for t in data.get("transitions", [])]

    @make_retry()
    async def transition_issue(self, issue_key: str, transition_id: str) -> None:
        """Move issue to a new status via transition ID."""
        if settings.dry_run:
            logger.info(f"[DRY RUN] Would transition {issue_key} → {transition_id}")
            return
        await self._post(
            f"/issue/{issue_key}/transitions",
            {"transition": {"id": transition_id}},
        )
        logger.info(f"Transitioned {issue_key} → transition {transition_id}")

    async def move_to_in_progress(self, issue_key: str) -> None:
        await self.transition_issue(issue_key, settings.jira_in_progress_transition_id)

    async def mark_done(self, issue_key: str) -> None:
        await self.transition_issue(issue_key, settings.jira_done_transition_id)

    # ─── Worklog ─────────────────────────────────────────────────────────────

    @make_retry()
    async def add_worklog(self, issue_key: str, hours: int = 8) -> str:
        """Add a worklog entry and return its ID."""
        body = {
            "timeSpent": f"{hours}h",
            "started": jira_datetime_started(),
            "comment": {
                "type": "doc",
                "version": 1,
                "content": [{"type": "paragraph", "content": [
                    {"type": "text", "text": f"Daily development work — {today_iso()}"}
                ]}],
            },
        }

        if settings.dry_run:
            logger.info(f"[DRY RUN] Would add {hours}h worklog to {issue_key}")
            return "DRY-RUN-WORKLOG"

        data = await self._post(f"/issue/{issue_key}/worklog", body)
        worklog_id = data["id"]
        logger.info(f"Added {hours}h worklog to {issue_key} (id={worklog_id})")
        return worklog_id
