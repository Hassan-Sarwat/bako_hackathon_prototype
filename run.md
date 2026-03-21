# Running the Bako Bakery App

## Prerequisites

| Tool | Version | Install |
|---|---|---|
| Python | ≥ 3.13 | https://python.org |
| uv | latest | `pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | ≥ 18 | https://nodejs.org |
| npm | ≥ 9 | comes with Node.js |

---

## 1. Set up the environment

### Clone / enter the project

```bash
cd "bako hackathon/bako_hackathon_prototype"
```

### Create a `.env` file

The backend needs a Gemini API key for the voice assistant feature.

```bash
cp .env.example .env   # if an example exists, otherwise create manually
```

Edit `.env` and add:

```
GEMINI_API_KEY=your_key_here
```

> The REST API and dashboard work without a key. The key is only required for the voice mode.

### Install Python dependencies

```bash
uv sync
```

### Install frontend dependencies

```bash
cd FRONTEND
npm install
cd ..
```

---

## 2. Set up the SQLite database (`bakery.db`)

The database is created automatically when the backend starts for the first time. No manual setup is needed.

**What happens on first run:**
- `bakery.db` is created in the project root.
- Tables are created: `checklist_items`, `materials`, `cleaning_tasks`, `tickets`, `audit_log`.
- Seed data is inserted: 8 sanitation checklist items, default materials list, and today's 10 cleaning tasks.

**To reset the database to a clean state:**

```bash
rm bakery.db
uv run -m src   # restarts and re-seeds automatically
```

**To inspect the database manually:**

```bash
python3 - <<'EOF'
import sqlite3
con = sqlite3.connect("bakery.db")
con.row_factory = sqlite3.Row
for table in ["checklist_items", "materials", "cleaning_tasks", "tickets"]:
    rows = con.execute(f"SELECT * FROM {table} LIMIT 5").fetchall()
    print(f"\n--- {table} ---")
    for r in rows:
        print(dict(r))
EOF
```

---

## 3. Run both servers together

```bash
./run.sh
```

This starts:
- **Backend** at http://localhost:8000
- **Frontend** at http://localhost:5173

Press `Ctrl+C` to stop both.

---

## 4. Run servers separately (optional)

**Backend only:**

```bash
uv run -m src
```

**Frontend only:**

```bash
cd FRONTEND
npm run dev
```

---

## 5. Verify everything is working

- Open http://localhost:5173 in your browser.
- The dashboard should load with live data from the database.
- Check backend health: http://localhost:8000/api/health → `{"status": "ok"}`
- Check all data: http://localhost:8000/api/dashboard

---

## API overview

| Endpoint | Method | Description |
|---|---|---|
| `/api/health` | GET | Health check |
| `/api/dashboard` | GET | All data in one call |
| `/api/tickets` | GET | Open tickets |
| `/api/inventory` | GET | Inventory log |
| `/api/checklist/{type}/items` | GET | Checklist items (`sanitation` or `inventory`) |
| `/api/checklist/items/{id}/complete` | PUT | Mark item complete |
| `/api/checklist/items/{id}/incomplete` | PUT | Mark item incomplete |
| `/api/cleaning/tasks` | GET | Today's cleaning tasks |
| `/api/cleaning/tasks/{id}/complete` | PUT | Mark task complete |
| `/api/cleaning/tasks/{id}/incomplete` | PUT | Mark task incomplete |
| `/api/materials` | GET | Current material stock levels |

Full schema: see `API_SCHEMA.yaml`.
