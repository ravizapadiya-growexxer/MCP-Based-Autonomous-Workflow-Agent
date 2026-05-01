"""
View State — CLI tool to inspect automation state.
Useful for debugging and understanding what has run.
"""

import asyncio
import sys
import argparse
from datetime import date, timedelta
from mcp_servers.state_mcp.server import state_server


async def print_today_state():
    """Print today's state."""
    await state_server.init_db()
    
    state = await state_server.get_today_state()
    
    if not state.get("exists"):
        print("No state recorded for today.")
        return
    
    today_date = date.today()
    print(f"\n{'='*60}")
    print(f"TODAY'S STATE — {today_date.strftime('%A, %B %d, %Y')}")
    print(f"{'='*60}\n")
    
    day_num = state.get("day_number", "?")
    subtask = state.get("subtask_key", "—")
    
    print(f"Day Number:         {day_num}")
    print(f"Subtask Key:        {subtask}")
    print()
    
    morning = "✅" if state.get("morning_done") else "❌"
    evening = "✅" if state.get("evening_done") else "❌"
    timesheet = "✅" if state.get("timesheet_done") else "❌"
    notif = "✅" if state.get("notification_done") else "❌"
    
    print(f"Morning Done:       {morning}")
    print(f"Evening Done:       {evening}")
    print(f"Timesheet Done:     {timesheet}")
    print(f"Notification Done:  {notif}")
    print()
    
    if state.get("skip_reason"):
        print(f"Skip Reason:        {state.get('skip_reason')}")
    
    if state.get("error_log"):
        print(f"\nErrors:")
        print(state.get("error_log"))
    
    print(f"{'='*60}\n")


async def print_history(days: int = 7):
    """Print last N days."""
    await state_server.init_db()
    
    print(f"\n{'='*60}")
    print(f"HISTORY — Last {days} Days")
    print(f"{'='*60}\n")
    
    print(f"{'Date':<12} {'Day':<4} {'Morning':<8} {'Evening':<8} {'Timesheet':<10}")
    print("-" * 60)
    
    for i in range(days):
        target_date = (date.today() - timedelta(days=i)).isoformat()
        state = await state_server.get_historical_state(target_date)
        
        if state.get("exists"):
            day_num = state.get("day_number", "?")
            morning = "✅" if state.get("morning_done") else "❌"
            evening = "✅" if state.get("evening_done") else "❌"
            timesheet = "✅" if state.get("timesheet_done") else "❌"
            
            date_str = target_date[-5:]  # MM-DD
            print(f"{date_str:<12} {day_num:<4} {morning:<8} {evening:<8} {timesheet:<10}")
    
    print(f"{'='*60}\n")


async def main():
    parser = argparse.ArgumentParser(description="View automation state")
    parser.add_argument("--days", type=int, default=7, help="Number of days to show in history")
    parser.add_argument("--history", action="store_true", help="Show history")
    
    args = parser.parse_args()
    
    if args.history:
        await print_history(args.days)
    else:
        await print_today_state()


if __name__ == "__main__":
    asyncio.run(main())