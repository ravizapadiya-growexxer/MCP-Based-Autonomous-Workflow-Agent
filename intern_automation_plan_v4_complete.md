# 🤖 Intern Daily Automation — Complete MCP Architecture Plan
> **Production-Grade · Python Stack · Autonomous Agentic AI · Senior Architect Design**
> Version 4.0 — v3 Refined + All Missing Deep Technical Content Restored
>
> What v3.0 refined:
> - ✅ Azure Student Account deployment (replaces Oracle/generic VPS)
> - ✅ Twilio (WhatsApp + SMS) replaces Telegram — with full justification
> - ✅ Deep explanation of why the 7:30 PM notification job deliberately skips Claude
> - ✅ Complete Observability Layer — how to know task status without waiting for any notification
>
> What v4.0 adds (restored from Complete Plan — not covered in v3):
> - ✅ Architecture Philosophy — Why MCP over plain scripts / LangChain
> - ✅ Agent Decision Model — full Read-Decide-Act flowchart
> - ✅ Detailed Data Flow diagrams for Morning, Evening, and Notification jobs
> - ✅ Why Jira API vs Browser + Why Browser for Timesheet — rationale tables
> - ✅ Complete requirements.txt dependency list
> - ✅ MCP Architecture Overview with JSON-RPC diagram
> - ✅ Deep per-tool inventory for Jira MCP and Browser MCP (not just tables)
> - ✅ MCP Client — how the orchestrator spawns and connects to all servers
> - ✅ Scheduler Configuration — cron, coalesce, misfire grace settings
> - ✅ Key File Responsibilities table
> - ✅ Threat Model, .gitignore, Token Best Practices, Human Approval Mode (Twilio), Credential Rotation
> - ✅ Local Laptop + Docker on Laptop + Windows Task Scheduler deployment options
> - ✅ Deployment Comparison Matrix (all options)
> - ✅ Error Handling Architecture flowchart
> - ✅ Catch-Up Logic, Weekend/Holiday Skip Logic, Failure Recovery Playbook
> - ✅ Recommended Build Order (Day-by-Day Summary)
> - ✅ Final Recommendation paragraph

---

## 📋 Table of Contents

