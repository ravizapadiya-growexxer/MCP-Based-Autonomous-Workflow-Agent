"""Evening agent — drives the 7:00 PM IST routine via Claude tool use."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from agent.client import AgentOrchestrator, ToolRegistry, build_default_registry
from agent.prompts import EVENING_SYSTEM_PROMPT
from config.settings import settings
from mcp_servers.browser_mcp.server import browser_server

logger = logging.getLogger(__name__)


class EveningAgent:
    def __init__(self, registry: Optional[ToolRegistry] = None) -> None:
        self.registry = registry or build_default_registry()
        self.orchestrator = AgentOrchestrator(self.registry)

    async def run(self) -> Dict[str, Any]:
        start = datetime.now()
        logger.info("=== Evening workflow started ===")

        if settings.dry_run:
            logger.warning("DRY_RUN enabled — agent will not be invoked")
            return {"status": "skipped", "reason": "dry_run", "duration_seconds": 0.0}

        user_message = (
            "Execute the evening internship workflow.\n"
            "Steps: read state, transition subtask to Done, add 8h worklog with "
            "+0530 IST offset, sync timesheet portal (login -> sync -> confirm 8h), "
            "update state, send WhatsApp confirmation. Follow the system prompt exactly."
        )

        try:
            result = await self.orchestrator.run(
                system_prompt=EVENING_SYSTEM_PROMPT,
                user_message=user_message,
                max_iterations=30,
            )
            duration = (datetime.now() - start).total_seconds()
            logger.info("Evening workflow completed in %.1fs", duration)
            return {"status": "completed", "duration_seconds": duration, "message": result}
        except Exception as exc:  # noqa: BLE001
            duration = (datetime.now() - start).total_seconds()
            logger.exception("Evening workflow failed")
            return {"status": "failed", "duration_seconds": duration, "error": str(exc)}
        finally:
            # Always release browser resources, even on failure.
            try:
                await browser_server.close()
            except Exception:  # noqa: BLE001
                logger.warning("browser cleanup raised", exc_info=True)


async def run_evening_agent() -> Dict[str, Any]:
    return await EveningAgent().run()
