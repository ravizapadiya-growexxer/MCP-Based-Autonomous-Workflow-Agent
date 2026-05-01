# Intern Daily Automation

Daily Jira + timesheet automation orchestrated by Claude. Three scheduled
jobs handle the morning subtask creation, the evening worklog + portal sync,
and a 7:30 PM summary message.

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│  APScheduler (Asia/Kolkata)                                         │
│   11:00 → morning_job()    19:00 → evening_job()    19:30 → notify  │
└──────────────┬───────────────────────┬───────────────────┬─────────┘
       guards passed?           guards passed?       (pure Python)
               │                       │                   │
               ▼                       ▼                   ▼
       MorningAgent            EveningAgent          twilio_client
               │                       │                   │
               ▼                       ▼                   │
       AgentOrchestrator (Anthropic tool-use loop)         │
               │                                           │
               ▼                                           │
       ToolRegistry  (in-process dispatch)                 │
               │                                           │
       ┌───────┼─────────┬──────────────┐                  │
       ▼       ▼         ▼              ▼                  ▼
   JiraSrv  StateSrv  BrowserSrv    NotifySrv           Twilio
   (httpx) (sqlite)  (playwright)  (httpx)
```

The morning/evening jobs run a real Anthropic tool-use loop. The 7:30 PM
notification is deterministic — it reads SQLite and POSTs to Twilio without
involving the LLM.

## Quick start

```bash
# 1. Install
pip install -r requirements.txt
playwright install chromium

# 2. Configure
cp .env.example .env
# edit .env with your credentials

# 3. Validate
python scripts/setup.py

# 4. Run
python -m scheduler.main_scheduler
```

Or via Docker:

```bash
docker compose up -d
docker compose logs -f
```

## Repository layout

| Path | Purpose |
|------|---------|
| `agent/` | Anthropic tool-use loop, prompts, morning/evening agents |
| `mcp_servers/jira_mcp/` | Jira REST API tool surface |
| `mcp_servers/state_mcp/` | SQLite state store + working-day counter |
| `mcp_servers/browser_mcp/` | Playwright timesheet portal automation |
| `mcp_servers/notification_mcp/` | Twilio WhatsApp/SMS senders |
| `scheduler/` | APScheduler entry point, jobs, guard checks |
| `notifications/` | Direct Twilio sender used by the 7:30 PM job |
| `observability/` | FastAPI status server (port 5050) |
| `config/` | Pydantic settings, holiday calendar |
| `scripts/` | Setup wizard, manual triggers, debug tools |
| `_legacy/` | Quarantined older code; not used at runtime |

## Configuration

All settings come from `.env`. See [.env.example](.env.example) for the full
list. Five logical groups are validated independently:

- **jira** — base URL, email, API token, parent/project keys, label, prefix
- **timesheet** — portal URL, username, password
- **twilio** — account SID, auth token, from/to numbers
- **anthropic** — `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL`
- **app** — `INTERN_START_DATE`, `DASHBOARD_TOKEN`

`python scripts/setup.py` reports exactly which fields are missing.

## Daily workflow

### Morning (11:00 IST, Mon–Fri)

1. Guard checks: weekend, national holiday, company holiday, leave day, idempotency.
2. Compute working-day count since `INTERN_START_DATE`.
3. Look up Jira account id + parent story.
4. Idempotency: if a `day_N` subtask already exists, save its key and stop.
5. Create the subtask, apply label, set 8h estimate, assign self.
6. Transition to *In Progress*.
7. Persist state, send WhatsApp confirmation.

### Evening (19:00 IST, Mon–Fri)

1. Guard checks (plus: morning must have completed).
2. Transition today's subtask to *Done*.
3. Add an 8h worklog with explicit `+0530` IST offset.
4. Login to the timesheet portal, click *Sync from Jira*, confirm 8h appears.
5. Persist state, send WhatsApp confirmation.

### Notification (19:30 IST, Mon–Fri)

Deterministic. Reads `daily_runs` for today, formats a summary, sends via
Twilio (WhatsApp with SMS fallback).

## Observability

`uvicorn` runs alongside the scheduler on port 5050. Bearer-token auth.

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Unauthenticated liveness check |
| `GET /status` | HTML dashboard for today |
| `GET /status/json` | Today's state as JSON |
| `GET /history?days=7` | Last N days' state |

```bash
curl -H "Authorization: Bearer $DASHBOARD_TOKEN" http://localhost:5050/status/json
```

## Useful commands

```bash
make morning            # one-off morning run
make evening            # one-off evening run
make test-jira          # smoke-test Jira credentials (read-only)
make view-state         # inspect today's state
python scripts/view_state.py --history --days 14
```

## Notes on the architecture choice

The original v4 plan describes the four "MCP servers" as stdio subprocesses
the agent connects to over JSON-RPC. In practice this is a single-user
automation with no external MCP clients, so the runtime instead exposes each
server as an in-process Python class and registers their methods as tools
in `agent/client.py`. The tool surface (and hence the prompt contract) is
identical; only the transport differs. The class-level `Server` files are
preserved so they can be re-exposed via `FastMCP` in future if needed.

See [_legacy/README.md](_legacy/README.md) for context on what was removed
and why.
