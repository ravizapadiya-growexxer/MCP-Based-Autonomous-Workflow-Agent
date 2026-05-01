"""Agent orchestration: in-process tool dispatch + Anthropic tool-use loop.

The original v4 plan describes MCP servers as separate stdio subprocesses, but
in practice this single-user automation runs every component in the same
process — there's no external client that needs the MCP protocol. We therefore
expose each "server" as a Python class and dispatch tool calls in-process,
which is simpler, faster, and keeps the same tool surface visible to Claude.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, List, Optional

from anthropic import Anthropic

from config.settings import settings

logger = logging.getLogger(__name__)

ToolHandler = Callable[..., Awaitable[Any]]


@dataclass
class Tool:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: ToolHandler

    def to_anthropic(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class ToolRegistry:
    """Holds the tool catalogue and routes calls to handlers."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"Tool already registered: {tool.name}")
        self._tools[tool.name] = tool

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def to_anthropic_tools(self) -> List[Dict[str, Any]]:
        return [t.to_anthropic() for t in self._tools.values()]

    async def call(self, name: str, arguments: Dict[str, Any]) -> str:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        tool = self._tools[name]
        result = await tool.handler(**(arguments or {}))
        if isinstance(result, str):
            return result
        return json.dumps(result, default=str)


def _obj(properties: Dict[str, Any], required: Optional[List[str]] = None) -> Dict[str, Any]:
    schema: Dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


def build_default_registry() -> ToolRegistry:
    """Wire all tool implementations into a single registry."""
    # Imports are local so unrelated callers (e.g. the notification job)
    # can import this module without paying for Playwright/Anthropic startup.
    from mcp_servers.browser_mcp.server import browser_server
    from mcp_servers.jira_mcp.server import jira_server
    from mcp_servers.notification_mcp.server import notif_server
    from mcp_servers.state_mcp.server import state_server

    reg = ToolRegistry()

    # -- Jira ----------------------------------------------------------------
    reg.register(Tool(
        "jira__get_my_account_id",
        "Get the authenticated user's Jira accountId, displayName, email.",
        _obj({}),
        jira_server.get_my_account_id,
    ))
    reg.register(Tool(
        "jira__get_parent_story",
        "Fetch the configured parent story (issue_key, summary, project_key, status).",
        _obj({}),
        jira_server.get_parent_story,
    ))
    reg.register(Tool(
        "jira__check_subtask_exists",
        "Idempotency check: does a subtask for this working-day already exist?",
        _obj({"day_number": {"type": "integer"}}, ["day_number"]),
        jira_server.check_subtask_exists,
    ))
    reg.register(Tool(
        "jira__create_subtask",
        "Create a new subtask under the parent story.",
        _obj({
            "parent_key": {"type": "string"},
            "summary": {"type": "string"},
            "project_key": {"type": "string"},
        }, ["parent_key", "summary", "project_key"]),
        jira_server.create_subtask,
    ))
    reg.register(Tool(
        "jira__add_label",
        "Add a label to an issue.",
        _obj({
            "issue_key": {"type": "string"},
            "label": {"type": "string"},
        }, ["issue_key", "label"]),
        jira_server.add_label,
    ))
    reg.register(Tool(
        "jira__set_time_estimate",
        "Set the original time estimate (seconds).",
        _obj({
            "issue_key": {"type": "string"},
            "seconds": {"type": "integer"},
        }, ["issue_key", "seconds"]),
        jira_server.set_time_estimate,
    ))
    reg.register(Tool(
        "jira__assign_issue",
        "Assign an issue to a user by accountId.",
        _obj({
            "issue_key": {"type": "string"},
            "account_id": {"type": "string"},
        }, ["issue_key", "account_id"]),
        jira_server.assign_issue,
    ))
    reg.register(Tool(
        "jira__get_issue_transitions",
        "List available workflow transitions for an issue.",
        _obj({"issue_key": {"type": "string"}}, ["issue_key"]),
        jira_server.get_issue_transitions,
    ))
    reg.register(Tool(
        "jira__transition_issue",
        "Transition an issue using a transition id.",
        _obj({
            "issue_key": {"type": "string"},
            "transition_id": {"type": "string"},
        }, ["issue_key", "transition_id"]),
        jira_server.transition_issue,
    ))
    reg.register(Tool(
        "jira__add_worklog",
        "Add a worklog entry. `started` MUST be ISO 8601 with +0530 offset.",
        _obj({
            "issue_key": {"type": "string"},
            "started": {"type": "string"},
            "time_spent": {"type": "string"},
        }, ["issue_key", "started", "time_spent"]),
        jira_server.add_worklog,
    ))

    # -- State ---------------------------------------------------------------
    reg.register(Tool(
        "state__get_today_state",
        "Read today's row from daily_runs.",
        _obj({}),
        state_server.get_today_state,
    ))
    reg.register(Tool(
        "state__set_today_state",
        "Upsert fields into today's daily_runs row.",
        _obj({
            "subtask_key": {"type": ["string", "null"]},
            "morning_done": {"type": ["integer", "null"]},
            "evening_done": {"type": ["integer", "null"]},
            "timesheet_done": {"type": ["integer", "null"]},
            "day_number": {"type": ["integer", "null"]},
            "morning_duration_sec": {"type": ["integer", "null"]},
            "evening_duration_sec": {"type": ["integer", "null"]},
            "skip_reason": {"type": ["string", "null"]},
        }),
        state_server.set_today_state,
    ))
    reg.register(Tool(
        "state__get_day_number",
        "Calculate working-day count (Mon-Fri minus holidays) since start_date.",
        _obj({}),
        state_server.get_day_number,
    ))
    reg.register(Tool(
        "state__log_error",
        "Append a timestamped error message to today's error_log.",
        _obj({"message": {"type": "string"}}, ["message"]),
        state_server.log_error,
    ))

    # -- Notifications -------------------------------------------------------
    reg.register(Tool(
        "notification__send_whatsapp",
        "Send a WhatsApp message via Twilio.",
        _obj({"message": {"type": "string"}}, ["message"]),
        notif_server.send_whatsapp,
    ))
    reg.register(Tool(
        "notification__send_sms",
        "Send an SMS via Twilio (fallback or direct).",
        _obj({"message": {"type": "string"}}, ["message"]),
        notif_server.send_sms,
    ))
    reg.register(Tool(
        "notification__send_alert",
        "Send a critical alert via SMS.",
        _obj({"message": {"type": "string"}}, ["message"]),
        notif_server.send_alert,
    ))

    # -- Browser -------------------------------------------------------------
    reg.register(Tool(
        "browser__login_timesheet",
        "Open browser, navigate to timesheet portal, sign in.",
        _obj({}),
        browser_server.login_timesheet,
    ))
    reg.register(Tool(
        "browser__sync_jira_logs",
        "Click the Sync from Jira button on the timesheet portal.",
        _obj({}),
        browser_server.sync_jira_logs,
    ))
    reg.register(Tool(
        "browser__confirm_hours",
        "Verify 8h appears in today's timesheet row.",
        _obj({}),
        browser_server.confirm_hours,
    ))
    reg.register(Tool(
        "browser__take_screenshot",
        "Capture a screenshot of the current page.",
        _obj({"label": {"type": "string"}}, ["label"]),
        browser_server.take_screenshot,
    ))
    reg.register(Tool(
        "browser__get_page_content",
        "Return visible text on the current page (truncated).",
        _obj({}),
        browser_server.get_page_content,
    ))

    return reg


