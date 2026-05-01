"""Morning agent — drives the 11:00 AM IST routine via Claude tool use."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from agent.client import AgentOrchestrator, ToolRegistry, build_default_registry
from agent.prompts import MORNING_SYSTEM_PROMPT
from config.settings import settings

logger = logging.getLogger(__name__)


class MorningAgent:
    def __init__(self, registry: Optional[ToolRegistry] = None) -> None:
        self.registry = registry or build_default_registry()
        self.orchestrator = AgentOrchestrator(self.registry)

    async def run(self) -> Dict[str, Any]:
        start = datetime.now()
        logger.info("=== Morning workflow started ===")

        if settings.dry_run:
            logger.warning("DRY_RUN enabled — agent will not be invoked")
            return {"status": "skipped", "reason": "dry_run", "duration_seconds": 0.0}

        user_message = (
            "Execute the morning internship workflow.\n"
            "Steps to perform: read state, look up day_number, ensure subtask exists "
            "(create if missing), assign + estimate + label, transition to In Progress, "
            "update state, send WhatsApp confirmation. Follow the system prompt exactly."
        )

        try:
            result = await self.orchestrator.run(
                system_prompt=MORNING_SYSTEM_PROMPT,
                user_message=user_message,
                max_iterations=30,
            )
            duration = (datetime.now() - start).total_seconds()
            logger.info("Morning workflow completed in %.1fs", duration)
            return {"status": "completed", "duration_seconds": duration, "message": result}
        except Exception as exc:  # noqa: BLE001
            duration = (datetime.now() - start).total_seconds()
            logger.exception("Morning workflow failed")
            return {"status": "failed", "duration_seconds": duration, "error": str(exc)}


async def run_morning_agent() -> Dict[str, Any]:
    return await MorningAgent().run()
