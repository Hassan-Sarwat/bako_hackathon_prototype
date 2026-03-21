# PROJECT CONTEXT — Bako Bakery Voice Assistant

> Single source of truth for AI assistant context. Load this file at the start of any session to avoid re-reading all backend/frontend code.
> Update this file when major architectural or logic changes occur.

---

## [PROJECT OVERVIEW]

A voice-powered AI assistant for bakery staff to handle daily operations:
- Inventory logging
- Sanitation checklist tracking
- Cleaning task logging
- Issue/ticket raising for the office

Built for the Bako Hackathon. The backend is complete; the UI dashboard is the active development area.

**Git branch for UI work:** `UI`

---

## [TECH STACK]

| Layer | Technology | Version |
|---|---|---|
| Backend language | Python | 3.13 |
| Backend framework | FastAPI | latest |
| Backend package manager | uv | latest |
| Voice AI | Gemini Live API | gemini-2.5-flash-preview-native-audio-dialog |
| Database | SQLite | (via sqlite3) |
| Frontend framework | React | 19.2.4 |
| Frontend build tool | Vite | 8.0.1 |
| Frontend CSS | Native CSS (no library) | — |

---

## [PROJECT FILE STRUCTURE]

```
bako_hackathon_prototype/
├── AGENTS.md               ← project overview + what's done/next
├── API_SCHEMA.yaml         ← OpenAPI 3.1.0 full endpoint + schema spec
├── src/                    ← Python backend
│   ├── main.py             ← FastAPI app, all REST endpoints, CORS, lifespan
│   ├── config.py           ← DB path, audio config, Gemini model name, system prompt
│   ├── db.py               ← SQLite schema, seed data, all CRUD helpers
│   ├── tools.py            ← 12 Gemini function declarations (voice mode)
│   ├── tool_handlers.py    ← dispatcher: Gemini calls → DB ops + audit logging
│   └── __main__.py         ← enables `uv run -m src`
├── FRONTEND/               ← React dashboard UI
│   ├── src/                ← all UI source code
│   │   ├── main.jsx        ← entry point (DO NOT MODIFY)
│   │   ├── index.css       ← CSS vars; --bk-* vars appended at bottom (extend, never overwrite)
│   │   ├── App.jsx         ← root shell: header + clock + TabNav + tab router
│   │   ├── App.css         ← dashboard layout
│   │   ├── data/
│   │   │   └── mockData.js ← all mock data (single source of truth for UI)
│   │   ├── components/
│   │   │   ├── TabNav/     ← horizontal tab bar (4 tabs)
│   │   │   ├── ProgressBar/← reusable progress bar: {completed, total, label}
│   │   │   ├── UrgencyBadge/← urgency pill: urgent/high/normal/low
│   │   │   ├── CategoryTag/ ← ticket category label
│   │   │   └── ChecklistRow/← shared checkbox row (Cleaning + HACCP)
│   │   └── tabs/
│   │       ├── TicketsTab/ ← issue cards grid
│   │       ├── InventoryTab/← ingredient count table
│   │       ├── CleaningTab/ ← sanitation + cleaning checklists
│   │       └── HaccpTab/   ← HACCP food-safety compliance groups
│   ├── EXTRAS/
│   │   └── PROJECT_CONTEXT.md ← THIS FILE
│   ├── package.json
│   └── vite.config.js
├── bakery.db               ← SQLite DB (auto-created)
├── pyproject.toml          ← Python dependencies
└── .env                    ← GEMINI_API_KEY (not committed)
```

---

## [BACKEND CONTEXT]

### REST API (FastAPI, port 8000)

All endpoints prefixed `/api/`. CORS is permissive (all origins) for development.

#### Checklists (sanitation | inventory)
```
GET  /api/checklists/{type}/items        → all items with completion state
GET  /api/checklists/{type}/remaining    → incomplete items only
GET  /api/checklists/{type}/summary      → {completed, total, remaining}
POST /api/checklists/items/{id}/complete   body: {staff_id, notes?}
POST /api/checklists/items/{id}/incomplete body: {staff_id}
```

