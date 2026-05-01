# 🚀 Getting Started — Where to Look First

This guide helps you quickly understand the Part 2 implementation and get up and running.

---

## 📖 Documentation (Read These First)

### **1. PART2_SUMMARY.md** (This is your overview)

- ✅ What was built
- ✅ 24 tools across 4 MCP servers
- ✅ Architecture highlights
- ✅ Quick start commands
- ✅ Testing checklist

**Read this first:** 5 minutes. Understand what exists.

### **2. IMPLEMENTATION_PART2.md** (Complete reference)

- ✅ Detailed file-by-file breakdown
- ✅ Data flow diagrams for morning/evening/notification
- ✅ Database schema
- ✅ Deployment options
- ✅ Testing instructions

**Read this:** 15 minutes. Get technical details.

### **3. README.md** (Updated in Part 2)

- ✅ High-level project overview
- ✅ Quick start
- ✅ Architecture diagram
- ✅ Contributing guidelines

**Skim this:** 5 minutes. Context.

---

## 🎯 Key Files to Understand

### Architecture & Startup

**Entry Point:** `scheduler/main_scheduler.py`

- Where APScheduler starts
- 4 jobs configured (morning, evening, notification, monthly)
- IST timezone setup
- Runs observability server in parallel

**MCP Client:** `agent/client.py`

- How Claude talks to MCP servers
- Tool list builder (24 tools)
- Agentic loop with 30-iteration limit
- Server subprocess management

### Agent Logic

**Morning:** `agent/morning_agent.py`

- Calls AgentOrchestrator with MORNING_SYSTEM_PROMPT
- Returns status + duration

**Evening:** `agent/evening_agent.py`

- Calls AgentOrchestrator with EVENING_SYSTEM_PROMPT
- Handles Jira + Timesheet integration

**Prompts:** `agent/prompts.py`

- MORNING_SYSTEM_PROMPT: 15 numbered steps
- EVENING_SYSTEM_PROMPT: 13 numbered steps
- Critical: Worklog timestamp MUST be `{time}+0530` (IST)

### MCP Servers (The Real Work)

**Jira:** `mcp_servers/jira_mcp/server.py`

- `create_subtask()` — Most critical tool
- `transition_issue()` — Change status to Done
- `add_worklog()` — 8h @ 11 AM IST (CRITICAL TIME FORMAT)
- 10 tools total

**Browser:** `mcp_servers/browser_mcp/server.py`

- Playwright automation for timesheet portal
- Multi-selector fallback strategy
- Screenshot on failure
- 5 tools total

**State:** `mcp_servers/state_mcp/server.py`

- SQLite persistence
- Working day counter (skips weekends/holidays)
- 6 tools total

**Notification:** `mcp_servers/notification_mcp/server.py`

- Twilio WhatsApp + SMS
- 3 tools (WhatsApp, SMS, Alert)

### Scheduler Logic

**Jobs:** `scheduler/jobs.py`

- `morning_job()` — Guard check + MorningAgent
- `evening_job()` — Guard check + EveningAgent
- `notification_job()` — Pure Python (no Claude), deterministic message builder
- `monthly_reminder_job()` — Credential rotation reminder

**Guards:** `scheduler/guards.py`

- `is_weekend()` — Sat/Sun check
- `is_national_holiday()` — India holidays
- `is_company_holiday()` — Custom dict
- `should_run_morning()` — Full pre-flight checks
- `should_run_evening()` — Pre-flight checks
- `check_catch_up()` — Yesterday's evening failed?

### Observability

**Dashboard:** `observability/status_server.py`

- FastAPI server on port 5050
- `GET /status` — HTML dashboard
- `GET /status/json` — JSON API
- `GET /history?days=7` — History
- Bearer token auth

---

## 🧪 Testing & Setup

**Setup Wizard:** `scripts/setup.py`

- Validates all 18 environment variables
- Tests Jira connectivity
- Tests Twilio
- Initializes database
- Creates directories

```bash
python scripts/setup.py
```

