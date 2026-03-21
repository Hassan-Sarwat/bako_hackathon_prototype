# PROJECT CONTEXT — Bako Bakery Voice Assistant

> **Single source of truth for AI assistant context.**
> Load this file at the start of any session — no need to re-read backend/frontend source files.
> Append new learnings rather than overwrite existing sections. Keep it structured and readable.

**Last updated:** 2026-03-21 (Europe/Berlin)

---

## [PROJECT OVERVIEW]

A voice-powered AI assistant for bakery staff to handle daily operations hands-free:
- Inventory logging
- Sanitation checklist tracking
- Cleaning task logging
- Issue/ticket raising for the office

Built for the Bako Hackathon. The backend is fully implemented. The UI dashboard is the active development area.

**Git branch for UI work:** `UI`
**Backend port:** 8000 (uvicorn, hot reload — `uv run -m src`)
**Frontend port:** 5173 (Vite dev server — `npm run dev` from `FRONTEND/`)

---

## [AI ASSISTANT RULES]

1. Understand how backend and frontend are connected.
2. Track data flow across layers.
3. Infer missing logic when needed.
4. Maintain consistency in architecture and coding patterns.
5. When modifying backend, ensure no breaking changes to frontend contracts.
6. Maintain consistent API response formats.
7. Ensure UI reflects backend data correctly.
8. Avoid unnecessary re-renders or inefficient state usage.
9. When given a task: analyze relevant code → summarize understanding → implement.
10. If context is missing: infer intelligently from codebase; ask only if absolutely necessary.

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
| Frontend CSS | Native CSS (no UI library) | — |

---

## [PROJECT FILE STRUCTURE]

```
bako_hackathon_prototype/
├── AGENTS.md               ← project overview + what's done/next (always safe to read)
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
│   │   │   ├── TabNav/         ← horizontal tab bar (4 tabs)
│   │   │   ├── ProgressBar/    ← reusable: props {completed, total, label}
│   │   │   ├── UrgencyBadge/   ← urgency pill: urgent/high/normal/low
│   │   │   ├── CategoryTag/    ← ticket category label
│   │   │   └── ChecklistRow/   ← shared checkbox row (Cleaning + HACCP)
│   │   └── tabs/
│   │       ├── TicketsTab/     ← issue cards grid + TicketCard
│   │       ├── InventoryTab/   ← ingredient count table
│   │       ├── CleaningTab/    ← sanitation + cleaning checklists
│   │       └── HaccpTab/       ← HACCP groups + HaccpGroup
│   ├── EXTRAS/
│   │   └── PROJECT_CONTEXT.md  ← THIS FILE
│   ├── .gitignore          ← excludes node_modules, dist, .vite (EXTRAS/ is tracked)
│   ├── package.json
│   └── vite.config.js
├── bakery.db               ← SQLite DB (auto-created on first run, not committed)
├── pyproject.toml          ← Python dependencies
└── .env                    ← GEMINI_API_KEY (not committed)
```

---

## [BACKEND CONTEXT]

### REST API (FastAPI, port 8000)

All endpoints prefixed `/api/`. CORS allows all origins (permissive for development).

#### Checklists (sanitation | inventory)
```
GET  /api/checklists/{type}/items          → all items with completion state
GET  /api/checklists/{type}/remaining      → incomplete items only
GET  /api/checklists/{type}/summary        → {completed, total, remaining}
POST /api/checklists/items/{id}/complete   body: {staff_id, notes?}
POST /api/checklists/items/{id}/incomplete body: {staff_id}
```

#### Inventory Log
```
GET  /api/inventory   → log entries (limit 50)
POST /api/inventory   body: {item_name, count, staff_id}
```

#### Cleaning Tasks (auto-created daily)
```
GET  /api/cleaning/tasks                    → today's tasks
GET  /api/cleaning/remaining                → incomplete tasks
GET  /api/cleaning/summary                  → {date, completed, total, remaining, all_done}
POST /api/cleaning/tasks/{id}/complete      body: {staff_id, notes?}
POST /api/cleaning/tasks/{id}/incomplete    body: {staff_id}
```

#### Tickets
```
GET  /api/tickets   → open tickets sorted: urgent → high → normal → low
POST /api/tickets   body: {title, description, category, urgency, staff_id}
  categories: machine_breakdown | no_show | stock_shortage | safety | other
  urgency:    urgent | high | normal | low
```

#### Dashboard (aggregate — one call for everything)
```
GET /api/dashboard  → {sanitation, inventory, cleaning, tickets}
```

#### Audit + Admin
```
GET  /api/audit?limit=50&staff_id=x
POST /api/admin/reset-checklists
GET  /api/health
```

### Database Schema