#### Inventory Log
```
GET  /api/inventory          → log entries (limit 50)
POST /api/inventory          body: {item_name, count, staff_id}
```

#### Cleaning Tasks (auto-created each day)
```
GET  /api/cleaning/tasks               → today's tasks
GET  /api/cleaning/remaining           → incomplete tasks
GET  /api/cleaning/summary             → {date, completed, total, remaining, all_done}
POST /api/cleaning/tasks/{id}/complete   body: {staff_id, notes?}
POST /api/cleaning/tasks/{id}/incomplete body: {staff_id}
```

#### Tickets
```
GET  /api/tickets   → open tickets sorted: urgent → high → normal → low
POST /api/tickets   body: {title, description, category, urgency, staff_id}
  categories: machine_breakdown | no_show | stock_shortage | safety | other
  urgency:    urgent | high | normal | low
```

#### Dashboard (aggregate)
```
GET /api/dashboard  → {sanitation, inventory, cleaning, tickets} in one call
```

#### Audit + Admin
```
GET  /api/audit?limit=50&staff_id=x
POST /api/admin/reset-checklists
GET  /api/health
```

### Database Schema

**checklist_items:** id, checklist_type (sanitation|inventory), item_name, is_complete(0/1), completed_at, completed_by, notes

**inventory_log:** id, item_name, count, logged_by, logged_at

**cleaning_tasks:** id, task_date, area, action, is_complete, completed_at, completed_by, notes

**tickets:** id, title, description, category, urgency, status (open|closed), raised_by, created_at, resolved_at

**audit_log:** id, staff_id, user_message, ai_model, ai_response, tool_name, tool_args, tool_result, created_at

### Seed Data (hard-coded in db.py)

**Sanitation (8 items):** Sanitize prep surfaces, Clean oven interiors, Wash mixing bowls and utensils, Mop bakery floor, Clean display cases, Sanitize sink and drain, Empty trash bins, Wipe down equipment handles

**Inventory (8 items):** All-purpose flour, Sugar, Butter, Eggs, Yeast, Vanilla extract, Chocolate chips, Baking powder

**Cleaning task areas (10):** Prep surfaces, Ovens, Mixing equipment, Floor, Display cases, Sinks and drains, Trash and recycling, Equipment handles, Storage areas, Restrooms

### Authentication
All write ops require `staff_id`. Hackathon: `--staff-id` CLI flag. Production plan: NFC card reader.

### Voice Mode (separate from REST API)
Gemini Live API with 12 function-callable tools for real-time voice interaction. Not relevant to the UI dashboard. Tools: mark_item_complete/incomplete, get_remaining_items, add_inventory_count, get_cleaning_tasks, get_incomplete_cleaning_tasks, mark_cleaning_complete/incomplete, get_cleaning_summary, get_checklist_summary, raise_ticket, get_open_tickets.

---

## [FRONTEND CONTEXT]

### Dashboard Tabs

| Tab ID | Label | Content |
|---|---|---|
| `tickets` | Tickets | Issue cards: urgency badge, category tag, title, description, assignee (raised_by), timestamp |
| `inventory` | Inventory | Ingredient table: name, count (color-coded), status, logged_by, time |
| `cleaning` | Cleaning | Sanitation checklist (8) + daily cleaning tasks (10), each with progress bar |
| `haccp` | HACCP | 7 food-safety category groups, 21 checks, overall compliance % |

### State Management
- `App.jsx`: `useState('tickets')` for active tab; `useEffect` 1s interval for live clock
- `CleaningTab`: `useState` copy of sanitation + cleaning data; local toggle only
- `HaccpTab`: `useState` copy of HACCP groups; local toggle only
- All toggle handlers have `// TODO: POST /api/...` stubs — replace with fetch calls

### CSS Variable System
Existing vars (never touch): `--text, --text-h, --bg, --border, --accent, --accent-bg, --accent-border, --shadow, --code-bg`