**Manual Triggers:**

```bash
python scripts/run_morning.py   # Test morning job now
python scripts/run_evening.py   # Test evening job now
```

**View State:**

```bash
python scripts/view_state.py            # Today's state
python scripts/view_state.py --history  # Last 7 days
```

**Test Jira:**

```bash
python scripts/test_jira.py  # Validate Jira connectivity
```

---

## 🏗 System Architecture (90-Second Overview)

```
┌─────────────────────────────────────────────────────┐
│  APScheduler (IST Timezone)                         │
├─────────────────────────────────────────────────────┤
│ • 11:00 AM → morning_job()                          │
│ • 7:00 PM  → evening_job()                          │
│ • 7:30 PM  → notification_job() [Pure Python]       │
│ • 1st @ 9 AM → monthly_reminder_job()               │
└──────────────┬──────────────────────────────────────┘
               │
               ├─→ Guard Checks (weekend/holiday/leave)
               │
               └─→ Agent Orchestrator (Claude + MCP)
                   │
                   ├─→ Jira MCP (10 tools)
                   │   • create_subtask()
                   │   • transition_issue()
                   │   • add_worklog() [+0530 IST]
                   │   • [7 more tools]
                   │
                   ├─→ Browser MCP (5 tools)
                   │   • login_timesheet()
                   │   • sync_jira_logs()
                   │   • confirm_hours()
                   │   • [2 more tools]
                   │
                   ├─→ State MCP (6 tools)
                   │   • get_today_state()
                   │   • set_today_state()
                   │   • get_day_number()
                   │   • [3 more tools]
                   │
                   └─→ Notification MCP (3 tools)
                       • send_whatsapp()
                       • send_sms()
                       • send_alert()

                   ↓ (Database)

               SQLite (data/automation_state.db)
               • daily_runs table (16 columns)
               • config table (settings)

                   ↓ (Observability)

               FastAPI Server (Port 5050)
               • /status (HTML dashboard)
               • /status/json (API)
               • /history?days=7 (History)
```

---

## 🚀 Quick Start (60 Seconds)

### 1. Install

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

```bash
# Copy .env.example → .env
# Fill in all 18 required environment variables
```

### 3. Setup

```bash
python scripts/setup.py
# Validates everything, initializes database
```

### 4. Test

```bash
python scripts/run_morning.py
# See it create a subtask in Jira
```

### 5. Deploy

```bash
python -m scheduler.main_scheduler
# Runs forever, waits for scheduled times
```

### 6. Monitor

```bash
open http://localhost:5050/status
# View dashboard (password: DASHBOARD_TOKEN from .env)
```

---

## 🧩 How Things Connect

### Morning Workflow

```
11:00 AM
   ↓
Guard: weekend? → NO
Guard: holiday? → NO
Guard: leave? → NO
Guard: already_done? → NO
   ↓
Claude receives MORNING_SYSTEM_PROMPT
   ↓
Calls (in order):
  1. state::get_today_state() [check idempotency]
  2. state::get_day_number() [calculate day 1, 2, 3...]
  3. jira::get_my_account_id()
  4. jira::get_parent_story()
  5. jira::check_subtask_exists() [idempotency]
  6. jira::create_subtask() [MAIN WORK]
  7. jira::add_label()
  8. jira::set_time_estimate(28800 seconds = 8h)
  9. jira::assign_issue()
  10. jira::get_issue_transitions()
  11. jira::transition_issue() [→ "In Progress"]
  12. state::set_today_state(morning_done=1)
  13. notification::send_whatsapp() [confirmation]
   ↓
Complete (~15 seconds)
Record day_number, subtask_key, morning_duration_sec in DB
```

### Evening Workflow