class AgentOrchestrator:
    """Runs an Anthropic tool-use loop against a ToolRegistry."""

    def __init__(self, registry: ToolRegistry, model: Optional[str] = None) -> None:
        self.registry = registry
        self.model = model or settings.anthropic_model
        self._client: Optional[Anthropic] = None

    def _get_client(self) -> Anthropic:
        if self._client is None:
            settings.require("anthropic")
            self._client = Anthropic(api_key=settings.anthropic_api_key)
        return self._client

    async def run(
        self,
        system_prompt: str,
        user_message: str,
        *,
        max_iterations: int = 30,
        max_tokens: int = 4096,
    ) -> str:
        client = self._get_client()
        tools = self.registry.to_anthropic_tools()
        messages: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]

        for iteration in range(1, max_iterations + 1):
            response = client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                tools=tools,
                messages=messages,
            )
            logger.debug(
                "agent iteration=%d stop_reason=%s blocks=%d",
                iteration, response.stop_reason, len(response.content),
            )

            if response.stop_reason == "end_turn":
                return _extract_text(response.content)

            if response.stop_reason != "tool_use":
                logger.warning("Unexpected stop_reason: %s", response.stop_reason)
                return _extract_text(response.content) or f"stop_reason={response.stop_reason}"

            tool_results = await self._dispatch_tool_calls(response.content)
            messages.append({"role": "assistant", "content": [b.model_dump() for b in response.content]})
            messages.append({"role": "user", "content": tool_results})

        logger.error("agent: max iterations (%d) reached", max_iterations)
        return f"max_iterations_reached ({max_iterations})"

    async def _dispatch_tool_calls(self, blocks: List[Any]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for block in blocks:
            if getattr(block, "type", None) != "tool_use":
                continue
            tool_id = block.id
            name = block.name
            args = block.input or {}
            logger.info("tool_call name=%s args=%s", name, _short(args))
            try:
                content = await self.registry.call(name, args)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": content,
                })
            except Exception as exc:  # noqa: BLE001
                logger.exception("tool_call failed name=%s", name)
                results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "is_error": True,
                    "content": json.dumps({"error": str(exc), "type": exc.__class__.__name__}),
                })
        return results


def _extract_text(content_blocks: List[Any]) -> str:
    parts: List[str] = []
    for block in content_blocks:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts)


def _short(value: Any, limit: int = 200) -> str:
    s = json.dumps(value, default=str)
    return s if len(s) <= limit else s[: limit - 3] + "..."