| Table | Key Columns |
|---|---|
| `checklist_items` | id, checklist_type (sanitation\|inventory), item_name, is_complete(0/1), completed_at, completed_by, notes |
| `inventory_log` | id, item_name, count, logged_by, logged_at |
| `cleaning_tasks` | id, task_date, area, action, is_complete, completed_at, completed_by, notes |
| `tickets` | id, title, description, category, urgency, status (open\|closed), raised_by, created_at, resolved_at |
| `audit_log` | id, staff_id, user_message, ai_model, ai_response, tool_name, tool_args, tool_result, created_at |

### Seed Data (hard-coded in db.py)

**Sanitation (8 items):** Sanitize prep surfaces, Clean oven interiors, Wash mixing bowls and utensils, Mop bakery floor, Clean display cases, Sanitize sink and drain, Empty trash bins, Wipe down equipment handles

**Inventory (8 items):** All-purpose flour, Sugar, Butter, Eggs, Yeast, Vanilla extract, Chocolate chips, Baking powder

**Cleaning task areas (10):** Prep surfaces, Ovens, Mixing equipment, Floor, Display cases, Sinks and drains, Trash and recycling, Equipment handles, Storage areas, Restrooms

### Authentication
All write operations require `staff_id`. Hackathon: `--staff-id` CLI flag. Production plan: NFC card reader.

### Voice Mode (separate from REST API, not relevant to dashboard)
Gemini Live API with 12 function-callable tools for real-time voice interaction.
Tools: mark_item_complete/incomplete, get_remaining_items, add_inventory_count, get_cleaning_tasks, get_incomplete_cleaning_tasks, mark_cleaning_complete/incomplete, get_cleaning_summary, get_checklist_summary, raise_ticket, get_open_tickets.

---

## [FRONTEND CONTEXT]

### Dashboard Tabs (implemented)

| Tab ID | Label | Content |
|---|---|---|
| `tickets` | Tickets | Issue cards: urgency badge, category tag, title, description, assignee (raised_by), timestamp |
| `inventory` | Inventory | Ingredient table: name, count (colour-coded), status label, logged_by, time |
| `cleaning` | Cleaning | Sanitation checklist (8 items) + daily cleaning tasks (10 items), each with progress bar |
| `haccp` | HACCP | 7 food-safety category groups, 21 checks total, overall compliance % badge |

### Component Responsibilities

| Component | File | What it does |
|---|---|---|
| `App` | `App.jsx` | Root shell — holds `activeTab` state, renders header with live clock, TabNav, tab router |
| `TabNav` | `components/TabNav/` | 4 tab buttons with accessible `role="tab"` and underline active indicator |
| `ProgressBar` | `components/ProgressBar/` | Generic: `{completed, total, label}` → labelled bar + % text |
| `UrgencyBadge` | `components/UrgencyBadge/` | Coloured pill for urgent/high/normal/low |
| `CategoryTag` | `components/CategoryTag/` | Small label for ticket category |
| `ChecklistRow` | `components/ChecklistRow/` | Checkbox row shared by CleaningTab and HaccpTab; shows completed_by + time when done |
| `TicketsTab` | `tabs/TicketsTab/` | Grid of TicketCard; shows urgent/high count summary at top |
| `TicketCard` | `tabs/TicketsTab/TicketCard.jsx` | Single ticket: header badges, title, description, assignee, date |
| `InventoryTab` | `tabs/InventoryTab/` | CSS Grid table; stock thresholds: ≤3 critical (red), ≤8 low (amber), >8 ok (green) |
| `CleaningTab` | `tabs/CleaningTab/` | Two sections with independent progress bars; local `useState` for checkbox toggling |
| `HaccpTab` | `tabs/HaccpTab/` | Overall compliance % + 7 HaccpGroup components |
| `HaccpGroup` | `tabs/HaccpTab/HaccpGroup.jsx` | Per-category group: header, count badge, progress bar, ChecklistRow list |

### State Management
- `App.jsx`: `useState('tickets')` for active tab; `useEffect` 1s interval for live clock
- `CleaningTab`: `useState` initialized from mock data; local checkbox toggle only
- `HaccpTab`: `useState` initialized from mock data; local checkbox toggle only
- All toggle handlers have `// TODO: POST /api/...` stubs — replace with fetch calls when API is wired

### CSS Variable System

**Existing vars — never modify:**
`--text, --text-h, --bg, --border, --accent, --accent-bg, --accent-border, --shadow, --code-bg`

**Bakery extensions — appended to `index.css` (all `--bk-*` prefixed):**
- Urgency badges: `--bk-{urgent|high|normal|low}-{bg|text|border}`
- Category tags: `--bk-cat-{machine|noshow|stock|safety|other}-{bg|text}`
- Stock levels: `--bk-stock-{ok|low|critical}` + `--bk-stock-{ok|low|critical}-bg`
- Progress bar: `--bk-progress-{track|fill|complete}`
- Header: `--bk-header-bg: #1a1015`, `--bk-header-text: #f5f0ff`
- Full dark mode overrides in `@media (prefers-color-scheme: dark)`

