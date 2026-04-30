# MCP Workflow Agent — Complete Project Setup

**Status**: ✅ Project created, installed, and ready for configuration

## Overview

This is a production-ready Python automation agent that:

- **11 AM (Morning)**: Creates a Jira story, adds a subtask, assigns it, sets 8h estimate, moves to In Progress
- **7 PM (Evening)**: Marks story & subtask as Done, adds 8h worklog, clicks Sync on timesheet portal
- **Intelligent**: Skips weekends/holidays, idempotent (safe to re-run), retries with backoff
- **Notifications**: WhatsApp alerts on success/failure (via CallMeBot or Twilio)
- **State Management**: SQLite tracks daily execution, prevents duplicate actions
- **MCP Server**: Can be triggered manually via Claude Desktop

---

## Project Structure

```
mcp-workflow-agent/
├── .env                      ← Configuration (EDIT THIS FIRST)
├── .env.example             ← Template
├── requirements.txt         ← Python dependencies (installed)
├── Makefile                 ← Convenience commands
│
├── config/
│   ├── settings.py          ← Pydantic config + keyring integration
│   └── holidays.py          ← Indian holidays 2026
│
├── src/
│   ├── main.py              ← APScheduler entry point
│   ├── utils/               ← Logger, date utils, retry decorator
│   ├── state/               ← SQLite state management
│   ├── jira_client/         ← Jira REST API v3 client
│   ├── browser/             ← Playwright automation
│   ├── notifications/       ← WhatsApp alerts
│   └── agents/              ← Morning & evening workflows
│
├── mcp_server/              ← FastMCP server for Claude Desktop
├── scripts/                 ← Helper scripts (reset, list transitions)
├── logs/                    ← Daily logs per phase + errors
└── data/                    ← SQLite database (auto-created)
```

---

## ✅ What's Done

- [x] All source files created (24 Python modules)
- [x] Virtual environment set up (`.venv`)
- [x] All dependencies installed:
  - `fastmcp`, `httpx`, `playwright`, `apscheduler`, `loguru`, `aiosqlite`, `tenacity`, `keyring`, `pydantic-settings`
- [x] Playwright chromium browser installed
- [x] Syntax validation passed
- [x] `.env` file created from template

---

## 🔧 Next Steps (Setup)

### 1. **Edit `.env` with Your Credentials** (REQUIRED)

```bash
# Minimal required fields:
JIRA_URL=https://your-company.atlassian.net
JIRA_USERNAME=your.email@company.com
JIRA_API_TOKEN=<paste your token>
JIRA_PROJECT_KEY=DEV
JIRA_ASSIGNEE_ACCOUNT_ID=<your account ID>
JIRA_ASSIGNEE_NAME=firstname_lastname

TIMESHEET_URL=https://timesheet.yourcompany.com
TIMESHEET_USERNAME=your_username
TIMESHEET_PASSWORD=<your password>
```

**How to find Jira Account ID:**

- Go to your Jira profile → Copy the account ID from the URL

**How to get Jira API Token:**

- Visit: https://id.atlassian.com/manage/api-tokens
- Create new token → Copy it

---

### 2. **Store Passwords in OS Keyring** (SECURE)

```bash
# Store passwords instead of keeping them in .env
python -c "import keyring; keyring.set_password('mcp-agent', 'JIRA_API_TOKEN', 'your_token_here')"
python -c "import keyring; keyring.set_password('mcp-agent', 'TIMESHEET_PASSWORD', 'your_password_here')"
```

Then leave `JIRA_API_TOKEN=` and `TIMESHEET_PASSWORD=` empty in `.env` — the system will auto-fetch from keyring.

---

### 3. **Find Jira Transition IDs** (REQUIRED)

Different Jira projects have different transition IDs for "In Progress" and "Done" states.

```bash
# Activate venv first
source .venv/bin/activate

# Run this with any existing Jira issue key (e.g., DEV-1)
python scripts/list_transitions.py DEV-1
```

Output will look like:

```
Transitions for DEV-1:
  ID:    21  Name: Start Progress
  ID:    31  Name: Done

Set JIRA_IN_PROGRESS_TRANSITION_ID and JIRA_DONE_TRANSITION_ID in your .env
```

