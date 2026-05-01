"""FastAPI status server (port 5050) — bearer-auth status JSON, history, dashboard."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse

from config.settings import settings
from mcp_servers.state_mcp.server import state_server

logger = logging.getLogger(__name__)

app = FastAPI(title="Intern Automation Status Server")


def _verify_token(authorization: Optional[str] = Header(None)) -> None:
    expected = settings.dashboard_token
    if not expected:
        raise HTTPException(status_code=503, detail="DASHBOARD_TOKEN not configured")
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    token = authorization[len("Bearer "):]
    if token != expected:
        raise HTTPException(status_code=403, detail="invalid token")


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/status/json")
async def status_json(_: None = Depends(_verify_token)):
    await state_server.init_db()
    today = await state_server.get_today_state()
    return {
        "date": today.get("run_date", date.today().isoformat()),
        "day_number": today.get("day_number"),
        "subtask_key": today.get("subtask_key"),
        "morning_done": bool(today.get("morning_done")),
        "evening_done": bool(today.get("evening_done")),
        "timesheet_done": bool(today.get("timesheet_done")),
        "notification_done": bool(today.get("notification_done")),
        "skip_reason": today.get("skip_reason"),
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/history")
async def history(days: int = 7, _: None = Depends(_verify_token)):
    if days < 1 or days > 90:
        raise HTTPException(status_code=400, detail="days must be 1..90")
    await state_server.init_db()
    rows = []
    for i in range(days):
        target = (date.today() - timedelta(days=i)).isoformat()
        state = await state_server.get_historical_state(target)
        if state.get("exists"):
            rows.append({
                "date": target,
                "day_number": state.get("day_number"),
                "morning_done": bool(state.get("morning_done")),
                "evening_done": bool(state.get("evening_done")),
                "timesheet_done": bool(state.get("timesheet_done")),
                "skip_reason": state.get("skip_reason"),
            })
    return {"history": rows}


@app.get("/status", response_class=HTMLResponse)
async def status_dashboard(_: None = Depends(_verify_token)):
    await state_server.init_db()
    today = await state_server.get_today_state()
    day_number = today.get("day_number", "?")
    subtask = today.get("subtask_key", "—")
    morning_done = bool(today.get("morning_done"))
    evening_done = bool(today.get("evening_done"))
    timesheet_done = bool(today.get("timesheet_done"))
    today_label = date.today().strftime("%A, %d %B %Y")
    overall = "🎉 All done!" if morning_done and evening_done and timesheet_done else "⏳ In progress..."

    def line(label: str, done: bool, note: str) -> str:
        cls = "done" if done else "pending"
        icon = "✅" if done else "⏳"
        return (
            f'<div class="status-item {cls}">'
            f'<div class="icon">{icon}</div>'
            f'<div class="details"><strong>{label}</strong><div class="subtitle">{note}</div></div>'
            f'</div>'
        )

    return f"""<!DOCTYPE html>
<html><head><title>Intern Automation Status</title>
<meta http-equiv="refresh" content="60">
<style>
body{{font-family:sans-serif;margin:20px;background:#f5f5f5}}
.container{{max-width:600px;margin:0 auto;background:white;padding:20px;border-radius:8px;box-shadow:0 2px 4px rgba(0,0,0,.1)}}
h1{{color:#333;text-align:center}}
.status-item{{display:flex;align-items:center;padding:12px;margin:10px 0;background:#f9f9f9;border-radius:4px;border-left:4px solid #ddd}}
.status-item.done{{border-left-color:#4CAF50}}
.status-item.pending{{border-left-color:#FF9800}}
.icon{{font-size:24px;margin-right:15px}}
.subtitle{{color:#666;font-size:12px}}
</style></head>
<body><div class="container">
<h1>🤖 Intern Automation Status</h1>
<p style="text-align:center;color:#666">Last updated: {datetime.now().strftime('%H:%M:%S')} {settings.timezone}</p>
<hr><h2>📅 {today_label}</h2><p>Day {day_number} of internship</p>
{line("Morning routine (11:00 AM)", morning_done, f"Subtask: {subtask}")}
{line("Evening routine (7:00 PM)", evening_done, "Worklog + timesheet")}
{line("Timesheet sync", timesheet_done, "8h confirmed on portal")}
<hr><p style="text-align:center;margin-top:20px">{overall}</p>
</div></body></html>
"""


async def run_status_server() -> None:
    config = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=settings.dashboard_port,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()
