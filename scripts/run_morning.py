"""Manual trigger for the morning agent."""

from __future__ import annotations

import asyncio
import logging
import sys

from agent.morning_agent import run_morning_agent
from config.settings import settings


async def main() -> int:
    logging.basicConfig(
        level=settings.log_level.upper(),
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    log = logging.getLogger("run_morning")

    log.info("Triggering morning agent manually")
    result = await run_morning_agent()
    log.info("result: %s", result)

    if result.get("status") == "completed":
        print(f"\n✅ Morning workflow completed in {result.get('duration_seconds', 0):.1f}s\n")
        return 0
    if result.get("status") == "skipped":
        print(f"\n⏭️  Skipped: {result.get('reason')}\n")
        return 0
    print(f"\n❌ Morning workflow failed: {result.get('error')}\n")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