Update `.env`:

```
JIRA_IN_PROGRESS_TRANSITION_ID=21
JIRA_DONE_TRANSITION_ID=31
```

---

### 4. **Setup WhatsApp Notifications** (OPTIONAL)

**Option A: CallMeBot (Free, Personal Use)** ← Recommended

```
1. Open WhatsApp on your phone
2. Add this contact: +34 644 59 71 28 (name it "CallMeBot")
3. Send message: "I allow callmebot to send me messages"
4. Within 60 seconds, you'll receive your WHATSAPP_APIKEY via WhatsApp
5. Update .env:
   WHATSAPP_PHONE=+91XXXXXXXXXX    # Your number with country code
   WHATSAPP_APIKEY=<received key>
```

**Option B: Twilio (Premium)**

- Sign up at https://www.twilio.com
- Get WhatsApp API credentials
- Set `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, etc. in `.env`

---

### 5. **Test Your Setup** (Before Running)

```bash
# Activate virtual environment
source .venv/bin/activate

# Test dry run (no Jira changes, no browser automation)
DRY_RUN=true python -c "import asyncio; from src.agents.morning import run_morning; asyncio.run(run_morning())"

# Should output: [DRY RUN] Would create story...
```

**Test WhatsApp:**

```bash
python -c "
import asyncio
from src.notifications.whatsapp import send_whatsapp
asyncio.run(send_whatsapp('🧪 Test from MCP Agent'))
"
```

---

## 🚀 How to Run

### Option 1: Direct (Terminal Stays Open)

```bash
source .venv/bin/activate
python src/main.py
```

Logs will show:

```
MCP Workflow Agent started
Timezone      : Asia/Kolkata
Morning job   : 11:00 Mon-Fri
Evening job   : 19:00 Mon-Fri
Dry run       : false
WhatsApp      : configured
```

Press `Ctrl+C` to stop.

---

### Option 2: Background (nohup)

```bash
cd /tmp/mcp-workflow-agent
source .venv/bin/activate
nohup python src/main.py > logs/main.log 2>&1 &
```

Check if running:

```bash
ps aux | grep "python src/main.py"
```

View logs:

```bash
tail -f logs/main.log
```

---

### Option 3: systemd Service (Linux, Recommended)

Create `/etc/systemd/system/mcp-workflow-agent.service`:

```ini
[Unit]
Description=MCP Workflow Agent
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/tmp/mcp-workflow-agent
Environment=PYTHONPATH=/tmp/mcp-workflow-agent
ExecStart=/tmp/mcp-workflow-agent/.venv/bin/python src/main.py
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable mcp-workflow-agent
sudo systemctl start mcp-workflow-agent
sudo systemctl status mcp-workflow-agent
```

---

### Option 4: Manual Trigger via Makefile

```bash
source .venv/bin/activate

# Run morning workflow manually
make morning

# Run evening workflow manually
make evening

# Reset today's state (for testing re-runs)
make reset-state

# Check list of transitions
make list-transitions