Bakery extensions appended to index.css (all `--bk-*` prefixed):
- Urgency: `--bk-{urgent|high|normal|low}-{bg|text|border}`
- Category: `--bk-cat-{machine|noshow|stock|safety|other}-{bg|text}`
- Stock: `--bk-stock-{ok|low|critical}` + `-bg` variants
- Progress bar: `--bk-progress-{track|fill|complete}`
- Header: `--bk-header-bg: #1a1015`, `--bk-header-text: #f5f0ff`
- Dark mode variants in `@media (prefers-color-scheme: dark)`

### Mock Data (FRONTEND/src/data/mockData.js)
All exports match API_SCHEMA.yaml exactly:
- `MOCK_TICKETS` — 5 tickets (urgent→low), staff: alice, bob, diana
- `MOCK_INVENTORY` — 8 items; chocolate chips(2) + yeast(3) = critical (red)
- `MOCK_SANITATION_ITEMS` — 8 items, 4 complete / 4 incomplete
- `MOCK_CLEANING_TASKS` — 10 tasks, 4 complete / 6 incomplete
- `MOCK_HACCP_GROUPS` — 7 groups, 21 checks (frontend-only, no backend endpoint yet)

### HACCP Groups
HACCP = Hazard Analysis and Critical Control Points (food safety regulatory standard).
Groups: Temperature Monitoring (4), Allergen Controls (3), Personal Hygiene (3), Cross-Contamination Prevention (3), Date Labeling & FIFO (3), Pest Control (2), Equipment Calibration (3).
No backend endpoint exists yet — stored as frontend-only mock. Plan: add as checklist_type "haccp" in backend.

---

## [DATA FLOW]

```
Voice: Staff → Microphone → PyAudio → Gemini Live API → tool call
                                                         ↓
                                               tool_handlers.py
                                                         ↓
                                                 db.py (SQLite)
                                                         ↓
                                               audit_log + result
                                                         ↓
                                         Gemini audio response → Speaker

REST (Dashboard): Browser → fetch(localhost:8000/api/...) → FastAPI (main.py)
                                                              ↓
                                                       db.py (SQLite)
                                                              ↓
                                                      JSON response
                                                              ↓
                                                   React component state
```

---

## [CODE EVOLUTION RULES]

- NEVER modify `FRONTEND/src/main.jsx`
- NEVER overwrite existing `--text`, `--bg`, `--accent` etc. CSS vars — only append `--bk-*` vars
- All mock data objects must match API_SCHEMA.yaml shapes exactly
- Each write handler in UI must have a `// TODO: POST /api/...` comment
- Maintain `--bk-*` dark mode variants when adding new colour vars
- Backend: do not change response shapes without updating mockData.js + API_SCHEMA.yaml

---

## [WHAT'S DONE]

- [x] Full Python backend: FastAPI + SQLite, all 8 CRUD tools, audit logging
- [x] Gemini Live API voice integration
- [x] Ticket system with AI-determined urgency
- [x] staff_id required on all write operations
- [x] React 19 + Vite 6 dashboard scaffold
- [x] 4-tab operations dashboard (Tickets, Inventory, Cleaning, HACCP)
- [x] Mock data matching all API schemas
- [x] Interactive checkboxes with local state (TODO stubs for API)
- [x] Live clock in header, mobile-responsive layout

---

## [WHAT'S NEXT]

- [ ] Wire real API calls (replace MOCK_* imports with fetch to localhost:8000)
- [ ] Add HACCP endpoint to backend (checklist_type: "haccp" or new table)
- [ ] NFC staff identification (replace --staff-id CLI flag)
- [ ] Conversation transcript logging to DB
- [ ] Session management for >15min voice sessions (Gemini Live API limit)
- [ ] Ticket resolution workflow (office can close/update tickets)
- [ ] Real-time push notifications for urgent tickets
- [ ] Export reports: CSV/PDF (daily cleaning log, inventory snapshot, ticket summary)
- [ ] Custom checklist items (add/remove per bakery)
