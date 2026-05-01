"""Probe Jira connectivity (read-only)."""

from __future__ import annotations

import asyncio
import logging
import sys

from mcp_servers.jira_mcp.server import jira_server


async def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    print("\n" + "=" * 60)
    print("Jira connectivity test")
    print("=" * 60 + "\n")

    tests = [
        ("get_my_account_id", jira_server.get_my_account_id()),
        ("get_parent_story", jira_server.get_parent_story()),
    ]

    failures = 0
    for name, coro in tests:
        print(f"-> {name}", end=" ... ")
        try:
            result = await coro
            print("OK")
            print(f"   {result}")
        except Exception as exc:  # noqa: BLE001
            print("FAIL")
            print(f"   {type(exc).__name__}: {exc}")
            failures += 1
    print()
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