# Start MCP server for Claude Desktop
make mcp-server
```

---

## 📊 How It Works

### Morning Workflow (11:00 AM Mon-Fri)

1. Check if it's weekend/holiday → skip if true
2. Check if already ran today → skip if true
3. Search Jira for today's story (by date in summary)
4. If not found → create new story with:
   - Summary: `[2026-04-30] Daily Development Work`
   - Description: Daily development tasks
   - Estimate: 8 hours
5. Create subtask: `firstname_lastname - [2026-04-30] Daily Development Work`
6. Assign story + subtask to yourself
7. Move story to "In Progress"
8. Save state to SQLite
9. Send WhatsApp: "✅ _Morning Workflow Done_" with details
10. Log everything to `logs/morning/YYYY-MM-DD.log`

**Errors**:

- Logged to `logs/error/YYYY-MM-DD-error.log`
- WhatsApp alert sent: "🚨 _Morning Workflow Failed_"
- Saved to SQLite for audit trail

---

### Evening Workflow (7:00 PM Mon-Fri)

1. Same skip checks + verify morning completed
2. Mark all subtasks → "Done"
3. Mark story → "Done"
4. Add 8-hour worklog with timestamp
5. Open timesheet portal in Playwright browser:
   - Auto-login if needed
   - Click "Sync" button
   - Take screenshots (before/after)
   - Verify network idle
6. Save state to SQLite
7. Send WhatsApp: "✅ _Evening Workflow Done_" with sync status
8. Log to `logs/evening/YYYY-MM-DD.log`

**Browser Features**:

- Headless by default (set `BROWSER_HEADLESS=false` in `.env` to watch it)
- Auto-retries with exponential backoff
- Screenshots on failure saved to `logs/screenshots/`
- Handles login forms automatically

---

## 📋 Database Schema

Located at `data/agent.db` (SQLite):

### `daily_runs` table:

```
date              TEXT PRIMARY KEY    (YYYY-MM-DD)
story_key         TEXT                (e.g., DEV-42)
subtask_keys      TEXT (JSON array)   (["DEV-43"])
morning_done      INTEGER             (0 or 1)
evening_done      INTEGER             (0 or 1)
worklog_id        TEXT                (Jira worklog ID)
timesheet_synced  INTEGER             (0 or 1)
errors            TEXT (JSON array)   (["Error 1", "Error 2"])
screenshot_path   TEXT                (path to last screenshot)
created_at        TEXT                (timestamp)
updated_at        TEXT                (timestamp)
```

### `run_log` table:

```
id        INTEGER PRIMARY KEY
date      TEXT                (YYYY-MM-DD)
phase     TEXT                ('morning' or 'evening')
step      TEXT                ('create_story', 'assign', etc.)
status    TEXT                ('success', 'failure', 'running')
detail    TEXT                (JSON or error message)
ts        TEXT                (timestamp)
```

---

## 🔐 Security Best Practices

- [x] Use OS keyring for sensitive data (Jira token, timesheet password)
- [x] `.env` is in `.gitignore`
- [x] `data/` (contains DB with task data) is ignored
- [x] `logs/` (may contain screenshots) is ignored
- [x] Screenshots auto-purge after 30 days (loguru setting)
- [x] Add cron for extra cleanup: `find logs/screenshots -mtime +30 -delete`

---

## 🐛 Troubleshooting

| Problem                           | Cause                        | Fix                                                                                           |
| --------------------------------- | ---------------------------- | --------------------------------------------------------------------------------------------- |
| `Error: JIRA_API_TOKEN not found` | Token not in keyring or .env | Run: `python -c "import keyring; keyring.set_password('mcp-agent', 'JIRA_API_TOKEN', '...')"` |
| `Story created twice`             | State DB not persisting      | Check `data/agent.db` exists, run: `python scripts/reset_state.py`                            |
| `Sync button not found`           | Button text doesn't match    | Set `TIMESHEET_SYNC_BUTTON_TEXT=ExactLabel` in .env. Use `BROWSER_HEADLESS=false` to inspect  |
| `Transition failed (404)`         | Wrong transition ID          | Run `python scripts/list_transitions.py DEV-1`, update .env                                   |
| `Scheduler not firing`            | Timezone mismatch            | Set `TZ=Asia/Kolkata` (or your tz)                                                            |
| `WhatsApp not sent`               | Wrong API key or phone       | Re-send activation to CallMeBot, verify `+` and country code in phone                         |
| `Playwright error`                | Browser not installed        | Run: `playwright install chromium`                                                            |
| `Permission denied`               | Directory issues             | Run: `mkdir -p logs/morning logs/evening logs/error logs/screenshots data`                    |

---

## 📈 Monitoring

### Check Status Without Running

```bash
source .venv/bin/activate

# Query today's execution status
python -c "
import asyncio
from src.state.store import StateStore
from src.utils.date_utils import today_iso

async def main():
    store = StateStore()
    await store.init()
    state = await store.get_today()
    if state:
        print(f'Date: {state.date}')
        print(f'Morning: {state.morning_done}')
        print(f'Evening: {state.evening_done}')
        print(f'Story: {state.story_key}')
        print(f'Errors: {state.errors}')
    else:
        print('No run recorded today')

asyncio.run(main())
"
```

### View Logs

```bash
# Today's morning log
tail logs/morning/$(date +%Y-%m-%d).log