```
7:00 PM
   ↓
Guard: weekend? → NO
Guard: holiday? → NO
Guard: leave? → NO
Guard: already_done? → NO
Guard: morning_done? → YES (required)
   ↓
Claude receives EVENING_SYSTEM_PROMPT
   ↓
Calls (in order):
  1. jira::get_issue_transitions()
  2. jira::transition_issue() [→ "Done"]
  3. jira::add_worklog(start="11:00:00+0530", 8h) [CRITICAL TIME]
  4. state::set_today_state(evening_done=1)
  5. browser::login_timesheet()
  6. browser::sync_jira_logs()
  7. browser::confirm_hours() [verify 8h appears]
  8. state::set_today_state(timesheet_done=1)
   ↓
Complete (~60 seconds, browser is slow)
Record evening_duration_sec, timesheet_done in DB
```

### Notification (7:30 PM)

```
7:30 PM
   ↓
Pure Python (NO Claude, NO MCP)
   ↓
Read state DB for today
   ↓
Format message based on 3 flags:
  • morning_done? (Y/N)
  • evening_done? (Y/N)
  • timesheet_done? (Y/N)
   → 8 possible message states

   ↓
Send via Twilio (WhatsApp → SMS fallback)
   ↓
Record notification_done=1, message_sid in DB
   ↓
Complete (<2 seconds)
```

---

## 🔍 Debug Commands

```bash
# 1. Check if setup is valid
python scripts/setup.py

# 2. See today's state
python scripts/view_state.py

# 3. See last 7 days
python scripts/view_state.py --history 7

# 4. Test Jira only
python scripts/test_jira.py

# 5. Run morning manually
python scripts/run_morning.py

# 6. Run evening manually
python scripts/run_evening.py

# 7. View latest logs
tail -f logs/automation.log

# 8. Open dashboard
open http://localhost:5050/status
# Password: DASHBOARD_TOKEN from .env

# 9. Check Jira subtask
# Open JIRA_BASE_URL → search "day_1" or "day_2" etc
```

---

## 🎯 What Each MCP Server Does (90 Seconds Each)

### Jira MCP

- Uses REST API v3 with Basic Auth (email:token)
- Creates subtasks with exact name format: `{prefix} - day_{N} - {story}`
- Transitions issues through workflow (In Progress → Done)
- Adds 8h worklogs with IST timestamp (CRITICAL: +0530)
- 10 tools that Claude calls sequentially

### Browser MCP

- Launches Playwright Chromium (headless)
- Logs into timesheet portal (username/password)
- Clicks "sync with Jira" button
- Verifies 8h appears in timesheet
- Takes screenshots on failure
- 5 tools for portal automation

### State MCP

- SQLite database at data/automation_state.db
- Tracks: morning_done, evening_done, timesheet_done flags
- Calculates working day number (skips weekends/holidays)
- Stores config values (start_date, parent_key, etc)
- 6 tools for persistence

### Notification MCP

- Posts directly to Twilio API
- Tries WhatsApp first, SMS fallback
- Returns message SID on success
- 3 tools for messaging

---

## 🔐 Environment Variables (18 Total)

| Category  | Variables                                                                    | Purpose                |
| --------- | ---------------------------------------------------------------------------- | ---------------------- |
| Jira      | JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN, JIRA_PARENT_KEY, JIRA_PROJECT_KEY | API connectivity       |
| Jira User | MY_JIRA_LABEL, MY_USERNAME_PREFIX                                            | Formatting & filtering |
| Timesheet | TIMESHEET_URL, TIMESHEET_USERNAME, TIMESHEET_PASSWORD                        | Portal automation      |
| Twilio    | TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, TWILIO_TO_NUMBER  | Notifications          |
| AI        | ANTHROPIC_API_KEY                                                            | Claude integration     |
| App       | INTERN_START_DATE, DASHBOARD_TOKEN                                           | Config & observability |

---

## ✅ Pre-Launch Checklist

- [ ] All 18 env vars set in `.env`
- [ ] `python scripts/setup.py` runs to completion (all green ✅)
- [ ] Jira subtask created successfully (during setup)
- [ ] Twilio test message received on phone
- [ ] Database created: `data/automation_state.db` exists
- [ ] Manual `python scripts/run_morning.py` works
- [ ] Subtask has correct name format
- [ ] Subtask has 8h estimate
- [ ] Subtask status is "In Progress"
- [ ] Subtask has your label applied
- [ ] WhatsApp notification arrived
- [ ] Dashboard accessible at `http://localhost:5050/status`