**Rule:** When adding new colour vars, always add a dark mode variant too.

### Mock Data (`FRONTEND/src/data/mockData.js`)
All exports match `API_SCHEMA.yaml` schemas exactly — swap to real fetch calls without restructuring.

| Export | Contents |
|---|---|
| `MOCK_TICKETS` | 5 tickets pre-sorted urgent→low; assignees: alice, bob, diana |
| `MOCK_INVENTORY` | 8 items; chocolate chips (2) + yeast (3) = critical red |
| `MOCK_SANITATION_ITEMS` | 8 items, 4 complete / 4 incomplete |
| `MOCK_CLEANING_TASKS` | 10 tasks, 4 complete / 6 incomplete |
| `MOCK_HACCP_GROUPS` | 7 groups, 21 checks — frontend-only, no backend endpoint yet |

### HACCP Groups (frontend-only)
HACCP = Hazard Analysis and Critical Control Points (food safety regulatory standard).

| Group | Checks |
|---|---|
| Temperature Monitoring | 4 |
| Allergen Controls | 3 |
| Personal Hygiene | 3 |
| Cross-Contamination Prevention | 3 |
| Date Labeling & FIFO | 3 |
| Pest Control | 2 |
| Equipment Calibration | 3 |

Backend plan: store as `checklist_type: "haccp"` or add a dedicated table.

---

## [DATA FLOW]

```
Voice mode:
  Staff → Microphone → PyAudio → Gemini Live API
                                        ↓ tool call
                               tool_handlers.py (async dispatch)
                                        ↓
                                  db.py (SQLite)
                                        ↓
                              audit_log written + result returned
                                        ↓
                         Gemini generates audio response → Speaker

Dashboard (REST):
  Browser → fetch(localhost:8000/api/...) → FastAPI main.py
                                                   ↓
                                            db.py (SQLite)
                                                   ↓
                                           JSON response
                                                   ↓
                                     React component useState
```

---

## [CODE EVOLUTION RULES]

- **NEVER** modify `FRONTEND/src/main.jsx`
- **NEVER** overwrite existing `--text`, `--bg`, `--accent` etc. CSS vars — only append new `--bk-*` vars
- All mock data objects must exactly match `API_SCHEMA.yaml` shapes
- Every write handler in UI must have a `// TODO: POST /api/...` comment until API is wired
- Always add dark mode CSS variant when introducing new `--bk-*` colour vars
- Backend: do not change response shapes without also updating `mockData.js` + `API_SCHEMA.yaml`
- Do NOT break existing functionality; prefer minimal, clean, scalable changes
- Add comments only where logic is non-trivial

---

## [WHAT'S DONE] ✅

- [x] Full Python backend: FastAPI + SQLite, all CRUD operations, audit logging
- [x] Gemini Live API voice integration with 12 callable tools
- [x] Ticket system with AI-determined urgency levels
- [x] `staff_id` required on all write operations (CLI flag for hackathon)
- [x] OpenAPI 3.1.0 schema documented in `API_SCHEMA.yaml`
- [x] React 19 + Vite 6 frontend scaffold initialised in `FRONTEND/`
- [x] 4-tab operations dashboard: Tickets, Inventory, Cleaning, HACCP
- [x] Mock data matching all API schemas (zero-friction swap to real API)
- [x] Urgency badges, category tags, progress bars, checklist rows (reusable components)
- [x] Interactive checkboxes with local state + API TODO stubs
- [x] Live clock in header (1s interval)
- [x] Mobile-responsive layout (breakpoints at 1024px and 640px)
- [x] CSS `--bk-*` variable system with full light + dark mode support
- [x] `FRONTEND/EXTRAS/PROJECT_CONTEXT.md` — this file, tracked in git

---

## [WHAT'S NEXT] 🔲

- [ ] Wire real API calls — replace `MOCK_*` imports with `fetch` to `localhost:8000`
- [ ] Add HACCP backend endpoint (`checklist_type: "haccp"` or new table)
- [ ] NFC staff identification (replace `--staff-id` CLI flag)
- [ ] Conversation transcript logging to DB
- [ ] Session management for >15min voice sessions (Gemini Live API limit)
- [ ] Ticket resolution workflow (office staff can close/update tickets)
- [ ] Real-time push notifications for urgent tickets
- [ ] Export reports: CSV/PDF (daily cleaning log, inventory snapshot, ticket summary)
- [ ] Custom checklist items (add/remove per bakery)
