"""Jira REST API v3 client. Exposes the tool surface for the agent."""

from __future__ import annotations

import base64
import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import (
    AsyncRetrying,
    RetryError,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(30.0, connect=10.0)
RETRYABLE_EXCEPTIONS = (httpx.TransportError, httpx.HTTPStatusError)


class JiraMCPServer:
    def __init__(self) -> None:
        # Pull lazily; agents using only state/notif don't need Jira creds.
        self._auth_header: Optional[str] = None

    # ---- internals ---------------------------------------------------------

    def _require(self) -> None:
        settings.require("jira")

    def _base_url(self) -> str:
        return settings.jira_base_url.rstrip("/")

    def _auth(self) -> Dict[str, str]:
        if self._auth_header is None:
            credentials = f"{settings.jira_email}:{settings.jira_api_token}"
            encoded = base64.b64encode(credentials.encode()).decode()
            self._auth_header = f"Basic {encoded}"
        return {
            "Authorization": self._auth_header,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        self._require()
        url = f"{self._base_url()}/rest/api/3{endpoint}"
        retry = AsyncRetrying(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            retry=retry_if_exception_type(
                (httpx.TransportError, httpx.ReadTimeout, httpx.ConnectTimeout)
            ),
            reraise=True,
        )
        try:
            async for attempt in retry:
                with attempt:
                    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                        response = await client.request(
                            method, url, headers=self._auth(), **kwargs
                        )
                        if response.status_code >= 400:
                            logger.error(
                                "jira %s %s -> %d: %s",
                                method, endpoint, response.status_code,
                                response.text[:500],
                            )
                            response.raise_for_status()
                        if not response.text:
                            return {}
                        return response.json()
        except RetryError as exc:
            raise exc.last_attempt.exception()  # noqa: B904
        return {}  # unreachable

    # ---- tools -------------------------------------------------------------

    async def get_my_account_id(self) -> Dict[str, Any]:
        result = await self._request("GET", "/myself")
        return {
            "accountId": result.get("accountId"),
            "displayName": result.get("displayName"),
            "emailAddress": result.get("emailAddress"),
        }

    async def get_parent_story(self) -> Dict[str, Any]:
        """Direct GET on the configured parent key."""
        parent_key = settings.jira_parent_key
        if not parent_key:
            raise RuntimeError("JIRA_PARENT_KEY is not configured")
        issue = await self._request(
            "GET", f"/issue/{parent_key}",
            params={"fields": "summary,project,status"},
        )
        if not issue:
            return {"error": f"Parent story {parent_key} not found"}
        fields = issue.get("fields", {})
        return {
            "issue_key": issue.get("key"),
            "summary": fields.get("summary"),
            "project_key": fields.get("project", {}).get("key"),
            "status": fields.get("status", {}).get("name"),
        }

    async def check_subtask_exists(self, day_number: int) -> Dict[str, Any]:
        """Idempotency: any subtask under the parent whose summary contains day_N."""
        parent_key = settings.jira_parent_key
        prefix = settings.my_username_prefix
        # Match summary on day_N AND our username prefix to avoid colliding
        # with other automation users sharing the same parent story.
        jql_parts = [
            f'parent = "{parent_key}"',
            f'summary ~ "day_{day_number}"',
        ]
        if prefix:
            jql_parts.append(f'summary ~ "{prefix}"')
        jql = " AND ".join(jql_parts)
        result = await self._request("GET", "/search", params={"jql": jql, "fields": "summary"})
        for issue in result.get("issues", []):
            summary = issue.get("fields", {}).get("summary", "")
            if f"day_{day_number}" in summary and (not prefix or prefix in summary):
                return {"exists": True, "issue_key": issue["key"], "summary": summary}
        return {"exists": False}

    async def create_subtask(self, parent_key: str, summary: str, project_key: str) -> Dict[str, Any]:
        payload = {
            "fields": {
                "project": {"key": project_key},
                "parent": {"key": parent_key},
                "summary": summary,
                "issuetype": {"name": "Subtask"},
                "description": {
                    "type": "doc", "version": 1,
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": "Auto-created by intern automation agent"}],
                    }],
                },
            }
        }
        result = await self._request("POST", "/issue", json=payload)
        return {"issue_key": result.get("key"), "issue_id": result.get("id")}

    async def add_label(self, issue_key: str, label: str) -> Dict[str, Any]:
        await self._request(
            "PUT", f"/issue/{issue_key}",
            json={"update": {"labels": [{"add": label}]}},
        )
        return {"status": "label_added", "issue_key": issue_key, "label": label}

    async def set_time_estimate(self, issue_key: str, seconds: int) -> Dict[str, Any]:
        await self._request(
            "PUT", f"/issue/{issue_key}",
            json={"fields": {"timetracking": {"originalEstimate": f"{seconds}s"}}},
        )
        return {"status": "time_estimate_set", "issue_key": issue_key, "seconds": seconds}

    async def assign_issue(self, issue_key: str, account_id: str) -> Dict[str, Any]:
        await self._request("PUT", f"/issue/{issue_key}/assignee", json={"accountId": account_id})
        return {"status": "assigned", "issue_key": issue_key}

    async def get_issue_transitions(self, issue_key: str) -> Dict[str, Any]:
        result = await self._request("GET", f"/issue/{issue_key}/transitions")
        transitions = [
            {
                "id": t["id"],
                "name": t["name"],
                "to_status": t["to"]["name"],
            }
            for t in result.get("transitions", [])
        ]
        return {"transitions": transitions}

    async def transition_issue(self, issue_key: str, transition_id: str) -> Dict[str, Any]:
        await self._request(
            "POST", f"/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
        )
        return {"status": "transitioned", "issue_key": issue_key, "transition_id": transition_id}

    async def add_worklog(self, issue_key: str, started: str, time_spent: str) -> Dict[str, Any]:
        """`started` MUST be ISO 8601 with explicit IST offset, e.g. 2026-01-15T11:00:00.000+0530."""
        if "+0530" not in started and "+05:30" not in started:
            logger.warning("worklog 'started' lacks +0530 offset: %s", started)
        result = await self._request(
            "POST", f"/issue/{issue_key}/worklog",
            json={"started": started, "timeSpent": time_spent},
        )
        return {
            "worklog_id": result.get("id"),
            "time_spent": result.get("timeSpent"),
            "started": result.get("started"),
        }


jira_server = JiraMCPServer()