---

## 🚀 Deploy Commands

### Local (Development)

```bash
python -m scheduler.main_scheduler
```

### Docker (Any Machine)

```bash
docker compose up -d
docker compose logs -f automation
```

### Azure Student VM (Production)

```bash
# SSH into VM
ssh -i key.pem azureuser@<ip>

# Clone repo, copy .env
git clone https://github.com/yourname/repo.git
cd repo
scp .env azureuser@<ip>:~/repo/

# Run
docker compose up -d
```

---

## 📞 If Something Goes Wrong

### Jira subtask not created

→ Check: JIRA_PARENT_KEY exists, MY_USERNAME_PREFIX doesn't have special chars, user has project permissions
→ Debug: `python scripts/test_jira.py`

### Timesheet sync fails

→ Check: TIMESHEET_URL, username, password are correct; portal structure hasn't changed
→ Debug: Add screenshots to logs/ (already done)

### Twilio WhatsApp not arriving

→ Check: TWILIO_TO_NUMBER includes country code (+91)
→ Fallback: SMS will automatically send instead

### Worklog has wrong time

→ Check: Worklog timestamp MUST be `{time}+0530` not UTC
→ Location: `agent/prompts.py` EVENING_SYSTEM_PROMPT line ~10
→ Critical: IST offset is hardcoded as +0530 (not +0530 from system time)

### Already ran today but flag not set

→ Debug: `python scripts/view_state.py` to see state DB
→ Fix: Database corruption is unlikely, check logs

---

## 📊 Monitoring (What to Check Daily)

1. **Dashboard:** http://localhost:5050/status
   - Green = everything done
   - Orange = partial completion
   - Red = errors

2. **Logs:** `tail -f logs/automation.log`
   - Should show tool calls for each run
   - Look for errors in evening runs (browser is flaky)

3. **State:** `python scripts/view_state.py`
   - Verify day_number incrementing
   - Check subtask_key is different each day
   - No error_log entries

4. **Jira:**
   - Verify subtask created daily
   - Verify worklog shows 8h @ 11 AM IST (not UTC!)
   - Verify status transition: In Progress → Done

5. **Timesheet:**
   - Verify sync button clicked
   - Verify 8h appears in timesheet
   - Verify marked as complete for the day

---

## 🎓 Learning Path

If you're new to this codebase:

1. **First:** Read PART2_SUMMARY.md (5 min) — Understand what exists
2. **Second:** Read this file (10 min) — Learn where things are
3. **Third:** Run `python scripts/setup.py` (2 min) — Validate environment
4. **Fourth:** Run `python scripts/run_morning.py` (15 sec) — See it in action
5. **Fifth:** Open `http://localhost:5050/status` — View dashboard
6. **Sixth:** Read IMPLEMENTATION_PART2.md (15 min) — Deep dive
7. **Seventh:** Read `agent/prompts.py` (5 min) — Understand Claude's instructions
8. **Eighth:** Read `scheduler/main_scheduler.py` (10 min) — Understand scheduling
9. **Ninth:** Deploy: `python -m scheduler.main_scheduler` (forever) — Run it
10. **Tenth:** Monitor for 1 week — Catch any env-specific issues

---

## ✨ Summary

**You now have:**

- ✅ 24 tools across 4 MCP servers
- ✅ Fully functional Claude agents (morning + evening)
- ✅ APScheduler running 3 main jobs + 1 monthly job
- ✅ SQLite persistence with state tracking
- ✅ FastAPI observability dashboard
- ✅ Production-ready error handling
- ✅ Comprehensive setup wizard

**Next step:** `python scripts/setup.py` → Deploy → Monitor

---

**Good luck! Your automation is ready. 🚀**
