"""Run: python scripts/reset_state.py — wipes today's state for a clean rerun."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.state.store import StateStore


async def main():
    store = StateStore()
    await store.init()
    await store.reset_today()
    print("Today's state has been reset. You can now re-run the workflows.")


if __name__ == "__main__":
    asyncio.run(main())
