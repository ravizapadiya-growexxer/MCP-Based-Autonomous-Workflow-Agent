"""Run: python scripts/list_transitions.py DEV-1 — find transition IDs for your project."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.jira_client.client import JiraClient


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/list_transitions.py <ISSUE-KEY>")
        sys.exit(1)
    issue_key = sys.argv[1]
    jira = JiraClient()
    transitions = await jira.get_transitions(issue_key)
    print(f"\nTransitions for {issue_key}:")
    for t in transitions:
        print(f"  ID: {t['id']:>5}  Name: {t['name']}")
    print("\nSet JIRA_IN_PROGRESS_TRANSITION_ID and JIRA_DONE_TRANSITION_ID in your .env")


if __name__ == "__main__":
    asyncio.run(main())