| # | Section |
|---|---------|
| 1 | [Final Architecture — Updated](#1-final-architecture--updated) |
| 2 | [Recommended Tech Stack — Updated](#2-recommended-tech-stack--updated) |
| 3 | [MCP Components — Full Design](#3-mcp-components--full-design) |
| 4 | [Daily Workflow — Exact Execution Flow](#4-daily-workflow--exact-execution-flow) |
| 5 | [The Intelligence Boundary — Why 7:30 PM Skips Claude](#5-the-intelligence-boundary--why-730-pm-skips-claude) |
| 6 | [Observability Layer — Know Status Without Notifications](#6-observability-layer--know-status-without-notifications) |
| 7 | [Codebase Structure — Updated](#7-codebase-structure--updated) |
| 8 | [Security Design](#8-security-design) |
| 9 | [Azure Student Deployment — Complete Guide](#9-azure-student-deployment--complete-guide) |
| 10 | [Risks & Edge Cases](#10-risks--edge-cases) |
| 11 | [Phase-wise Build Roadmap — Detailed, No Code](#11-phase-wise-build-roadmap--detailed-no-code) |
| 12 | [Final Verdict](#12-final-verdict) |
| 13 | [Alternative Deployment Options — Laptop & Windows](#13-alternative-deployment-options--laptop--windows) |

---

## 1. Final Architecture — Updated

### 1.1 Philosophy — Why MCP Over Simple Scripts?

Before the architecture, understand the design choice. You could build this with:

- **Option A — Plain Python script:** Hardcoded API calls, cron job, no agent reasoning. Fast to build, brittle to change.
- **Option B — LangChain/LangGraph:** Heavy framework, over-engineered for solo personal use.
- **Option C — MCP-based Agentic System (chosen):** Claude reasons about *what to do next*, each capability is an isolated MCP server (testable independently), the agent handles errors, retries, and unexpected Jira states without rewriting logic.

The key advantage of MCP here: if your Jira changes a field name, or the timesheet portal redesigns its UI, you only touch one isolated server file — not a sprawling script. The agent's reasoning adapts automatically.

---

### 1.2 System Architecture with All Refinements Applied

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                     AZURE STUDENT VM B1s (Free 12 months)                        ║
║                        Ubuntu 22.04 · Docker Compose                             ║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐ ║
║  │                    SCHEDULER LAYER  (APScheduler · IST)                      │ ║
║  │    11:00 AM → Morning Job    7:00 PM → Evening Job    7:30 PM → Notify Job   │ ║
║  └────────────────────────────────┬────────────────────────────────────────────┘ ║
║                                   │ triggers (with guards)                       ║
║  ┌────────────────────────────────▼────────────────────────────────────────────┐ ║
║  │               GUARD / PRE-FLIGHT LAYER (Pure Python — No LLM)               │ ║
║  │   Weekend? → Holiday? → Company Leave? → Already Done? → PROCEED / SKIP     │ ║
║  └────────────────────────────────┬────────────────────────────────────────────┘ ║
║                                   │                                              ║
║          ┌────────────────────────┼──────────────────────────┐                  ║
║          │ Morning/Evening Jobs   │                          │ Notification Job  ║
║          │ (LLM-powered)          │                          │ (Pure Python)     ║
║          ▼                        │                          ▼                   ║
║  ┌──────────────────┐             │              ┌─────────────────────────┐     ║
║  │  Claude Sonnet 4 │             │              │  Notification Engine    │     ║
║  │  Agent (Agentic) │             │              │  (Reads state DB →      │     ║
║  │  Tool-Use Mode   │             │              │   Formats message →     │     ║
║  └──────┬───────────┘             │              │   Calls Twilio API)     │     ║
║         │ MCP Protocol            │              └─────────────┬───────────┘     ║
║         │ (JSON-RPC stdio)        │                            │                 ║
║  ┌──────▼──────┐  ┌──────────┐  ┌──────────┐                  │                 ║
║  │  JIRA MCP   │  │BROWSER   │  │ STATE    │                   │                 ║
║  │  Server     │  │  MCP     │  │  MCP     │                   │                 ║
║  │  (10 tools) │  │ (5 tools)│  │ (6 tools)│                   │                 ║
║  └──────┬──────┘  └────┬─────┘  └────┬─────┘                  │                 ║
║         │              │             │                         │                 ║
║         ▼              ▼             ▼                         ▼                 ║
║   Jira REST API  Playwright    SQLite DB              Twilio WhatsApp/SMS        ║
║   (Atlassian)    (Chromium)   (state.db)              (messages to your phone)   ║
║                  Timesheet                                                       ║
║                  Portal                                                          ║
║                                                                                  ║
║  ┌─────────────────────────────────────────────────────────────────────────────┐ ║
║  │                    OBSERVABILITY LAYER (Always Available)                    │ ║
║  │  Status HTTP Server (port 5050) · SQLite Viewer · Twilio /status command    │ ║
║  └─────────────────────────────────────────────────────────────────────────────┘ ║
╚══════════════════════════════════════════════════════════════════════════════════╝
```

### 1.3 Key Architectural Decisions in v3.0

| Decision | Choice | Reason |
|---|---|---|
| Cloud Platform | Azure Student VM B1s | Free 12 months, $100 credit, Docker-compatible, 24/7 uptime |
| Notification | Twilio (WhatsApp + SMS) | Works on any phone, no special app, more reliable delivery, programmable fallback |
| 7:30 PM Job | Pure Python (no Claude) | Deterministic output — explained fully in Section 5 |
| Observability | HTTP status server + SQLite viewer | Know status anytime, even if notifications fail |
| Notification MCP | Twilio MCP Server | Replaces Telegram MCP throughout |

---

### 1.4 Agent Decision Model — Read-Decide-Act Loop

Every time the scheduler fires, the agent runs this decision tree before doing anything:

```
SCHEDULER FIRES (11 AM / 7 PM / 7:30 PM)
           │
           ▼
┌─────────────────────────────────┐
│  GUARD 1: Is today Saturday     │──── YES ──→ Log "Weekend skip" → STOP
│           or Sunday?            │
└─────────────────────────────────┘
           │ NO
           ▼
┌─────────────────────────────────┐
│  GUARD 2: Is today a national   │──── YES ──→ Log holiday name → STOP
│  public holiday (India)?        │
└─────────────────────────────────┘
           │ NO
           ▼
┌─────────────────────────────────┐
│  GUARD 3: Is today a company-   │──── YES ──→ Log holiday name → STOP
│  specific holiday?              │
└─────────────────────────────────┘
           │ NO
           ▼
┌─────────────────────────────────┐
│  GUARD 4 (Morning): Is          │──── YES ──→ Log "Already done" → STOP
│  morning_done = 1 in state DB?  │           (IDEMPOTENCY PROTECTION)
└─────────────────────────────────┘
           │ NO
           ▼
┌─────────────────────────────────┐
│  CATCH-UP CHECK: Was yesterday  │──── YES ──→ Send Twilio alert
│  a workday with evening_done=0? │           about missed yesterday
└─────────────────────────────────┘
           │
           ▼
     EXECUTE WORKFLOW
           │
           ▼
┌─────────────────────────────────┐
│  After each tool call:          │
│  SUCCESS → Update state DB      │
│  FAILURE → Retry (max 3x)       │
│          → Still fail?          │
│          → Screenshot + Alert   │
└─────────────────────────────────┘
```

---

### 1.5 Data Flow — Morning Routine

```
SCHEDULER (11:00 AM IST)
     │
     ├─► STATE MCP: Read today's state
     │        └─► If morning_done=1, EXIT immediately
     │
     ├─► STATE MCP: Get day_number (count workdays since start_date)
     │
     ├─► JIRA MCP: get_my_account_id
     │        └─► Store accountId for this session
     │
     ├─► JIRA MCP: get_parent_story (by JIRA_PARENT_KEY from config)
     │        └─► Extract: summary, project_key, issue_key
     │
     ├─► JIRA MCP: check_subtask_exists (parent_key + "day_N" in name)
     │        └─► If exists: save key to state, mark morning_done=1, EXIT
     │
     ├─► Build subtask name:
     │        "firstname_surname - day_N - parent_story_title"
     │
     ├─► JIRA MCP: create_subtask
     │        └─► Returns: new issue key (e.g., PROJ-456)
     │
     ├─► JIRA MCP: add_label (my personal label)
     │
     ├─► JIRA MCP: set_time_estimate (28800 seconds = 8h)
     │
     ├─► JIRA MCP: assign_issue (to my accountId)
     │
     ├─► JIRA MCP: get_issue_transitions (for the subtask)
     │        └─► Find transition ID for "In Progress"
     │
     ├─► JIRA MCP: transition_issue (→ In Progress)
     │
     ├─► STATE MCP: set_today_state (subtask_key, morning_done=1, day_number)
     │
     └─► NOTIFY MCP: send_whatsapp("✅ Morning done: PROJ-456 created & In Progress")
```

---

### 1.6 Data Flow — Evening Routine

```
SCHEDULER (7:00 PM IST)
     │
     ├─► STATE MCP: Read today's state
     │        ├─► If evening_done=1, EXIT immediately
     │        └─► If morning_done=0, send alert "morning failed", EXIT
     │
     ├─► Get subtask_key from today's state DB
     │
     ├─► JIRA MCP: get_issue_transitions (for subtask)
     │        └─► Find transition ID for "Done"
     │
     ├─► JIRA MCP: transition_issue (→ Done)
     │
     ├─► JIRA MCP: add_worklog
     │        ├─► started: TODAY at 11:00:00.000+0530 (IST)
     │        └─► timeSpent: "8h"
     │
     ├─► STATE MCP: set_today_state (evening_done=1)
     │
     ├─► BROWSER MCP: login_timesheet
     │        └─► Headless Chromium → navigate → fill credentials → submit
     │
     ├─► BROWSER MCP: sync_jira_logs
     │        └─► Click "Sync from Jira" button → wait for load
     │
     ├─► BROWSER MCP: confirm_hours
     │        └─► Assert 8h appears on today's timesheet row
     │
     ├─► STATE MCP: set_today_state (timesheet_done=1)
     │
     └─► (Notification sent at 7:30 PM by separate job)
```

---

### 1.7 Data Flow — Notification Job (7:30 PM)

```
SCHEDULER (7:30 PM IST)
     │
     ├─► STATE MCP: Read today's state
     │
     ├─► Build summary message:
     │     ✅ Subtask created: PROJ-456        ← if morning_done=1
     │     ❌ Subtask creation FAILED          ← if morning_done=0
     │     ✅ Worklog submitted (8h @ 11 AM)   ← if evening_done=1
     │     ✅ Timesheet synced (8h confirmed)  ← if timesheet_done=1
     │     🎉 Today's routine completed!       ← if all done
     │     ⚠️  Some steps failed — check logs  ← if any failed
     │
     └─► NOTIFY (direct Python): send_whatsapp(formatted message)
```

---

## 2. Recommended Tech Stack — Updated

### 2.1 Full Technology Stack

| Layer | Tool | Version | Notes |
|---|---|---|---|
| **Agent Brain** | Claude Sonnet 4 | claude-sonnet-4-20250514 | Anthropic API · Tool-use mode |
| **MCP Framework** | Official MCP Python SDK | `mcp >= 1.0` | Spec-compliant, stdio transport |
| **Jira Integration** | Jira REST API v3 | v3 | HTTP via `httpx` |
| **Browser Automation** | Playwright Python | `>= 1.40` | Chromium headless |
| **Scheduler** | APScheduler | `>= 3.10` | IST timezone, cron triggers |
| **State Database** | SQLite + aiosqlite | `>= 0.19` | File-based, async-compatible |
| **HTTP Client** | httpx | `>= 0.27` | Async, used in Jira + Twilio calls |
| **Notifications** | **Twilio** | `>= 9.0` | WhatsApp Business + SMS fallback |
| **Retry Logic** | tenacity | `>= 8.2` | Exponential backoff decorator |
| **Logging** | loguru | `>= 0.7` | Rotating, structured logs |
| **Secrets** | python-dotenv | `>= 1.0` | `.env` file management |
| **Holiday Detection** | holidays | `>= 0.46` | Indian national holidays |
| **Status Server** | FastAPI | `>= 0.110` | Lightweight observability HTTP server |
| **Containerization** | Docker + Compose | Docker 24+ | Azure VM deployment |

### 2.2 Twilio vs Telegram — Why Twilio Wins for This Use Case

This deserves a full comparison because Telegram was used in v2. Here is the honest breakdown:

| Factor | Telegram | Twilio WhatsApp | Twilio SMS |
|---|---|---|---|
| **App Required** | ✅ Telegram app must be installed | ✅ WhatsApp (already on your phone) | ❌ No app needed — native SMS |
| **Reliability** | Good (depends on Telegram servers) | Excellent (Meta infrastructure) | Excellent (carrier-grade) |
| **Delivery Guarantee** | No read receipts by default | WhatsApp delivery receipts ✅ | Delivery receipts ✅ |
| **Works Without Internet (recipient)** | ❌ Requires internet | ❌ Requires internet | ✅ SMS over cellular |
| **API Complexity** | Simple HTTP bot API | Medium (Twilio SDK) | Simple (Twilio SDK) |
| **Cost** | Free | ~$0.005/message (WhatsApp) | ~$0.0075/message (SMS India) |
| **Monthly Cost (2 msgs/day × 22 days)** | Free | ~$0.22/month | ~$0.33/month |
| **Professional Appearance** | Bot username shows | Business name shows | Your Twilio number |
| **Fallback Capability** | No built-in fallback | Yes — can fall back to SMS | N/A (already SMS) |
| **Student Budget Impact** | None | Minimal (~$2.64/year) | Minimal (~$3.96/year) |
| **Programmable (dynamic message templates)** | Yes | Yes | Yes |
| **WhatsApp Business Approval Needed** | No | Yes (or use Sandbox for testing) | No |

**Verdict:** For a personal automation project where you want maximum reliability and delivery on your primary phone number, **Twilio WhatsApp is the best choice**. You already have WhatsApp. Messages arrive with delivery receipts. If WhatsApp fails, you configure automatic SMS fallback. Telegram requires everyone to have Telegram installed — Twilio sends to your phone number directly.

**Cost vs. Peace of Mind:** At ~$0.22/month, Twilio WhatsApp costs essentially nothing and your Azure student credit of $100 comfortably covers it for the full year (it would cost ~$2.64/year for WhatsApp messages alone).

### 2.3 Twilio Setup Overview

**WhatsApp Business API (via Twilio Sandbox — Free for Development):**

1. Create Twilio account at `console.twilio.com`
2. Get your `Account SID` and `Auth Token`
3. Go to Messaging → Try it Out → Send a WhatsApp Message
4. Connect your WhatsApp number to the Twilio sandbox (send a join code once)
5. For production (after testing): Apply for WhatsApp Business approval OR keep using sandbox (sandbox requires re-joining every 72 hours — fine for testing, not for production)
6. For production without approval friction: use **Twilio SMS** — no approval needed, works immediately

**Recommended Approach:**
- **Phase 1–3 (Development):** Twilio WhatsApp Sandbox (free)
- **Phase 4+ (Production):** Twilio SMS (no approval process, immediate, ~$0.33/month)

**Environment Variables:**

```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+14155238886        # Twilio WhatsApp sandbox number
                                        # OR your purchased Twilio number for SMS
TWILIO_TO_NUMBER=+919xxxxxxxxx         # Your Indian mobile number with country code
TWILIO_CHANNEL=whatsapp               # or "sms"
```

### 2.4 Twilio Notification MCP Server — Tool Design

**Server Name:** `notification-mcp`
**Tools:**

#### Tool 1: `send_whatsapp`
- **Purpose:** Send formatted WhatsApp message via Twilio
- **API:** Twilio Messages API (`POST /2010-04-01/Accounts/{SID}/Messages.json`)
- **From:** `whatsapp:+14155238886` (sandbox) or your Twilio WhatsApp number
- **To:** `whatsapp:+91XXXXXXXXXX` (your number)
- **Body:** Plain text (WhatsApp doesn't support HTML; use emoji + line breaks)
- **Delivery:** Returns `message_sid`; delivery status via Twilio webhook (optional)

#### Tool 2: `send_sms`
- **Purpose:** SMS fallback when WhatsApp fails
- **API:** Same Twilio Messages API, without `whatsapp:` prefix on numbers
- **When Used:** Called automatically when `send_whatsapp` fails after 3 retries

#### Tool 3: `send_alert` (Critical Failures Only)
- **Purpose:** Urgent failure alert — bypasses the 7:30 PM notification schedule
- **Behavior:** Sends immediately when a critical step (create_subtask, add_worklog) fails permanently
- **Format:** SMS (not WhatsApp) for guaranteed immediate delivery

#### Message Format — Twilio WhatsApp (plain text with emoji)

```
📊 Daily Automation Report
📅 Wednesday, 15 January 2025
Internship Day 4

─────────────────────
✅ Subtask Created: PROJ-456
   ravi_zapadiya - day_4 - RAG, Chatbots, Agentic AI

✅ Worklog Submitted
   8h from 11:00 AM IST

✅ Subtask Marked: Done

✅ Timesheet Synced
   8h confirmed on portal
─────────────────────
🎉 Today's routine completed!
⏱️ Automation took: 52 seconds
```

**Failure Report:**

```
⚠️ Automation Partial Failure
📅 Wednesday, 15 January 2025

✅ Subtask Created: PROJ-456
✅ Worklog Submitted: 8h
✅ Subtask Marked: Done
❌ Timesheet Sync: FAILED

Error: TimeoutError on sync button
Screenshot saved: timesheet_error_20250115.png

Action needed: Login to timesheet portal
manually and sync Jira logs.
```

---

### 2.5 Why Jira API, Not Browser Automation for Jira?

This is a critical architectural decision:

| Factor | Jira REST API | Browser Automation for Jira |
|---|---|---|
| **Reliability** | ✅ Stable, versioned, never breaks from UI redesigns | ❌ Breaks whenever Atlassian updates the UI |
| **Speed** | ✅ ~200ms per API call | ❌ 3–10 seconds per browser action |
| **Auth Complexity** | ✅ Simple API token (Bearer auth) | ❌ Must handle SSO, 2FA, session cookies |
| **Error Clarity** | ✅ HTTP status codes + JSON error body | ❌ Must parse visual page state |
| **Parallel Actions** | ✅ Can fire multiple requests | ❌ Sequential UI interactions only |
| **Verdict** | **Always use API for Jira** | Only as absolute last resort |

### 2.6 Why Browser Automation for Timesheet?

| Factor | Assessment |
|---|---|
| **Does it have a public API?** | Internal portals almost never expose REST APIs |
| **Is the portal SSO-locked?** | Likely yes — browser handles SSO flows naturally |
| **Alternative?** | Network traffic inspection might reveal internal APIs, but fragile |
| **Verdict** | **Browser automation (Playwright) is the correct tool here** |

### 2.7 Complete Dependency List

```
# requirements.txt

# MCP Framework
mcp>=1.0.0

# Anthropic Agent
anthropic>=0.34.0

# Jira HTTP Client
httpx>=0.27.0

# Browser Automation
playwright>=1.40.0

# Scheduler
apscheduler>=3.10.0

# Database
aiosqlite>=0.19.0

# Notifications
twilio>=9.0.0

# Observability
fastapi>=0.110.0
uvicorn>=0.29.0

# Reliability
tenacity>=8.2.0

# Logging
loguru>=0.7.0

# Secrets
python-dotenv>=1.0.0

# Holiday Detection
holidays>=0.46

# Async utilities
asyncio
```

---

## 3. MCP Components — Full Design

### 3.1 MCP Architecture Overview

MCP (Model Context Protocol) allows Claude to call external tools through a standardized JSON-RPC protocol over stdio (subprocess pipes). Each MCP server is a standalone Python process that:

1. Declares its available tools (name, description, input schema)
2. Receives tool call requests from the orchestrator
3. Executes the action (API call, browser action, DB read/write)
4. Returns structured results as text content

The orchestrator (Claude agent) spawns these servers as subprocesses and communicates with them over stdio.

```
Claude Agent (orchestrator)
       │
       │  spawn subprocess
       ▼
  Python MCP Server (jira_mcp/server.py)
       │
       │  stdio pipe (JSON-RPC)
       │
       │  REQUEST:  {"method": "tools/call", "params": {"name": "create_subtask", ...}}
       │  RESPONSE: {"result": {"content": [{"type": "text", "text": "{...json...}"}]}}
```

### 3.2 MCP Server Overview

The system runs four MCP servers as subprocesses managed by the agent client:

| Server | Tools | Backend | Transport | Purpose |
|---|---|---|---|---|
| `jira-mcp` | 10 tools | Jira REST API v3 | stdio | All Jira operations |
| `browser-mcp` | 5 tools | Playwright Chromium | stdio | Timesheet portal |
| `notification-mcp` | 3 tools | Twilio API | stdio | WhatsApp + SMS alerts |
| `state-mcp` | 6 tools | SQLite (aiosqlite) | stdio | State management |

### 3.3 Jira MCP Server — Complete Tool Inventory

**Server Name:** `jira-mcp`
**Transport:** stdio
**Dependencies:** `httpx`, `python-dotenv`

**Authentication:** Jira Cloud uses Basic Auth with `email:api_token`. The API token is generated at `id.atlassian.com → Security → API Tokens`. Never use your account password.

**Base URL Pattern:** `https://yourcompany.atlassian.net/rest/api/3/`

Quick reference table:

| Tool | API Endpoint | Purpose |
|---|---|---|
| `get_my_account_id` | `GET /rest/api/3/myself` | Get current user's Jira `accountId` |
| `get_parent_story` | `GET /rest/api/3/issue/{key}` | Fetch parent story title and project key |
| `check_subtask_exists` | `GET /rest/api/3/search` (JQL) | Idempotency — detect existing subtask |
| `create_subtask` | `POST /rest/api/3/issue` | Create daily subtask with formatted name |
| `add_label` | `PUT /rest/api/3/issue/{key}` | Apply personal label (uses `update.labels`) |
| `set_time_estimate` | `PUT /rest/api/3/issue/{key}` | Set 8h estimate (28800 seconds) |
| `assign_issue` | `PUT /rest/api/3/issue/{key}/assignee` | Assign to self using `accountId` |
| `get_issue_transitions` | `GET /rest/api/3/issue/{key}/transitions` | Discover transition IDs dynamically |
| `transition_issue` | `POST /rest/api/3/issue/{key}/transitions` | Move to In Progress / Done |
| `add_worklog` | `POST /rest/api/3/issue/{key}/worklog` | Log 8h at 11:00:00+0530 IST |

#### Deep Tool Inventory

#### Tool 1: `get_my_account_id`
- **Purpose:** Retrieve the authenticated user's Jira account ID
- **Why needed:** Jira's `assign_issue` endpoint requires `accountId` (not email, not username — the internal UUID-like ID)
- **API Endpoint:** `GET /rest/api/3/myself`
- **Returns:** `accountId`, `displayName`, `emailAddress`
- **Called:** Once per morning session, cached in agent memory

#### Tool 2: `get_parent_story`
- **Purpose:** Fetch the active parent Jira Story that the intern is working under
- **Why needed:** To extract the story's summary (title) for building the subtask name, and its `project_key` for creating the subtask
- **API Endpoint:** `GET /rest/api/3/search` with JQL filter
- **JQL Used:** `issuekey = {PARENT_KEY}` (hardcoded from config) — most reliable approach
- **Fallback JQL:** `assignee = currentUser() AND issuetype = Story AND status != Done ORDER BY created DESC LIMIT 1`
- **Returns:** Issue key, summary, project key, labels, status
- **Critical Field:** `summary` — this becomes the third segment of the subtask name

#### Tool 3: `check_subtask_exists`
- **Purpose:** Idempotency check — prevents duplicate subtask creation
- **Why needed:** If the agent crashes after creating a subtask but before saving state, the next run must detect the existing subtask
- **API Endpoint:** `GET /rest/api/3/search` with JQL
- **JQL Used:** `parent = {PARENT_KEY} AND summary ~ "day_{N}" AND issuetype = Subtask AND created >= startOfDay()`
- **Returns:** `{ "exists": true/false, "issue_key": "PROJ-456" or null }`
- **Decision:** If `exists = true`, save the key to state DB and skip creation

#### Tool 4: `create_subtask`
- **Purpose:** Create the daily subtask under the parent story
- **API Endpoint:** `POST /rest/api/3/issue`
- **Payload Structure:** `fields.project.key`, `fields.parent.key`, `fields.summary` (the formatted name), `fields.issuetype.name = "Subtask"`, optional `fields.description`
- **Returns:** New issue `key` (e.g., `PROJ-456`) and `id`
- **Name Format:** `{firstname_surname} - day_{N} - {parent_story_title}`
  - Example: `ravi_zapadiya - day_4 - RAG, Chatbots, Agentic AI`
- **Important:** The Jira description field uses Atlassian Document Format (ADF), not plain text

#### Tool 5: `add_label`
- **Purpose:** Apply the intern's personal tag/label to the subtask
- **API Endpoint:** `PUT /rest/api/3/issue/{issueKey}` using the `update` field (not `fields`) to avoid overwriting existing labels
- **Payload:** `{ "update": { "labels": [{ "add": "your-label-name" }] } }`
- **Why `update` not `fields`:** Using `fields.labels = [...]` overwrites all labels; `update.labels` appends safely
- **Returns:** HTTP 204 (no body) on success

#### Tool 6: `set_time_estimate`
- **Purpose:** Set the original time estimate to 8 hours
- **API Endpoint:** `PUT /rest/api/3/issue/{issueKey}`
- **Payload:** Uses `timetracking` update. Value must be in seconds: `28800` (8 × 60 × 60)
- **Alternative:** Can also use Jira's time format string `"8h"` depending on your Jira instance configuration
- **Note:** Jira Cloud may require `timetracking` to be enabled in the project settings

#### Tool 7: `assign_issue`
- **Purpose:** Assign the subtask to the current user
- **API Endpoint:** `PUT /rest/api/3/issue/{issueKey}/assignee`
- **Payload:** `{ "accountId": "5f7a8b9c..." }` — uses the `accountId` retrieved in Tool 1
- **Returns:** HTTP 204 on success

#### Tool 8: `get_issue_transitions`
- **Purpose:** Discover available workflow transitions for the issue
- **Why needed:** Transition IDs vary between Jira projects. Never hardcode "In Progress" = 21. Always fetch dynamically.
- **API Endpoint:** `GET /rest/api/3/issue/{issueKey}/transitions`
- **Returns:** Array of `{ "id": "21", "name": "In Progress", "to": {...} }`
- **Agent Logic:** Find the transition whose `name` contains "progress" (case-insensitive match)

#### Tool 9: `transition_issue`
- **Purpose:** Change the issue status (to "In Progress" in morning, "Done" in evening)
- **API Endpoint:** `POST /rest/api/3/issue/{issueKey}/transitions`
- **Payload:** `{ "transition": { "id": "{transition_id}" } }`
- **Note:** The `transition_id` must be fetched fresh via Tool 8, not hardcoded

#### Tool 10: `add_worklog`
- **Purpose:** Log 8 hours of work, starting at 11:00 AM IST on the current day
- **API Endpoint:** `POST /rest/api/3/issue/{issueKey}/worklog`
- **Critical fields:**
  - `started`: Must be in format `"2025-01-15T11:00:00.000+0530"` — the `+0530` IST offset is mandatory
  - `timeSpent`: `"8h"`
- **Common Bug:** If the timezone offset is missing or wrong, Jira logs the time incorrectly. Always hardcode `+0530` for IST.
- **Returns:** `worklog_id`, `timeSpent`, `started`

---

### 3.4 Browser MCP Server — Complete Tool Inventory

**Server Name:** `browser-mcp`
**Transport:** stdio
**Dependencies:** `playwright`, `asyncio`
**Browser:** Chromium (headless mode in production, headed mode for debugging)

**Important Note:** The exact CSS selectors, button text, and page flow in the tools below are **templates**. Before coding, you must inspect your actual timesheet portal's HTML using Chrome DevTools and update the selectors accordingly.

#### How to Inspect Your Timesheet Portal

1. Open your timesheet portal in Chrome
2. Press `F12` → Open DevTools → Elements tab
3. Click the cursor icon (Inspect element)
4. Click the Login button → copy the selector
5. Click the Sync button → copy the selector
6. Look for the hours table → note the structure
7. Document: button IDs, class names, ARIA labels, and placeholder text

Quick reference table:

| Tool | Purpose | Failure Behavior |
|---|---|---|
| `login_timesheet` | Navigate + authenticate to portal | Screenshot + SMS alert |
| `sync_jira_logs` | Click Sync button, wait for completion | Screenshot + SMS alert |
| `confirm_hours` | Assert 8h appears on today's row | Screenshot + WhatsApp partial-fail alert |
| `take_screenshot` | Capture current page for debugging | Always succeeds |
| `get_page_content` | Return visible page text for agent inspection | Returns empty string on error |

#### Deep Tool Inventory

#### Tool 1: `login_timesheet`
- **Purpose:** Authenticate into the company timesheet portal
- **Flow:**
  1. Navigate to `TIMESHEET_URL`
  2. Wait for page load (`networkidle` state)
  3. Detect login form — try multiple selector strategies:
     - `input[type="email"]` or `input[name="username"]` or `#username`
     - `input[type="password"]` or `input[name="password"]` or `#password`
     - `button[type="submit"]` or `.login-button` or `input[type="submit"]`
  4. Fill credentials from environment variables
  5. Click submit
  6. Wait for redirect to dashboard
  7. Assert URL changed (not still on login page)
- **Returns:** `{ "status": "logged_in", "current_url": "...", "page_title": "..." }`
- **On Failure:** Take screenshot, return error with screenshot path

#### Tool 2: `sync_jira_logs`
- **Purpose:** Trigger the "Sync from Jira" action in the timesheet portal
- **Flow:**
  1. Look for sync button using multiple strategies:
     - By role: `page.get_by_role("button", name=re.compile("sync|jira", re.IGNORECASE))`
     - By text: `page.get_by_text("Sync", exact=False)`
     - By attribute: `[data-action="sync"]`, `#syncJira`, `.sync-jira-btn`
  2. Click the button
  3. Wait for the loading indicator to disappear (if any)
  4. Wait for `networkidle` state
  5. Capture current page text to confirm sync happened
- **Returns:** `{ "status": "synced", "confirmation_text": "..." }`
- **Selector Fallback Strategy:** Try 3 different selectors sequentially; if all fail, take screenshot and alert

#### Tool 3: `confirm_hours`
- **Purpose:** Verify that 8 hours appear in today's timesheet row
- **Flow:**
  1. Read the inner text of the main content area
  2. Look for patterns: `"8h"`, `"8:00"`, `"08:00"`, `"480 min"`, `"8.0"`
  3. Optionally: find today's date row in the timesheet table and check the hours cell
- **Returns:** `{ "status": "confirmed", "has_8h": true/false, "found_text": "8h" }`
- **If not confirmed:** Take screenshot, log as partial failure, send Twilio alert asking for manual check

#### Tool 4: `take_screenshot`
- **Purpose:** Capture current browser state for debugging
- **Flow:** `page.screenshot(full_page=True)` → save to `logs/screenshots/YYYYMMDD_HHMMSS.png`
- **Called automatically** on any tool failure
- **Returns:** Path to saved screenshot file

#### Tool 5: `get_page_content`
- **Purpose:** Return visible text content of the current page for agent inspection
- **Used by:** The Claude agent to diagnose unexpected page states
- **Returns:** First 2000 characters of `page.inner_text("body")`

---

### 3.5 Notification MCP Server — 3 Tools (Twilio)

| Tool | Channel | When Used | Failure Fallback |
|---|---|---|---|
| `send_whatsapp` | Twilio WhatsApp API | Normal workflow messages | Falls back to `send_sms` |
| `send_sms` | Twilio SMS API | WhatsApp failures, critical alerts | Log to file only |
| `send_alert` | SMS (direct) | Critical failures needing immediate action | Log + write to `data/failed_alerts.txt` |

**Smart Fallback Chain:**

```
send_whatsapp() called
       │
       ├── SUCCESS → Message delivered to WhatsApp ✅
       │
       └── FAIL (Twilio API error / WhatsApp unavailable)
               │
               └── AUTO-RETRY send_sms() as fallback
                       │
                       ├── SUCCESS → SMS delivered ✅
                       │
                       └── FAIL (Twilio down / no credit)
                               │
                               └── Log to data/failed_alerts.txt
                                   Write to state DB: notification_failed=1
                                   (Observability layer still shows status)
```

---

### 3.6 State MCP Server — 6 Tools + Updated Schema

**Server Name:** `state-mcp`
**Transport:** stdio
**Dependencies:** `aiosqlite`
**Database File:** `data/automation_state.db` (auto-created on first run)

#### Updated Database Schema (v4.0)

**Table: `daily_runs`**

| Column | Type | New in v3/v4? | Description |
|---|---|---|---|
| `run_date` | TEXT (PK) | — | ISO date: `2025-01-15` |
| `day_number` | INTEGER | — | Working day count since internship start |
| `subtask_key` | TEXT | — | Jira issue key: `PROJ-456` |
| `morning_done` | INTEGER | — | 0 or 1 |
| `evening_done` | INTEGER | — | 0 or 1 |
| `timesheet_done` | INTEGER | — | 0 or 1 |
| `notification_done` | INTEGER | — | 0 or 1 |
| `notification_channel` | TEXT | ✅ NEW | `"whatsapp"` or `"sms"` or `"failed"` |
| `notification_sid` | TEXT | ✅ NEW | Twilio message SID (for delivery tracking) |
| `morning_duration_sec` | INTEGER | ✅ NEW | How long morning agent took |
| `evening_duration_sec` | INTEGER | ✅ NEW | How long evening agent took |
| `is_leave_day` | INTEGER | ✅ NEW | 1 if manually marked as leave |
| `skip_reason` | TEXT | ✅ NEW | "weekend", "holiday", "leave", "already_done" |
| `error_log` | TEXT | — | Accumulated error messages |
| `created_at` | TEXT | — | ISO datetime |
| `updated_at` | TEXT | — | ISO datetime |

**Table: `config`**

| Key | Value | Purpose |
|---|---|---|
| `start_date` | `2025-01-06` | Day counter start |
| `parent_jira_key` | `PROJ-100` | The parent story |
| `my_label` | `ravi-zapadiya` | Personal Jira label |
| `my_username_prefix` | `ravi_zapadiya` | Subtask name prefix |
| `twilio_channel` | `whatsapp` | Default notification channel |
| `human_approval_mode` | `false` | Enable/disable approval prompts |
| `observability_port` | `5050` | Status HTTP server port |

#### Tool Descriptions

| Tool | Purpose |
|---|---|
| `get_today_state` | Returns the full row for today's date from `daily_runs`. If no row exists, returns `{ "exists": false }` |
| `set_today_state` | Upserts fields into today's row (INSERT if new date, UPDATE otherwise) |
| `get_day_number` | Calculates count of working days (Mon–Fri, non-holidays) from `start_date` to today |
| `get_config` / `set_config` | Read or write key-value pairs from the `config` table |
| `log_error` | Appends timestamped error message to today's `error_log` field |
| `get_historical_state` | Returns state for a specific past date (for catch-up checking) |

---

### 3.7 MCP Client — How the Orchestrator Connects

The agent runs a **client** that spawns all four MCP servers as subprocesses and maintains sessions:

```
Agent Process (main Python process)
├── Spawns: python mcp_servers/jira_mcp/server.py      → Session "jira"
├── Spawns: python mcp_servers/browser_mcp/server.py   → Session "browser"
├── Spawns: python mcp_servers/notification_mcp/server.py → Session "notification"
└── Spawns: python mcp_servers/state_mcp/server.py     → Session "state"
```

Tool naming convention for the agent: `{server}__{tool_name}`
- Example: `jira__create_subtask`, `browser__login_timesheet`, `state__get_today_state`

This naming prevents collisions when all tools from all servers are passed to Claude simultaneously.

---

## 4. Daily Workflow — Exact Execution Flow

### 4.1 Morning Workflow — 16 Steps

| Step | Action | Tool | Critical? |
|---|---|---|---|
| 1 | Read today's state | `state__get_today_state` | Yes |
| 2 | Guard: morning_done=1? | Agent decision | Yes — EXIT if true |
| 3 | Catch-up: check yesterday | `state__get_historical_state` | No — alert only |
| 4 | Get working day number | `state__get_day_number` | Yes |
| 5 | Get my Jira account ID | `jira__get_my_account_id` | Yes |
| 6 | Get parent story details | `jira__get_parent_story` | Yes |
| 7 | Check subtask exists | `jira__check_subtask_exists` | Yes (idempotency) |
| 8 | Guard: subtask exists? | Agent decision | Yes — skip creation if true |
| 9 | Create subtask | `jira__create_subtask` | ⛔ CRITICAL |
| 10 | Add label | `jira__add_label` | No — non-critical |
| 11 | Set 8h estimate | `jira__set_time_estimate` | No — non-critical |
| 12 | Assign to myself | `jira__assign_issue` | No — non-critical |
| 13 | Get transitions | `jira__get_issue_transitions` | Yes |
| 14 | Transition → In Progress | `jira__transition_issue` | Yes |
| 15 | Save state | `state__set_today_state` | ⛔ CRITICAL |
| 16 | Send morning summary | `notification__send_whatsapp` | No — non-critical |

**Total estimated time:** 8–15 seconds for the entire morning workflow.

### 4.2 Evening Workflow — 12 Steps

| Step | Action | Tool | Critical? |
|---|---|---|---|
| 1 | Read today's state | `state__get_today_state` | Yes |
| 2 | Guard: evening_done=1? | Agent decision | Yes — EXIT if true |
| 3 | Guard: morning_done=0? | Agent decision | Alert but continue |
| 4 | Get "Done" transition | `jira__get_issue_transitions` | Yes |
| 5 | Transition → Done | `jira__transition_issue` | ⛔ CRITICAL |
| 6 | Add 8h worklog at 11 AM | `jira__add_worklog` | ⛔ CRITICAL |
| 7 | Save Jira evening state | `state__set_today_state` | ⛔ CRITICAL |
| 8 | Login to timesheet | `browser__login_timesheet` | Yes |
| 9 | Sync Jira logs | `browser__sync_jira_logs` | Yes |
| 10 | Confirm 8h logged | `browser__confirm_hours` | Alert if fails |
| 11 | Save timesheet state | `state__set_today_state` | Yes |
| 12 | SMS alert if anything failed | `notification__send_alert` | No — non-critical |

**Total estimated time:** 30–90 seconds (browser operations take longer).

### 4.3 Notification Job — 7:30 PM (Pure Python)

This job does NOT call the Claude agent. It is pure Python logic that reads the state and sends a formatted Twilio message.

**Why no LLM here?** The notification is deterministic — read state, format message, send. No reasoning needed. Saves API cost and latency. (See Section 5 for full 7-reason breakdown.)

### 4.4 Scheduler Configuration — All Three Jobs

| Job | Cron Expression (IST) | Timezone | Max Jitter | Coalesce | Misfire Grace |
|---|---|---|---|---|---|
| Morning Routine | `0 11 * * MON-FRI` | `Asia/Kolkata` | 30 seconds | True | 2 hours |
| Evening Routine | `0 19 * * MON-FRI` | `Asia/Kolkata` | 30 seconds | True | 2 hours |
| Notification | `30 19 * * MON-FRI` | `Asia/Kolkata` | 0 | True | 30 minutes |

**`coalesce=True`:** If the scheduler was offline and missed a trigger, it will run the job once (not N times) when it comes back online.

**`misfire_grace_time=7200`:** If the scheduler starts late (e.g., laptop was asleep), it will still run the morning job if it's within 2 hours of 11 AM.

**`max_jitter=30`:** Adds up to 30 seconds of random delay to avoid exact-second API hammering.

---

## 5. The Intelligence Boundary — Why 7:30 PM Skips Claude

This is the most architecturally significant decision in the entire system. It deserves a complete, honest explanation.

### 5.1 What "Intelligence" Actually Means in This Context

Claude (or any LLM) adds value in exactly one scenario: **when the output cannot be determined mechanically from the inputs**. Said differently: use an LLM when you need *reasoning*, and use plain code when you need *computation*.

Ask yourself this question about the 7:30 PM notification job:

> *"Given the state DB has: morning_done=1, evening_done=1, timesheet_done=1, subtask_key='PROJ-456', day_number=4 — what should the notification message say?"*

The answer is **completely, 100% deterministic**. Every single word of the output can be computed from the input flags with a chain of if/else statements. There is no ambiguity. There is nothing to reason about. The output is always the same for the same inputs.

This is the Intelligence Boundary: **on this side, use Claude. On that side, use Python.**

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INTELLIGENCE BOUNDARY                             │
│                                                                          │
│  ← Use Claude                         Use Plain Python →                 │
│                                                                          │
│  "The Jira transition has              "morning_done=1?                  │
│   failed 3 times. Should I             → print ✅ Subtask Created"       │
│   try a different transition           "morning_done=0?                  │
│   name, or mark it as error            → print ❌ Subtask FAILED"        │
│   and alert the user?"                                                   │
│                                                                          │
│  "The timesheet page shows             "evening_done=1?                  │
│   unexpected content. Is              → print ✅ Worklog Submitted"      │
│   this a login wall or a              "timesheet_done=1?                 │
│   redesigned UI?"                     → print ✅ Timesheet Synced"       │
│                                                                          │
│  ← Requires reasoning                 Requires zero reasoning →          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 5.2 The Seven Concrete Reasons Not to Use Claude at 7:30 PM

#### Reason 1: Output Is Fully Deterministic

The notification message has exactly `2^4 = 16` possible states (morning_done × evening_done × timesheet_done × notification_failed, each 0 or 1). You can write 16 if/else branches in Python in 10 minutes. Claude would produce the same 16 outputs — it adds no new information.

#### Reason 2: Latency

Claude API call takes 1–4 seconds. A Python function that reads SQLite and formats a string takes 2 milliseconds. For a notification job, the user is waiting for the message. Why add 4 seconds of unnecessary API latency to a 2-millisecond operation?

#### Reason 3: Cost

Small, but real. Each Claude call with the tool list and conversation history costs approximately $0.003–$0.006. That is $0.066–$0.132/month just for the 7:30 PM job (22 working days). Over 6 months of internship: up to $0.79 wasted on computation a for-loop could do.

#### Reason 4: Failure Surface

Every dependency you add is a potential failure point. If the 7:30 PM notification job calls Claude, the Anthropic API must be reachable, your API key must be valid, and Claude must not hallucinate a different message format. With pure Python, the SQLite read essentially always succeeds and string formatting always does.

#### Reason 5: The Message Can't Be Wrong

If Claude generates the notification, it could theoretically phrase something differently than expected. With Python, the message format is 100% controlled — you know exactly what you'll receive, every time, byte-for-byte.

#### Reason 6: No Tool Calls Needed

The entire purpose of Claude in this system is to orchestrate tool calls. The 7:30 PM job makes exactly zero tool calls. There is nothing for Claude to orchestrate.

#### Reason 7: Violates the "Use the Right Tool" Principle

Using an LLM for something a for-loop can do is like using a chainsaw to slice bread. Claude is a valuable, expensive, rate-limited resource. Reserve it for tasks that actually need it.

### 5.3 When You SHOULD Use Claude in a Notification Context

| Scenario | Should Use Claude? | Why |
|---|---|---|
| "7:30 PM daily summary" | ❌ No | Deterministic — see above |
| "Something failed — should I retry or alert?" | ✅ Yes | Requires contextual reasoning about error type |
| "The timesheet page shows unexpected content — is this a CAPTCHA or redesigned UI?" | ✅ Yes | Requires visual/text interpretation |
| "Generate a personalized standup note from today's Jira activity" | ✅ Yes | Natural language generation from structured data |
| "The Jira transition failed — try this alternative workflow?" | ✅ Yes | Error recovery reasoning |
| "Send a weekly performance summary with insights" | ✅ Yes | Analysis + natural language generation |

So the rule is precise: **"Is the output derivable from the input by mechanical rules, with no ambiguity?"** If yes → Python. If no → Claude.

### 5.4 What the 7:30 PM Job Actually Does (Architecture)

```
SCHEDULER (7:30 PM IST)
         │
         ▼
  read_today_state()          ← Direct aiosqlite call (no MCP, no Claude)
         │
         ▼
  build_notification_message(state)   ← Pure Python string formatting
         │                               16 possible if/else outcomes
         ▼
  send_via_twilio(message)    ← Direct httpx POST to Twilio API (no MCP)
         │
         ├── SUCCESS: WhatsApp delivered → mark notification_done=1
         │
         └── FAIL: Try SMS fallback → mark notification_channel="sms"
                     │
                     └── STILL FAIL: Write to data/failed_alerts.txt
                                     Mark notification_channel="failed"
                                     (User checks Observability Dashboard)
```

Notice: this job doesn't even open the MCP servers. It uses direct function calls to SQLite and Twilio. This makes it maximally fast, reliable, and independent of every other system component.

---

## 6. Observability Layer — Know Status Without Notifications

### 6.1 Why This Layer Exists

The user asked: *"How do I know if the task is done without waiting for a notification?"*

This is the right question. A production system must be observable independently of its notification mechanism. You should be able to check the status of today's automation:

- When your phone has no internet (can't receive WhatsApp)
- When Twilio is down
- When you're curious mid-day and don't want to wait until 7:30 PM
- When a notification arrived but you weren't sure if it was real or stale
- When you want historical data ("did it run last Tuesday?")

The answer is the **Observability Layer**: three independent mechanisms that always show you the truth about what the automation has done.

---

### 6.2 Mechanism 1 — HTTP Status Dashboard (Port 5050)

A lightweight FastAPI server that runs alongside the scheduler. Always available on your Azure VM at `http://<azure-vm-ip>:5050/status`.

**Endpoints:**

#### `GET /status` — Today's Status (Primary Use)

Returns a clean HTML page (or JSON if you call with `Accept: application/json`):

```
╔══════════════════════════════════════════════════════╗
║     🤖 Intern Automation — Live Status Dashboard      ║
║        Last updated: 7:02:14 PM IST                   ║
╠══════════════════════════════════════════════════════╣
║  📅 Wednesday, 15 January 2025   |  Day 4             ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  MORNING ROUTINE (11:00 AM)                          ║
║  ✅ COMPLETED at 11:00:47 AM IST  (took 12 sec)      ║
║  📋 Subtask: PROJ-456                                ║
║     ravi_zapadiya - day_4 - RAG, Chatbots            ║
║                                                      ║
║  EVENING ROUTINE (7:00 PM)                           ║
║  ✅ COMPLETED at 7:01:23 PM IST  (took 52 sec)       ║
║  ⏱️  Worklog: 8h from 11:00 AM                       ║
║  📊 Timesheet: Synced (8h confirmed)                 ║
║                                                      ║
║  NOTIFICATION (7:30 PM)                              ║
║  ⏳ Pending (scheduled for 7:30 PM)                  ║
║                                                      ║
╠══════════════════════════════════════════════════════╣
║  ✅ Everything on track for today                    ║
╚══════════════════════════════════════════════════════╝
```

#### `GET /status/json` — Machine-Readable Status

```json
{
  "date": "2025-01-15",
  "day_number": 4,
  "subtask_key": "PROJ-456",
  "morning_done": true,
  "morning_completed_at": "2025-01-15T11:00:47+05:30",
  "morning_duration_sec": 12,
  "evening_done": true,
  "evening_completed_at": "2025-01-15T19:01:23+05:30",
  "evening_duration_sec": 52,
  "timesheet_done": true,
  "notification_done": false,
  "notification_scheduled": "2025-01-15T19:30:00+05:30",
  "errors": [],
  "overall_status": "completed"
}
```

#### `GET /history?days=7` — Last N Days

Returns a table showing the last 7 (or N) working days.

#### `GET /health` — System Health Check

Used by Azure health probes and your own monitoring.

#### `POST /mark-manual-done` — Override for Manual Actions

When you manually fixed something, call this to update state:

```
POST /mark-manual-done
Body: { "field": "timesheet_done", "value": 1, "note": "Synced manually at 7:15 PM" }
Response: { "status": "updated" }
```

**Security:** Protected by a simple bearer token in the request header. Set `DASHBOARD_TOKEN=your_secret_here` in `.env`.

---

### 6.3 Mechanism 2 — Twilio Two-Way Commands (Reply to WhatsApp/SMS)

Beyond just receiving notifications, you can **reply** to the Twilio number to query status on demand. This turns the notification channel into a bidirectional command interface.

| You send to Twilio number | Bot replies with |
|---|---|
| `STATUS` | Today's current automation state |
| `STATUS 2025-01-14` | That specific day's run history |
| `HISTORY 7` | Last 7 working days summary table |
| `LEAVE` | Marks today as personal leave, disables automation for today |
| `LEAVE 2025-01-20` | Marks a future date as leave |
| `RUN MORNING` | Manually triggers morning agent (with confirmation) |
| `RUN EVENING` | Manually triggers evening agent (with confirmation) |
| `APPROVE` | Approves pending human-approval-mode prompt |
| `CANCEL` | Cancels pending human-approval-mode prompt |
| `HELP` | Lists all commands |

---

### 6.4 Mechanism 3 — SQLite State Viewer (Local CLI)

For direct inspection without HTTP or Twilio. Run from the project directory:

**Command:** `python scripts/view_state.py`

```
═══════════════════════════════════════════════
 Intern Automation — State Viewer
 Database: data/automation_state.db
═══════════════════════════════════════════════

TODAY (Wednesday, 15 January 2025):
  Day Number:        4
  Subtask Key:       PROJ-456
  Morning Done:      ✅ Yes (11:00:47 AM, took 12s)
  Evening Done:      ✅ Yes (7:01:23 PM, took 52s)
  Timesheet Done:    ✅ Yes
  Notification:      ⏳ Pending (7:30 PM)
  Errors:            None

LAST 5 WORKING DAYS:
  14 Jan (Tue) Day 3  Morning ✅  Evening ✅  Timesheet ✅  Notify ✅
  13 Jan (Mon) Day 2  Morning ✅  Evening ✅  Timesheet ✅  Notify ✅
  10 Jan (Fri) Day 1  Morning ✅  Evening ✅  Timesheet ❌  Notify ✅(warn)
```

**Commands:**

```bash
python scripts/view_state.py                    # Today + last 5 days
python scripts/view_state.py --days 30          # Last 30 days
python scripts/view_state.py --date 2025-01-14  # Specific date
python scripts/view_state.py --errors           # Only show days with errors
python scripts/view_state.py --fix morning_done 1  # Manually set a flag
```

---

### 6.5 Mechanism 4 — Log File (Always-On Audit Trail)

Every action is written to `logs/automation.log` with structured format:

```
2025-01-15 11:00:00.123 | INFO     | scheduler.jobs:morning_job | Morning job triggered
2025-01-15 11:00:01.432 | INFO     | agent.morning_agent | Tool call: jira__get_my_account_id
2025-01-15 11:00:01.889 | SUCCESS  | agent.morning_agent | accountId: 5f7a8b9c... (Ravi Zapadiya)
2025-01-15 11:00:03.781 | SUCCESS  | agent.morning_agent | Created: PROJ-456 "ravi_zapadiya - day_4 - RAG, Chatbots, Agentic AI"
2025-01-15 11:00:05.612 | SUCCESS  | scheduler.jobs:morning_job | Morning routine completed in 5.5 seconds
```

**Log Rotation:** Daily rotation, 30-day retention, compressed. Location: `logs/automation.log`

---

### 6.6 Observability Decision Tree — "Is My Task Done?"

```
I want to know if today's task is done
             │
             ▼
 Did I receive a WhatsApp/SMS at 7:30 PM?
    ├── YES → Read the message → Done/Failed clearly stated
    └── NO  → (notification may have failed)
                     │
                     ▼
         Open http://<azure-ip>:5050/status
            ├── Page loads → Read the status dashboard
            └── Page doesn't load → Azure VM may be down
                         │
                         ▼
              Send "STATUS" to your Twilio number
                 ├── Receives reply → Status in WhatsApp
                 └── No reply → Twilio or VM down
                              │
                              ▼
                  SSH into Azure VM
                  Run: python scripts/view_state.py
```

Four independent mechanisms. If all four fail simultaneously, your Azure VM is down — check Azure Portal.

---

## 7. Codebase Structure — Updated

### 7.1 Complete Folder Tree (v4.0)

```
intern-automation/
│
├── 📄 README.md
├── 📄 .env                              ← All secrets — NEVER COMMIT
├── 📄 .env.example                      ← Template — commit this
├── 📄 .gitignore
├── 📄 requirements.txt
├── 📄 docker-compose.yml                ← Azure deployment config
├── 📄 Dockerfile
│
├── 📁 config/
│   ├── 📄 settings.py                   ← All constants from .env
│   ├── 📄 holidays_config.py            ← Company holidays dict
│   └── 📄 mcp_client_config.py          ← MCP server spawn params
│
├── 📁 mcp_servers/
│   ├── 📁 jira_mcp/
│   │   ├── 📄 __init__.py
│   │   └── 📄 server.py                 ← Jira REST API (10 tools)
│   ├── 📁 browser_mcp/
│   │   ├── 📄 __init__.py
│   │   └── 📄 server.py                 ← Playwright timesheet (5 tools)
│   ├── 📁 notification_mcp/
│   │   ├── 📄 __init__.py
│   │   └── 📄 server.py                 ← Twilio WhatsApp/SMS (3 tools)
│   └── 📁 state_mcp/
│       ├── 📄 __init__.py
│       └── 📄 server.py                 ← SQLite state (6 tools)
│
├── 📁 agent/
│   ├── 📄 __init__.py
│   ├── 📄 client.py                     ← MCP session manager
│   ├── 📄 morning_agent.py              ← Morning agentic loop
│   ├── 📄 evening_agent.py              ← Evening agentic loop
│   ├── 📄 prompts.py                    ← All Claude system prompts
│   └── 📄 tools_wrapper.py              ← Retry + error wrapper
│
├── 📁 scheduler/
│   ├── 📄 __init__.py
│   ├── 📄 main_scheduler.py             ← Entry point: APScheduler + FastAPI
│   ├── 📄 jobs.py                       ← morning_job, evening_job, notify_job
│   └── 📄 guards.py                     ← Weekend/holiday/leave checks
│
├── 📁 notifications/
│   ├── 📄 __init__.py
│   ├── 📄 twilio_client.py              ← Direct Twilio API (no MCP, used by notify job)
│   └── 📄 message_builder.py           ← Pure Python message formatter (16 states)
│
├── 📁 observability/
│   ├── 📄 __init__.py
│   ├── 📄 status_server.py              ← FastAPI HTTP server (port 5050)
│   ├── 📄 routes.py                     ← /status, /history, /health, /twilio-webhook
│   ├── 📄 state_reader.py               ← Helper: read state DB without MCP
│   └── 📄 templates/
│       └── 📄 status.html               ← HTML status dashboard template
│
├── 📁 scripts/
│   ├── 📄 setup.py                      ← First-time setup wizard
│   ├── 📄 run_morning.py                ← Manual morning trigger
│   ├── 📄 run_evening.py                ← Manual evening trigger
│   ├── 📄 test_jira.py                  ← Test Jira MCP isolation
│   ├── 📄 test_browser.py               ← Test Browser MCP isolation
│   ├── 📄 test_notify.py                ← Test Twilio send
│   └── 📄 view_state.py                 ← CLI state viewer
│
├── 📁 tests/
│   ├── 📄 test_guards.py
│   ├── 📄 test_day_counter.py
│   ├── 📄 test_name_formatter.py
│   ├── 📄 test_message_builder.py       ← NEW: test all 16 notification states
│   └── 📄 test_state_mcp.py
│
├── 📁 data/
│   ├── 📄 automation_state.db           ← SQLite (gitignored)
│   ├── 📁 backups/                      ← Daily DB backups
│   └── 📄 failed_alerts.txt            ← Fallback when Twilio fails
│
└── 📁 logs/
    ├── 📄 automation.log                ← Rotating (gitignored)
    └── 📁 screenshots/                 ← Browser failure screenshots (gitignored)
```

### 7.2 New Files Explained (vs v2.0)

| New File | Why Added |
|---|---|
| `notifications/twilio_client.py` | Replaces Telegram client; direct Twilio API calls for the non-MCP notification job |
| `notifications/message_builder.py` | The deterministic Python message formatter; covers all 16 state combinations; independently testable |
| `observability/status_server.py` | FastAPI server for HTTP status dashboard; runs alongside scheduler |
| `observability/routes.py` | All HTTP routes: `/status`, `/history`, `/health`, `/twilio-webhook`, `/mark-manual-done` |
| `observability/state_reader.py` | Read state DB directly without spawning MCP server (used by HTTP routes) |
| `observability/templates/status.html` | Clean HTML dashboard — readable on phone browser |
| `data/failed_alerts.txt` | Last-resort notification log when Twilio fails |
| `tests/test_message_builder.py` | Unit tests for all 16 notification message states |

### 7.3 Key File Responsibilities

| File | Responsibility | Depends On |
|---|---|---|
| `config/settings.py` | Single source of truth for all config values | `.env` |
| `config/holidays_config.py` | Dict of `{"YYYY-MM-DD": "Holiday Name"}` for company days off | Nothing |
| `config/mcp_client_config.py` | Dict of server name → `{command, args, env}` for spawning | `settings.py` |
| `agent/client.py` | Context manager that spawns all MCP servers and exposes `call_tool()` | `mcp_client_config.py` |
| `agent/prompts.py` | `MORNING_SYSTEM_PROMPT`, `EVENING_SYSTEM_PROMPT` constants | Nothing |
| `agent/morning_agent.py` | Runs the agentic loop using Claude API + MCP client | `client.py`, `prompts.py` |
| `scheduler/guards.py` | Returns `(should_run: bool, reason: str)` | `holidays`, `config` |
| `scheduler/jobs.py` | Wraps agents in try/except; called by APScheduler | `guards.py`, `morning_agent.py` |
| `scheduler/main_scheduler.py` | Starts the APScheduler with IST timezone; process entry point | `jobs.py` |
| `notifications/twilio_client.py` | Direct HTTP call to Twilio API (used in notification job) | `settings.py`, `httpx` |
| `notifications/message_builder.py` | 16-state deterministic message formatter | Nothing |
| `observability/status_server.py` | FastAPI server on port 5050 | `state_reader.py`, `settings.py` |
| `scripts/setup.py` | One-time setup wizard: validates `.env`, creates DB, sets config, tests connections | All |

---

## 8. Security Design

### 8.1 Updated Secrets Structure

```env
# ─── Jira ──────────────────────────────────────────────────────────────────────
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=ravi.zapadiya@company.com
JIRA_API_TOKEN=<from id.atlassian.com → Security → API Tokens>

# ─── Jira Workflow Config ──────────────────────────────────────────────────────
JIRA_PARENT_KEY=PROJ-100
JIRA_PROJECT_KEY=PROJ
MY_JIRA_LABEL=ravi-zapadiya
MY_USERNAME_PREFIX=ravi_zapadiya

# ─── Timesheet Portal ─────────────────────────────────────────────────────────
TIMESHEET_URL=https://timesheet.yourcompany.com
TIMESHEET_USERNAME=ravi.zapadiya
TIMESHEET_PASSWORD=<portal password>

# ─── Twilio (replaces Telegram) ───────────────────────────────────────────────
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=<from Twilio Console>
TWILIO_FROM_NUMBER=+14155238886
TWILIO_TO_NUMBER=+919xxxxxxxxx
TWILIO_CHANNEL=whatsapp

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-...

# ─── Application Config ───────────────────────────────────────────────────────
STATE_DB_PATH=data/automation_state.db
INTERN_START_DATE=2025-01-06
TIMEZONE=Asia/Kolkata
HUMAN_APPROVAL_MODE=false
LOG_LEVEL=INFO

# ─── Observability ────────────────────────────────────────────────────────────
DASHBOARD_PORT=5050
DASHBOARD_TOKEN=<random string — your password for the status page>
```

### 8.2 Azure-Specific Security

When deployed on Azure Student VM:

- **Network Security Group (NSG):** Allow only port 22 (SSH) and port 5050 (dashboard) inbound. Block everything else.
- **SSH Access:** Use SSH key pair, not password login
- **Secrets:** Never store `.env` in the repository. Use `scp` to copy it to the VM.
- **Dashboard Access:** The dashboard token protects the status page from public access. Change it from the default.
- **Azure Student Credit:** Monitor usage at `portal.azure.com → Cost Management`. The B1s VM + 5 GB storage should cost well under $5/month, leaving plenty of your $100 credit.

### 8.3 Twilio Security

- Twilio webhook validation: Verify the `X-Twilio-Signature` header on incoming webhook requests
- Only accept incoming messages from `TWILIO_TO_NUMBER` (your phone)
- Reject all other incoming numbers — don't let anyone else control your automation

### 8.4 Threat Model for a Personal Automation Tool

Even for personal use, consider these threats:

| Threat | Risk Level | Mitigation |
|---|---|---|
| Jira API token leaked via git | High | `.gitignore` `.env`; use `git secret` or GitHub secret scanning alerts |
| Timesheet password in code | Critical | Always from env variable, never hardcoded |
| Twilio credentials exposed | Medium | Token gives messaging rights only; still protect and rotate if exposed |
| Anthropic API key leaked | High | Will incur charges; protect and rotate if exposed |
| Unauthorized Jira actions | Low | Token is scoped to your user account only |
| State DB corruption | Low | SQLite is ACID-compliant; regular file backup suffices |
| Browser session hijacking | Low | Headless Chromium in isolated profile; session not persisted |
| Status dashboard exposed | Medium | DASHBOARD_TOKEN prevents unauthorized access |

### 8.5 `.gitignore` Essential Entries

```
# Secrets
.env
*.env

# Runtime data
data/automation_state.db
data/*.db

# Logs and screenshots
logs/
*.log
*.png

# Python
__pycache__/
*.pyc
.venv/
venv/

# OS
.DS_Store
Thumbs.db
```

### 8.6 Jira API Token — Best Practices

- Generate at: `https://id.atlassian.com/manage-profile/security/api-tokens`
- Name it clearly: `intern-automation-2025`
- Set a calendar reminder to rotate it every 90 days
- The automation agent will send a monthly reminder on the 1st of each month: "⚠️ Jira API token is 30 days old. Consider rotating it."
- If token expires: the Jira MCP server returns HTTP 401; agent catches this and sends: "❌ Jira authentication failed — please rotate your API token."

### 8.7 Human Approval Mode

When `HUMAN_APPROVAL_MODE=true` in `.env`:

**Flow:**

1. At 10:55 AM, the scheduler sends a Twilio WhatsApp message: "⏳ Morning routine about to run in 5 minutes. Reply APPROVE or CANCEL within 5 minutes."
2. A Twilio webhook listener waits for the response
3. If `APPROVE` received → proceed with morning workflow at 11:00 AM
4. If `CANCEL` received → skip today, log "Manually cancelled"
5. If no response in 5 minutes → proceed anyway (configurable: `APPROVAL_TIMEOUT_BEHAVIOR=proceed|skip`)

**Implementation Note:** The Twilio webhook handler runs as part of the FastAPI observability server on port 5050. The `/twilio-webhook` endpoint receives incoming messages and dispatches commands — APPROVE and CANCEL are handled as special commands that update an in-memory flag the scheduler checks before running the job.

### 8.8 Credential Rotation Reminder Schedule

| Secret | Rotation Frequency | Reminder Method |
|---|---|---|
| Jira API Token | Every 90 days | Monthly Twilio WhatsApp message on 1st |
| Anthropic API Key | On compromise only | N/A |
| Twilio Credentials | On compromise only | N/A |
| Timesheet Password | Per company policy | Manual |

---

## 9. Azure Student Deployment — Complete Guide

### 9.1 What Azure for Students Gives You

| Resource | Included | Cost | Relevant? |
|---|---|---|---|
| **Free credit** | **$100 USD** | Free for 12 months | ✅ Yes — covers everything |
| **B1s VM** (1 vCPU, 1 GB RAM) | **750 hours/month free** | Free for 12 months | ✅ Yes — primary choice |
| **B2s VM** (2 vCPU, 4 GB RAM) | Pay from credit | ~$30/month | Optional upgrade |
| **Azure Container Instances** | Pay per second | ~$5/month for this workload | Alternative |
| **Azure Functions** | 1M free executions | Free | ⚠️ Limited (no Playwright) |
| **Storage** (Blob + Disk) | 5 GB free | Free | ✅ Enough |
| **Bandwidth** | 15 GB free | Free | ✅ More than enough |

**Verdict:** The **B1s VM is the best choice** for this project. It runs Docker, supports Playwright Chromium in headless mode, and is completely free for 12 months.

**Azure Functions — Why Not?**
Azure Functions (serverless, timer-triggered) seems like a perfect fit for scheduled jobs. And it is — for the Jira-only parts. But Playwright (browser automation) requires a persistent environment with Chromium installed. For the simplicity goal: VM + Docker Compose is far easier.

---

### 9.2 Option A — Azure VM B1s + Docker (Primary Recommendation)

**Why B1s is Sufficient:**
- The automation makes 2 Claude API calls/day (each lasts ~15 seconds)
- SQLite reads/writes are negligible
- The FastAPI status server handles <5 requests/day
- Playwright Chromium in headless mode runs fine on 1 GB RAM
- CPU and memory are idle 99% of the day

**Complete Setup Guide:**

**Step 1: Create the VM**
1. Go to `portal.azure.com` → Create a resource → Virtual Machine
2. Image: Ubuntu Server 22.04 LTS
3. Size: B1s (1 vCPU, 1 GB RAM) — this is free
4. Authentication: SSH public key — paste your public key
5. Inbound ports: Allow SSH (22); you'll add 5050 later
6. Disk: Standard SSD, 30 GB (free tier)
7. Click Review + Create

**Step 2: Configure Network Security Group**
1. Azure Portal → Your VM → Networking
2. Add inbound rule: Port 5050, TCP, Priority 1001, Allow — for the status dashboard
3. Keep port 22 (SSH) already allowed

**Step 3: SSH into VM and Install Docker**
```bash
ssh -i your-key.pem azureuser@<public-ip>

# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker azureuser
logout
# Log back in for group change to take effect
ssh -i your-key.pem azureuser@<public-ip>

# Verify Docker works
docker --version
docker compose version
```

**Step 4: Deploy Your Application**
```bash
# On your laptop: clone your repo and push to GitHub
# On the Azure VM:
git clone https://github.com/yourusername/intern-automation.git
cd intern-automation

# Copy your .env file from laptop to VM (run this on your laptop)
scp -i your-key.pem .env azureuser@<public-ip>:~/intern-automation/.env

# Back on VM: start the application
docker compose up -d

# Verify it's running
docker compose ps
docker compose logs -f
```

**Step 5: Verify Deployment**
```bash
# Check scheduler started
docker compose logs automation | grep "Scheduler started"

# Check status dashboard
curl http://localhost:5050/health
# Should return: {"status": "healthy", ...}

# Trigger morning agent manually to test
docker compose exec automation python scripts/run_morning.py
```

**Step 6: Configure Auto-Start**
Docker Compose with `restart: unless-stopped` already handles automatic restart after container crashes or Azure VM reboots (which happen for maintenance).

---

### 9.3 Option B — Azure Container Instances (Alternative — No VM Management)

**Best for:** If you don't want to manage a VM at all.

**Cost Estimate:** The container runs 24/7 but uses minimal resources. B1s equivalent in ACI: ~$5-10/month from your $100 credit.

**Verdict:** Use VM B1s for simplicity. Use ACI only if you're determined to avoid VM management.

---

### 9.4 Option C — Azure Functions (Partial — Jira Only)

**Possible architecture:** Use Azure Functions timer triggers for the Jira-only jobs (no Playwright), and a separate VM or ACI for browser automation.

**This is overengineered for your use case.** Stick with the VM.

---

### 9.5 Azure Monitoring — Know When Your VM Is Down

**Set up an alert:**
1. Azure Portal → Your VM → Alerts → Create Alert Rule
2. Condition: `VM Availability < 1` (VM is unreachable)
3. Action: Send email to your student email

---

### 9.6 Keeping the Automation Running Long-Term on Azure

| Concern | Solution |
|---|---|
| VM reboots for Azure maintenance | `restart: unless-stopped` in Docker Compose handles this |
| Azure Student credit expires after 12 months | Migrate to free Oracle Cloud OR pay ~$4/month with standard Azure account |
| Ubuntu security updates | Run `sudo apt update && sudo apt upgrade` monthly via cron |
| Docker image outdated | Rebuild image monthly: `docker compose build && docker compose up -d` |
| Jira API token expires | Monthly Twilio reminder (see Section 8) |
| Student account deactivation | Azure notifies 30 days in advance; migrate project to new account |

---

## 10. Risks & Edge Cases

### 10.1 Updated Risk Matrix (v4.0)

| Risk | Likelihood | Impact | Detection | Mitigation |
|---|---|---|---|---|
| **Duplicate subtask creation** | Medium | High | Pre-flight JQL check + state DB | `check_subtask_exists` + `morning_done` flag |
| **Jira "In Progress" transition ID hardcoded** | High | High | Workflow breaks when Jira admin changes workflow | Always use `get_issue_transitions` dynamically |
| **Timesheet portal redesign** | High | Medium | `TimeoutError` on element selector | Multiple fallback selectors; screenshot + SMS alert |
| **Azure VM restart** | Medium | Low | Docker auto-restarts; `misfire_grace_time` catches up | `restart: unless-stopped` + 2-hour misfire grace |
| **Azure Student credit expires** | Certain (after 12 months) | Medium | Azure emails 30 days warning | Migrate to Oracle Free Tier or new account |
| **Twilio WhatsApp sandbox 72h expiry** | High (development) | Low | Messages stop delivering | Use SMS for production; or re-join sandbox |
| **Jira API token expired** | Low | High | HTTP 401 from Jira MCP; SMS alert | Monthly rotation reminder via Twilio |
| **Wrong IST timezone in worklog** | Medium | High | Worklog shows wrong time | Hardcode `+0530` offset; unit-test this |
| **Timesheet requires MFA/CAPTCHA** | Low | High | Browser stuck; screenshot shows CAPTCHA | Screenshot + SMS alert; manual action needed |
| **Subtask name has special chars from parent title** | Low | Medium | Jira API returns 400 | Sanitize parent title: strip `<>{}|` characters |
| **Notification failed — user unaware** | Low | Medium | `notification_channel="failed"` in state DB | Observability dashboard shows status independently |
| **State DB corrupted** | Very Low | High | `aiosqlite` throws exception | Daily backup to `data/backups/` |
| **Anthropic API rate limit** | Very Low | Low | 429 response | Only 2 calls/day; well within limits. Add retry on 429. |

### 10.2 Twilio-Specific Failure Scenarios

| Scenario | Detection | Response |
|---|---|---|
| Twilio API returns 400 | Message invalid (check number format) | Validate numbers include country code (`+91`) |
| Twilio API returns 401 | Wrong `Account SID` or `Auth Token` | Check `.env` values against Twilio Console |
| Twilio API returns 429 | Rate limited (>1 msg/second) | Add 1-second delay between messages |
| WhatsApp sandbox expired | Messages show `undelivered` status | Re-join sandbox OR switch to SMS |
| WhatsApp down globally | Twilio returns error | Automatic SMS fallback triggered |

### 10.3 Failure Recovery Playbook (from Twilio alerts)

| Failure | Immediate Action | Prevention |
|---|---|---|
| Morning agent didn't run | Open status dashboard → or SSH and run `python scripts/run_morning.py` | Azure VM auto-restart |
| Subtask created but wrong name | Edit name directly in Jira + update `subtask_key` via `python scripts/view_state.py --fix` | Validate name format in `setup.py` |
| Worklog not added | Go to Jira issue → Log work → 11 AM start, 8h → run `python scripts/view_state.py --fix evening_done 1` | Catch-up alert prevents missing this |
| Timesheet not synced | Login manually → sync → run `POST /mark-manual-done` on status dashboard | Screenshot alert identifies the issue |
| No notification received at 7:30 PM | Open `http://<vm-ip>:5050/status` OR send "STATUS" to Twilio number | 4-mechanism observability layer |
| Azure VM completely down | Open Azure Portal → Restart VM → Verify Docker restarts | Azure monitoring alert for VM availability |

### 10.4 Error Handling Architecture

Every tool call in the agent follows this pattern:

```
CALL TOOL
    │
    ├── SUCCESS (HTTP 200-204, valid JSON)
    │       └── Parse response → Return structured data → Continue
    │
    └── FAILURE (Network error, HTTP 4xx/5xx, JSON parse error)
            │
            ├── RETRY 1: Wait 4 seconds → Retry tool call
            │
            ├── RETRY 2: Wait 8 seconds → Retry tool call
            │
            ├── RETRY 3: Wait 16 seconds → Retry tool call
            │
            └── FINAL FAILURE
                    │
                    ├── Classify error:
                    │       ├── CRITICAL (create_subtask, add_worklog, transitions)
                    │       │       └── Stop workflow → Log → Alert → Save error to state DB
                    │       │
                    │       └── NON-CRITICAL (add_label, set_estimate)
                    │               └── Log warning → Continue remaining steps
                    │
                    └── If Browser error:
                            └── Take screenshot → Save to logs/screenshots/ → Include path in alert
```

### 10.5 Catch-Up Logic for Missed Operations

**Scenario:** Evening agent crashed halfway through. Next morning runs.

Morning agent pre-flight check:

1. Read yesterday's state from state DB
2. If `morning_done=1` AND `evening_done=0` for yesterday:
   - Send Twilio SMS: "⚠️ Yesterday's evening routine (PROJ-456) was not completed. The worklog and timesheet for [date] need manual attention."
3. If `morning_done=1` AND `timesheet_done=0` for yesterday:
   - Send Twilio SMS: "⚠️ Timesheet sync may have failed yesterday. Please verify [date] shows 8h on the portal."
4. Continue with today's morning routine regardless

### 10.6 Weekend and Holiday Skip Logic

**Weekend Detection:** `date.today().weekday() >= 5` (Saturday=5, Sunday=6)

**National Holiday Detection:** Python `holidays.India(years=today.year)` library covers Republic Day (Jan 26), Holi, Good Friday, Dr. Ambedkar Jayanti (Apr 14), Independence Day (Aug 15), Mahatma Gandhi Jayanti (Oct 2), Diwali, Christmas (Dec 25), and more (state-wise configurable).

**Company Holiday Config** (`config/holidays_config.py`):

```python
COMPANY_HOLIDAYS = {
    "2025-01-14": "Makar Sankranti (Company Holiday)",
    "2025-08-27": "Company Foundation Day",
    "2025-10-24": "Diwali (Company Holiday)",
    # Add as announced by HR
}
```

**Skip Notification:** When a day is skipped, the agent sends: "📅 Today is [Holiday/Weekend] — automation skipped. Have a good [holiday/weekend]! 🎉"

### 10.7 Complete Risk Matrix — What Can Go Wrong

| Risk | Likelihood | Impact | Detection | Mitigation Strategy |
|---|---|---|---|---|
| **Duplicate subtask creation** | Medium | High | `check_subtask_exists` pre-flight | Double-check via JQL + state DB idempotency key |
| **Jira parent story changed** | Medium | High | Agent fails to find expected issue | Hardcode `JIRA_PARENT_KEY` in `.env`; weekly health check message |
| **"In Progress" transition ID wrong** | High | High | Tool returns error on transition | Always call `get_issue_transitions` dynamically; never hardcode ID |
| **Timesheet portal UI redesigned** | High | Medium | Browser MCP throws `TimeoutError` | Screenshot on failure; parameterize all selectors in config; alert for manual action |
| **Wrong IST timezone on worklog** | Medium | High | Worklog appears at wrong time | Always use explicit `+0530` in `started` field |
| **Timesheet CAPTCHA appears** | Low | High | Browser MCP stuck on CAPTCHA page | Screenshot + human intervention alert; `HUMAN_APPROVAL_MODE` bypass |
| **Jira project-level timetracking disabled** | Low | Medium | `set_time_estimate` returns 404/400 | Catch error, log warning, continue workflow (non-critical step) |
| **Subtask issuetype not enabled** | Low | High | `create_subtask` returns 400 | Pre-validate in `scripts/setup.py` during first-time setup |
| **Evening crash — worklog missed** | Low | High | `evening_done=0` in next morning's catch-up check | Morning catch-up check sends alert; manual action required |
| **Wrong day number (holidays miscounted)** | Low | Medium | Subtask named "day_32" but actually day_31 | Unit test day counter; visual verification in first week |
| **Company Jira has custom fields** | Medium | Medium | Subtask missing required fields | Inspect your Jira project's issue creation form in DevTools |
| **Parent story title has special characters** | Low | Medium | Subtask name invalid | Sanitize title: strip commas, slashes, quotes before using in name |

---

## 11. Phase-wise Build Roadmap — Detailed, No Code

### Phase 0 — Reconnaissance (Before Writing Any Code)
**Duration:** 2–3 hours total (one-time)
**Goal:** Gather all project-specific data that cannot be discovered by code alone.

This phase is non-negotiable. Without this data, your automation will either fail silently or create subtasks with wrong names.

#### Jira Reconnaissance (1 hour)

Open your Jira in Chrome. Open DevTools → Network tab. Filter by XHR/Fetch.

**Data to collect:**

1. **Your `accountId`:** Visit `https://yourcompany.atlassian.net/rest/api/3/myself` in the browser while logged in. Copy the `accountId` field — it looks like `5f7a8b9c0123456789abcdef`.

2. **Parent story `issue_key` and `project_key`:** Open your parent story in Jira. The URL contains the issue key (e.g., `PROJ-100`). The first 4 characters before the dash are the project key (`PROJ`).

3. **Parent story exact summary/title:** Copy the full title text exactly. This becomes the third segment of your subtask name. Note any special characters.

4. **Subtask issuetype name:** Go to your parent story → Create subtask. In DevTools Network, watch for a POST to `/rest/api/3/issue`. In the request payload, find `"issuetype"`. The name might be `"Subtask"` or `"Sub-task"` or `"Child Issue"` — copy the exact string from the actual API call.

5. **Available workflow transitions:** Create a test subtask manually. Watch the Network tab as you move it from "To Do" → "In Progress". Find the POST to `/rest/api/3/issue/{key}/transitions`. Note the `transition_id` for "In Progress". Then find "Done" transition ID. Write these down even though the code discovers them dynamically — knowing them helps debug.

6. **Label format:** Add your personal label to a test issue. Note the exact label string format (lowercase? hyphenated? camelCase?). This goes in `MY_JIRA_LABEL` in `.env`.

7. **Timetracking format:** In the Network tab, check if setting `originalEstimate` uses seconds (`"28800s"`) or the `"8h"` string format. Your Jira instance may accept either, but confirm which one works.

**Write all this into `.env` and `config/holidays_config.py` before any code.**

#### Timesheet Portal Reconnaissance (1–2 hours)

This is the most important reconnaissance step because browser automation is entirely selector-dependent.

1. Open your timesheet portal in Chrome (not incognito — use your normal session)
2. Open DevTools → Elements tab
3. **Login form:** right-click the username input → Inspect → copy: `id`, `name`, `type`, `placeholder`. Same for password and submit button.
4. **Sync button:** right-click the "Sync from Jira" or "Import" button → Inspect. In Network tab: click the button and watch what HTTP request fires. If it's a direct API call, you may be able to skip browser automation for this step.
5. **Hours confirmation area:** Find today's date row in the timesheet table → right-click → Inspect. Note how 8h is displayed: `"8h"`, `"8:00"`, `"08:00"`, `"480"`, `"8.0h"`.
6. **Session persistence:** Try closing the browser and reopening. Does the portal require you to log in again?

**Create `config/timesheet_selectors.py`** with all selectors as named constants.

#### Company Holidays (15 minutes)

Ask HR or check your offer letter / company intranet for the official holiday list for this year. Add all dates to `config/holidays_config.py`. The Python `holidays` library covers national holidays, but company-specific days off must be added manually.

---

### Phase 1 — Foundation: Jira MCP + State MCP + Setup
**Duration:** 3–5 days
**Goal:** Build the core infrastructure. Validate Jira automation works end-to-end when triggered manually.

#### Day 1–2: Project Infrastructure

**Repository Setup:**
- Create private GitHub repository: `intern-automation`
- Initialize with the complete folder structure from Section 7
- Create `.gitignore` as the very first commit (before adding any code)
- Create `.env.example` with all keys and empty values — commit this
- Create `requirements.txt` with all dependencies — commit this
- Set up Python virtual environment locally

**First-time Setup Wizard (`scripts/setup.py`):**

Design this script to be the single entry point for anyone setting up the project. It should:
1. Verify Python version is 3.11+
2. Check all required `.env` keys are present and non-empty
3. Create the SQLite database and both tables if they don't exist
4. Prompt interactively for `start_date` if not set (with validation)
5. Write `parent_jira_key`, `my_label`, `my_username_prefix` to config table
6. Make a test call to Jira `/rest/api/3/myself` — print the display name on success
7. Send a test WhatsApp message via Twilio — print "Delivered" on success
8. Print a summary checklist with ✅/❌ for each component
9. Print the next steps to follow

**Success condition:** `python scripts/setup.py` completes with all green checkmarks.

#### Day 3: Jira MCP Server

Build `mcp_servers/jira_mcp/server.py` tool by tool. After each tool, test it in isolation via `python scripts/test_jira.py --tool <name>`. Follow this exact build order:

1. `get_my_account_id` → Verify it returns your correct `accountId` and display name
2. `get_parent_story` → Verify it returns the correct story summary and project key
3. `check_subtask_exists` → Create a test subtask manually → verify the tool finds it → delete it → verify tool returns `exists: false`
4. `create_subtask` → Create a test subtask via the tool → verify it appears in Jira with the correct name → delete it after verification
5. `add_label` → Call on a test issue → verify label appears in Jira
6. `set_time_estimate` → Call on test issue → verify 8h estimate appears
7. `assign_issue` → Call on test issue → verify assigned to you
8. `get_issue_transitions` → Print all transitions → confirm "In Progress" and "Done" names match your Jira workflow
9. `transition_issue` → Move test issue to "In Progress" → verify in Jira
10. `add_worklog` → Add worklog to test issue → verify it shows 8h starting at 11 AM IST

**Critical validation:** The worklog timestamp. Open Jira → test issue → worklog entry. Does it show 11:00 AM? If it shows 5:30 AM or UTC time, the timezone offset in your `started` field is wrong. Fix it before proceeding.

**Clean up:** Delete all test subtasks created during testing. Do not leave noise in Jira.

#### Day 4: State MCP Server

Build `mcp_servers/state_mcp/server.py` with all 6 tools. Test via `python scripts/test_state.py`:

1. `get_today_state` on fresh DB → verify returns `{ "exists": false }`
2. `set_today_state` with `morning_done=1` → call `get_today_state` → verify returns 1
3. `set_today_state` again with `subtask_key="PROJ-TEST"` → verify upsert works (both fields present)
4. `get_day_number` with your actual `start_date` → verify it equals the day you're on
5. Get day number for a weekend: Saturday + Sunday should not be counted
6. Get day number across a known national holiday: that day should not be counted
7. `log_error` → call twice → verify both messages appear in `error_log` separated by newlines
8. `get_historical_state` for a past date → verify returns correct data

Build `scripts/view_state.py` and verify it prints a clean, readable state summary.

#### Day 5: Full Manual End-to-End Test

Run the complete morning workflow manually using the tools directly (no agent yet). Then run the evening portion. Verify in Jira: the subtask exists, has correct name, label, 8h estimate, assigned to you, status "Done", and worklog shows 8h at 11:00 AM IST.

**Deliverable:** Everything works manually. The subtask name format is correct. The worklog timestamp is correct.

---

### Phase 2 — Twilio Notifications + Agent Brain + Scheduler
**Duration:** 4–5 days
**Goal:** Full automated morning + evening pipeline on schedule with Twilio notifications.

#### Day 1: Twilio Notification MCP Server

1. Verify Twilio account setup: Account SID, Auth Token, from/to numbers in `.env`
2. For WhatsApp sandbox: follow Twilio's sandbox join instructions
3. Build `mcp_servers/notification_mcp/server.py` with `send_whatsapp`, `send_sms`, `send_alert`
4. Build `notifications/twilio_client.py` (direct client, no MCP — used by notification job)
5. Build `notifications/message_builder.py` with all 16 state combination handlers
6. Test: `python scripts/test_notify.py` → verify WhatsApp message received on your phone
7. Test failure format → verify failure message received
8. Test SMS fallback: temporarily set wrong WhatsApp number → verify SMS is sent instead

Write `tests/test_message_builder.py` and verify all 16 states produce the correct messages.

#### Day 2: Claude Agent Prompts

Build `agent/prompts.py` — this is the most critical engineering work in the project.

**`MORNING_SYSTEM_PROMPT` design principles:**
- Numbered steps matching the exact 16-step morning workflow from Section 4.1
- Explicit: "After step N succeeds, extract {field} and use it in step N+1"
- Explicit: "If step N fails after 3 retries, call `state__log_error`, call `notification__send_alert`, and STOP"
- Explicit: "If `check_subtask_exists` returns `exists: true`, save the key via `state__set_today_state`, then skip to step 15"
- Explicit: "The subtask name format is EXACTLY: `{MY_USERNAME_PREFIX} - day_{day_number} - {parent_story_summary}`"
- Explicit: "The worklog `started` field must be in ISO 8601 format with explicit `+0530` offset for IST"

#### Day 3: Agent Client + Morning/Evening Agents

Build `agent/client.py` with the MCP session manager pattern — spawns all 4 servers, combines tool lists with `{server}__` prefix, exposes `call_tool()`.

Build `agent/morning_agent.py` with the agentic loop: Guard check first → Open MCP client context → Agentic loop with 30-iteration safety limit → Handle `stop_reason: end_turn` and `stop_reason: tool_use` correctly.

Build `agent/evening_agent.py` same pattern.

**Test:** `python scripts/run_morning.py` on a weekday → full morning workflow via Claude agent → verify in Jira.

#### Day 4: Scheduler + Guards

Build `scheduler/guards.py` and test every case: Saturday → skip, Sunday → skip, a known national holiday → skip, a date in `COMPANY_HOLIDAYS` → skip, `is_leave_day=1` in state DB → skip, normal Monday → proceed.

Build `scheduler/jobs.py` and `scheduler/main_scheduler.py` with APScheduler configured for IST, three jobs, and `coalesce=True`.

**First live test:** Run `python -m scheduler.main_scheduler` and wait for 11 AM on a real working day. Verify morning job fires, subtask created, WhatsApp received, evening job fires at 7 PM, and 7:30 PM summary arrives.

**Idempotency test:** Run `python scripts/run_morning.py` twice on the same day. Verify the second run detects the existing subtask and exits without creating a duplicate.

**Deliverable:** Full Jira automation running on schedule. WhatsApp/SMS notifications delivered. No manual action required.

---

### Phase 3 — Browser Automation for Timesheet
**Duration:** 5–7 days
**Goal:** Automate the company timesheet portal sync as part of the evening workflow.

#### Day 1–2: Portal Investigation and Selector Mapping

Return to your timesheet reconnaissance data from Phase 0.

Build `config/timesheet_selectors.py` with the exact selectors you documented, providing 2–3 alternatives for each. Playwright tries them in order. This is your resilience layer against minor UI changes.

#### Day 3–4: Build Browser MCP Server (Headed Mode)

Build `mcp_servers/browser_mcp/server.py` with Playwright in **headed mode** (visible browser window). This is essential during development — you can see exactly what Playwright is doing.

For each tool, develop in this order:
1. `login_timesheet`: Navigate → fill → submit → verify URL changed
2. `get_page_content`: Read body text → verify page content makes sense
3. `take_screenshot`: Take screenshot → verify file saved to `logs/screenshots/`
4. `sync_jira_logs`: Find sync button → click → wait for load → verify page changes
5. `confirm_hours`: Read hours cell → verify "8h" or equivalent appears

Test each tool: `python scripts/test_browser.py --tool login_timesheet`

Common issues to debug in headed mode: Login button not found (check if portal uses iframes); sync button not found after login (check if page uses client-side routing); hours not showing (check if you need to navigate to a specific date view first); CAPTCHA appears (note this and document it as a known failure mode).

#### Day 5–6: Integration + Headless Testing

Switch to `headless=True` and re-test all browser tools. Headless mode behaves slightly differently. Fix any headless-specific issues by adding `viewport={"width": 1920, "height": 1080}` to browser context.

Integrate browser tools into `EVENING_SYSTEM_PROMPT` and `agent/evening_agent.py`.

Run complete evening workflow: `python scripts/run_evening.py`. Verify end-to-end: Jira Done → worklog → browser login → sync → confirm 8h.

**Test failure handling:** Temporarily break a selector. Verify: screenshot is saved, SMS alert is sent, state DB shows `timesheet_done=0`, but `evening_done=1` is intact (Jira portion was not affected).

**Deliverable:** Complete hands-free automation. Morning creates. Evening closes. Timesheet syncs. WhatsApp confirms. You did nothing.

---

### Phase 4 — Observability Layer + Hardening + Azure Deploy
**Duration:** 5–7 days
**Goal:** Production-ready system with full observability, unit tests, and Azure deployment.

#### Day 1–2: Observability HTTP Server

Build `observability/status_server.py` using FastAPI.

Design the HTML status dashboard template — readable on mobile browser, auto-refreshes every 60 seconds, shows today's status (all 4 flags), last 7 days history table, any error logs. Color coding: green (done), red (failed), yellow (pending), gray (skipped).

Implement all routes: `GET /status`, `GET /status/json`, `GET /history?days=7`, `GET /health`, `POST /mark-manual-done`, `POST /twilio-webhook`.

Run the status server alongside APScheduler in the same process — APScheduler runs in one async task, FastAPI (via uvicorn) runs in the same event loop.

Test: Open `http://localhost:5050/status` in your browser. Verify the dashboard loads and shows today's actual state.

#### Day 3: Twilio Two-Way Commands

Implement the Twilio webhook handler for incoming messages. For local testing, use `ngrok` to expose port 5050 publicly and set the Twilio webhook URL to the ngrok HTTPS URL temporarily.

Test each command: Send "STATUS" from your phone → verify reply arrives within 5 seconds. Send "LEAVE" → verify today marked as leave day in state DB.

#### Day 4: Hardening

**Catch-up logic:** In `scheduler/jobs.py`, before running morning job, check yesterday's state. If `morning_done=1` and `evening_done=0` → send SMS alert about missed evening.

**State DB backup:** At the start of each morning job, copy `automation_state.db` to `data/backups/automation_state_YYYYMMDD.db`. Keep 30 days. Auto-delete older ones.

**Log rotation:** Configure loguru with `rotation="midnight"`, `retention="30 days"`, `compression="zip"`.

**Monthly reminders:** Add APScheduler job on 1st of each month at 9 AM sending Jira API token age warning and internship progress note.

#### Day 5: Unit Tests

Write and run all tests in `tests/`:

`test_guards.py`: Assert Saturday → skip, Republic Day → skip, company holiday → skip, normal Monday → proceed, `is_leave_day=1` → skip.

`test_day_counter.py`: Assert contiguous 5 weekdays = day 5, 5 weekdays with a public holiday = day 4, start_date = today → day 1.

`test_name_formatter.py`: Assert correct format: `ravi_zapadiya - day_4 - RAG, Chatbots, Agentic AI`. Assert special chars in title handled.

`test_message_builder.py`: Test all 16 combinations of `{morning_done, evening_done, timesheet_done, notification_done}`. Assert morning_done=0 → message contains "❌". Assert all done → message contains "🎉".

**Target:** All tests pass. `python -m pytest tests/ -v` → all green.

#### Day 6–7: Azure Deployment

Follow the Azure B1s deployment guide from Section 9.2 step by step. One-week validation: Leave the Azure-deployed system running for one full working week. Verify 5 consecutive working days of fully automated operation.

**Deliverable:** Production system deployed on Azure. Observable via HTTP dashboard. Controllable via WhatsApp commands. Tested with 5 consecutive automated working days.

---

### Phase 5 — Long-term Reliability (Month 2+)

**Weekly Health Check (Every Monday 9 AM):**
Send WhatsApp with: internship day number, parent story title, last week's success rate. Format: "📊 Week N starting! Day X of internship. Last week: 5/5 days automated. Parent story: {title}."

**Auto-Detect Parent Story Change:**
If `get_parent_story` returns a different story than `JIRA_PARENT_KEY`, send alert to verify configuration.

**Leave Management via WhatsApp:**
"LEAVE" → mark today. "LEAVE 2025-02-14" → mark a future date. "LEAVE LIST" → show all marked leave days this month.

**Telegram Bot Commands (Interactive Control):** See Section 12 — these are the same commands listed for Twilio two-way control.

**SQLite Run History Dashboard Enhancement:**
Add a sparkline chart (SVG-based) showing 30-day automation success rate. Add "streak counter": consecutive successful days.

**Azure Cost Check (Monthly):**
Add a monthly reminder job: "💰 Azure monthly check: Visit portal.azure.com → Cost Management to verify VM costs are within expected range."

---

## 12. Final Verdict

### 12.1 What Changed from v2.0 and Why It Matters

| Change | v2.0 | v3.0/v4.0 | Impact |
|---|---|---|---|
| **Cloud** | Oracle Free Tier / generic VPS | Azure Student B1s | Free for 12 months, Azure Portal familiarity, student support |
| **Notifications** | Telegram Bot | Twilio WhatsApp + SMS | Works on your primary phone number; no app switching; delivery receipts; SMS fallback |
| **7:30 PM Job** | Mentioned as "skips Claude, reason not explained" | Full 7-reason architectural justification | Understand the Intelligence Boundary — the most reusable principle in AI engineering |
| **Observability** | Not present | Full 4-mechanism layer | Know status anytime, independent of notifications |
| **Two-way control** | Telegram bot commands | WhatsApp/SMS reply commands | Same channel as notifications; simpler setup |
| **Dashboard** | Not present | FastAPI status server (port 5050) | Open on phone browser; no app needed |

---

### 12.2 The Intelligence Boundary — The One Principle to Remember

From this entire project, the most transferable lesson is this:

> **Use Claude (or any LLM) when output cannot be mechanically derived from input. Use Python when it can.**

Apply this to every future automation project. The skill of correctly placing the intelligence boundary is what separates engineers who build reliable AI systems from those who build expensive, fragile ones.

Morning agent → needs Claude (reason about which transition to pick, handle unexpected Jira states, decide if an error is fatal or not)

7:30 PM notification → does not need Claude (read 4 boolean flags → format string → send message)

This distinction saves cost, reduces failure surface, and makes the deterministic parts 100% predictable.

---

### 12.3 Honest Reliability Assessment

| Component | Expected Reliability | Weak Point |
|---|---|---|
| Jira operations | 99.9% | Jira itself going down (rare) or API token expiring |
| Twilio notifications | 99.5% | WhatsApp platform issues → SMS fallback covers this |
| Timesheet browser | 90–95% | Portal UI changes; CAPTCHA; session issues |
| Azure VM uptime | 99.5% | Planned maintenance → Docker auto-restart |
| Overall system | ~89–94% per day | Timesheet portal is the weakest link |

**Mitigation for the weak link:** The Jira portion (creating subtask, logging 8h worklog) is decoupled from the timesheet browser portion. Even if timesheet sync fails, your Jira work is recorded correctly. Timesheet failure → manual sync takes 30 seconds → status dashboard has a "Mark as Manual Done" button to update state.

---

### 12.4 Cost Summary for 6-Month Internship

| Item | Monthly | 6-Month Total |
|---|---|---|
| Azure B1s VM | **Free** (12-month free tier) | $0.00 |
| Anthropic API (~$0.006/day × 22 days) | ~$0.13 | ~$0.79 |
| Twilio WhatsApp (~$0.005/msg × 44 msgs/month) | ~$0.22 | ~$1.32 |
| Twilio SMS (fallback only, rare) | ~$0.02 | ~$0.12 |
| **Total** | **~$0.37/month** | **~$2.23 total** |

**ROI:** ~13 minutes/day × 22 days × 6 months = **28.6 hours of manual work eliminated** for $2.23 total. That is $0.078 per hour of work saved.

---

### 12.5 The Three Actions to Take Today

1. **Run Phase 0 reconnaissance right now** (30 minutes). Open Jira in Chrome, open DevTools, collect all the data listed. Write it in a notes file. This is the most valuable 30 minutes of the entire project.

2. **Set up the Azure Student VM today** (45 minutes). The VM takes ~10 minutes to provision. Install Docker while reading Phase 1.

3. **Build `scripts/setup.py` first** (1 hour). A working setup script proves your environment is correct, your credentials are valid, and Twilio messages actually reach your phone — before you write a single line of automation logic.

Phase 1 subtask + worklog automation can be working by end of week. The timesheet browser is the hardest part — plan 2 weeks for Phase 3. Everything else is plumbing.

---

### 12.6 What Makes This Architecture Genuinely Production-Grade

This is not a "quick script with a cron job." It is a proper autonomous agent system. Here is what makes it real:

| Quality Attribute | How It's Achieved |
|---|---|
| **Idempotent** | `check_subtask_exists` + `morning_done` flag in state DB. Safe to run 10 times — creates subtask exactly once |
| **Reliable** | `tenacity` exponential backoff retry on every tool call. Critical steps get 3 retries; Jira is rarely down |
| **Observable** | `loguru` rotating logs + SQLite state history + Twilio notifications with full error context + HTTP dashboard |
| **Secure** | `.env`-based secrets never committed; API tokens not passwords; no hardcoded credentials anywhere in code |
| **Maintainable** | Clean folder structure; one file per responsibility; prompts centralized in one file; selectors in config |
| **Self-healing** | Catch-up alerts for missed operations; screenshot on browser failure; error logged to DB for post-mortem |
| **Timezone-correct** | `Asia/Kolkata` in APScheduler; explicit `+0530` offset in Jira worklog `started` field |
| **Holiday-aware** | Python `holidays` library for national days + custom company holidays dict |
| **Non-duplicating** | Double protection: Jira JQL check AND state DB idempotency flag |
| **Portable** | Runs on laptop, Azure, Docker — zero code changes between environments |
| **Testable** | Unit tests for guards, day counter, name formatter, message builder (16 states); integration tests for state DB |
| **Scalable** | Each MCP server is independent — add new capabilities without touching other servers |

---

### 12.7 Recommended Build Order — Day-by-Day Summary

```
Day 1:  Set up repo + .env + install dependencies + run setup wizard
Day 2:  Build + test Jira MCP server (tools 1–5)
Day 3:  Build + test Jira MCP server (tools 6–10)
Day 4:  Build + test State MCP server
Day 5:  Build + test Notification (Twilio) MCP server
Day 6:  Build agent client + write system prompts
Day 7:  Build morning agent + run first fully automated morning
Day 8:  Build evening agent + run first fully automated evening
Day 9:  Build scheduler + guards → live on schedule for 3 days
Day 10: Timesheet portal reconnaissance → document selectors
Day 11: Build browser MCP server (headed mode testing)
Day 12: Build browser MCP server (headless testing) + integrate into evening agent
Day 13: Full end-to-end test (all three jobs automated)
Day 14: Write unit tests + add catch-up logic + Docker build
Month 2: Telegram bot commands, weekly health check, leave management
```

---

### 12.8 Final Recommendation

**Start with Phase 0 reconnaissance today.** Don't wait until you have the "perfect" architecture. The Jira MCP server alone (Phase 1) eliminates 70% of your daily manual work and runs in 10 seconds. Everything else is incremental improvement on top of that foundation.

The architecture is intentionally lean. No Kubernetes, no Redis, no message queues, no microservices. Just Python processes, a SQLite file, four clean MCP servers, and a Twilio number. That's all a personal automation project needs to run reliably for the duration of your internship and beyond.

**Build it. Ship Phase 1 this week. The rest follows.**

---

## 13. Alternative Deployment Options — Laptop & Windows

> This section restores the local and Windows deployment options from the Complete Plan (v2). These are useful if you want to start testing locally before moving to Azure, or if you're on Windows without Docker.

---

### 13.1 Option A — Local Laptop (Start Here, Day 1)

**Best for:** Initial testing and validation of the full pipeline.

**Limitations:**
- Laptop must be ON and awake at 11:00 AM and 7:00 PM
- If laptop is closed/sleeping, jobs are missed
- `misfire_grace_time` helps if you open the laptop within 2 hours

**Setup Steps:**

1. Clone the repository to your local machine
2. Create a virtual environment: `python -m venv .venv`
3. Activate: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Install Playwright browsers: `playwright install chromium`
6. Copy `.env.example` → `.env` and fill in all values
7. Run the setup wizard: `python scripts/setup.py`
   - Validates all environment variables
   - Creates SQLite database and tables
   - Prompts for `start_date` if not set
   - Tests Jira connectivity (calls `/rest/api/3/myself`)
   - Tests Twilio notification (sends a test WhatsApp message)
8. Run individual tests: `python scripts/test_jira.py`
9. Run the scheduler: `python -m scheduler.main_scheduler`
10. Keep the terminal open (or use `nohup` / `screen` / `tmux`)

**Keeping it Running on Laptop:**

On Linux/Mac:
```
nohup python -m scheduler.main_scheduler > logs/scheduler_stdout.log 2>&1 &
```

On Windows: Use Windows Task Scheduler to run `python -m scheduler.main_scheduler` at startup.

---

### 13.2 Option B — Docker on Laptop (Recommended for Laptop Deploy)

**Best for:** Clean environment, easy restart, no virtual env management.

**Advantages over bare Python:**
- Isolated environment — no Python version conflicts
- `restart: unless-stopped` — auto-restarts after crashes
- Chromium included in container

**Docker Compose Structure:**

```yaml
# docker-compose.yml (conceptual — not runnable without actual code)
services:
  automation:
    build: .                          # Dockerfile in project root
    container_name: intern_automation
    restart: unless-stopped           # Auto-restart on crash
    env_file: .env                    # Load all secrets from .env
    volumes:
      - ./data:/app/data              # Persist SQLite DB
      - ./logs:/app/logs              # Persist logs and screenshots
    environment:
      - TZ=Asia/Kolkata               # Critical: IST timezone in container
```

**Dockerfile Layers:**

1. Base: `python:3.11-slim`
2. Install system deps for Playwright (Chromium requires ~15 system libraries)
3. Copy `requirements.txt` → `pip install`
4. Run `playwright install chromium --with-deps`
5. Copy application code
6. Create `data/` and `logs/screenshots/` directories
7. `CMD: python -m scheduler.main_scheduler`

**Daily Commands:**

```bash
docker compose up -d          # Start in background
docker compose logs -f        # Watch live logs
docker compose down           # Stop
docker compose restart        # Restart after code changes
```

---

### 13.3 Option C — Windows Task Scheduler (No Docker, No VPS)

**Best for:** Windows laptop users who don't want Docker.

Create three scheduled tasks in Windows Task Scheduler:
- Task 1: `python scripts/run_morning.py` at 11:00 AM, Mon–Fri
- Task 2: `python scripts/run_evening.py` at 7:00 PM, Mon–Fri
- Task 3: `python scripts/run_notify.py` at 7:30 PM, Mon–Fri

**Settings for each task:**
- Run whether user is logged on or not
- Run with highest privileges
- Configure for: Windows 10/11
- Stop task if it runs longer than: 1 hour
- Set working directory to the project folder

---

### 13.4 Deployment Comparison Matrix — All Options

| Factor | Laptop (bare) | Docker on Laptop | Azure VM B1s + Docker | Windows Task Scheduler |
|---|---|---|---|---|
| **Reliability** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Setup Complexity** | Low | Medium | Medium-High | Low |
| **Runs 24/7** | ❌ (laptop must be on) | ❌ | ✅ | ❌ |
| **Cost** | Free | Free | Free (12 months) | Free |
| **Observability Dashboard** | ❌ | Localhost only | ✅ Public IP | ❌ |
| **Recommended For** | Testing only | Phase 1-2 | Phase 3+ Production | Windows users |

**Recommended path:** Start on local laptop for Phase 0–1 testing → move to Azure VM B1s for Phase 2+ production running.

---

> *"Know when to use the chainsaw and when to use the bread knife. That is engineering."*

---

*Architecture: Python 3.11+ · MCP SDK 1.x · Claude Sonnet 4 · Playwright · APScheduler · SQLite · FastAPI · Twilio · Azure Student B1s*
*Designed for: Personal productivity · Single-user · IST timezone · Atlassian Jira Cloud · 6-month internship horizon*
*Version: 4.0 — Complete: v3 Refined + All Deep Technical Content from Complete Plan Restored*