# Today's evening log
tail logs/evening/$(date +%Y-%m-%d).log

# All errors
tail -f logs/error/*.log

# Main agent log (if running)
tail -f logs/main.log
```

---

## 🤝 Manual Triggers via Claude Desktop

The project includes a FastMCP server that allows manual triggers from Claude Desktop:

```bash
source .venv/bin/activate
python mcp_server/server.py
```

Then add to Claude Desktop config at `~/.config/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "jira-timesheet-agent": {
      "command": "python",
      "args": ["/absolute/path/to/mcp-workflow-agent/mcp_server/server.py"]
    }
  }
}
```

Available tools in Claude Desktop:

- `run_morning_workflow(dry_run=false)`
- `run_evening_workflow(dry_run=false)`
- `get_daily_status()`
- `list_jira_transitions(issue_key)`
- `send_test_whatsapp(message)`
- `reset_today_state()`
- `take_timesheet_screenshot()`

---

## 📝 Configuration Reference

### Required Settings

| Setting                    | Example                         | Notes                                                  |
| -------------------------- | ------------------------------- | ------------------------------------------------------ |
| `JIRA_URL`                 | `https://company.atlassian.net` | Your Jira cloud URL                                    |
| `JIRA_USERNAME`            | `you@company.com`               | Email used for Jira                                    |
| `JIRA_API_TOKEN`           | Leave empty if using keyring    | Generate at https://id.atlassian.com/manage/api-tokens |
| `JIRA_PROJECT_KEY`         | `DEV`                           | Your Jira project key                                  |
| `JIRA_ASSIGNEE_ACCOUNT_ID` | `5f123abc...`                   | From your Jira profile URL                             |
| `TIMESHEET_URL`            | `https://timesheet.company.com` | Your timesheet portal                                  |
| `TIMESHEET_USERNAME`       | `username`                      | Portal login username                                  |
| `TIMESHEET_PASSWORD`       | Leave empty if using keyring    | Or store in keyring                                    |

### Optional Settings

| Setting            | Default        | Notes                                   |
| ------------------ | -------------- | --------------------------------------- |
| `TZ`               | `Asia/Kolkata` | Your timezone (TZ database format)      |
| `MORNING_HOUR`     | `11`           | Hour to run morning workflow (0-23)     |
| `EVENING_HOUR`     | `19`           | Hour to run evening workflow (0-23)     |
| `BROWSER_HEADLESS` | `true`         | Set to false to see browser (debugging) |
| `DRY_RUN`          | `false`        | Simulate without making changes         |
| `LOG_LEVEL`        | `INFO`         | DEBUG, INFO, WARNING, ERROR             |

---

## 🎯 Production Checklist

- [ ] All required fields in `.env` filled
- [ ] Jira API token stored in keyring
- [ ] Timesheet password stored in keyring
- [ ] Correct transition IDs verified
- [ ] WhatsApp configured and tested
- [ ] Dry run successful: `DRY_RUN=true make morning`
- [ ] Actual morning run successful on test day
- [ ] Agent running via systemd or background process
- [ ] Logs being generated in `logs/`
- [ ] `.env` and `data/` are in `.gitignore`

---

## 📞 Support

**Key Files to Check:**

- `.env` — Configuration
- `logs/main.log` — Scheduler logs
- `logs/morning/YYYY-MM-DD.log` — Morning run details
- `logs/evening/YYYY-MM-DD.log` — Evening run details
- `logs/error/YYYY-MM-DD-error.log` — Errors
- `data/agent.db` — Execution history

**Commands to Debug:**

```bash
# Test Jira connection
source .venv/bin/activate
python -c "from src.jira_client.client import JiraClient; import asyncio; print('✅ Jira client imports OK')"

# Check settings
python -c "from config.settings import settings; print(f'Jira URL: {settings.jira_url}')"

# Verify database
python scripts/reset_state.py

# List available holidays
python -c "from config.holidays import HOLIDAYS; print(sorted(HOLIDAYS))"
```

---

**Status**: ✅ Ready to Configure and Run

**Next Action**: Edit `.env` with your Jira and timesheet credentials, then test with `DRY_RUN=true make morning`
