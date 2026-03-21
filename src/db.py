"""SQLite database setup, schema, seed data, and query helpers."""

import re
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from .config import DB_PATH


# ---------------------------------------------------------------------------
# Amount parsing helpers
# ---------------------------------------------------------------------------

_AMOUNT_RE = re.compile(r'^([\d.,]+)\s*(.*)$')

_UNIT_TO_BASE = {
    'kg': ('g', 1000),
    'g': ('g', 1),
    'l': ('ml', 1000),
    'ml': ('ml', 1),
    'stück': ('Stuck', 1),
    'stuck': ('Stuck', 1),
    'stk': ('Stuck', 1),
}


def parse_amount(text: str) -> tuple[float, str]:
    """Parse a text amount like '200g' or '2,5 kg' into (value, unit).

    Handles German comma-as-decimal (e.g. '2,5' → 2.5).
    Returns (0.0, '') if parsing fails.
    """
    text = text.strip()
    m = _AMOUNT_RE.match(text)
    if not m:
        return (0.0, '')
    num_str = m.group(1).replace(',', '.')
    try:
        value = float(num_str)
    except ValueError:
        return (0.0, '')
    unit = m.group(2).strip() or 'Stuck'
    return (value, unit)


def to_base_units(value: float, unit: str) -> tuple[float, str]:
    """Normalize a value+unit to base units (g, ml, or Stuck)."""
    key = unit.lower().rstrip('.')
    if key in _UNIT_TO_BASE:
        base_unit, factor = _UNIT_TO_BASE[key]
        return (value * factor, base_unit)
    # Unknown unit — pass through as-is
    return (value, unit)

# Default checklist items for a bakery
SANITATION_ITEMS = [
    "Arbeitsflächen desinfizieren",
    "Öfen innen reinigen",
    "Rührschüsseln und Utensilien waschen",
    "Bäckereiboden wischen",
    "Vitrinen reinigen",
    "Spülbecken und Abfluss desinfizieren",
    "Mülleimer leeren",
    "Gerätegriffe abwischen",
]

MATERIAL_ITEMS = [
    "Weizenmehl",
    "Zucker",
    "Butter",
    "Eier",
    "Hefe",
    "Vanilleextrakt",
    "Schokoladenstückchen",
    "Backpulver",
]

# Default daily cleaning tasks
CLEANING_TASKS = [
    {"area": "Arbeitsflächen", "action": "Alle Arbeitsflächen und Theken desinfizieren"},
    {"area": "Öfen", "action": "Öfen und Roste innen reinigen"},
    {"area": "Mischgeräte", "action": "Rührschüsseln, Utensilien und Aufsätze waschen"},
    {"area": "Boden", "action": "Bäckereiboden kehren und wischen"},
    {"area": "Vitrinen", "action": "Vitrinen reinigen und desinfizieren"},
    {"area": "Spülbecken und Abflüsse", "action": "Spülbecken desinfizieren und Abflüsse reinigen"},
    {"area": "Müll und Recycling", "action": "Alle Müll- und Recyclingbehälter leeren"},
    {"area": "Gerätegriffe", "action": "Alle Gerätegriffe und Knöpfe abwischen"},
    {"area": "Lagerbereiche", "action": "Lagerregale ordnen und reinigen"},
    {"area": "Toiletten", "action": "Toiletten reinigen und auffüllen"},
]


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables and seed with default data if empty."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS checklist_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checklist_type TEXT NOT NULL,
            item_name TEXT NOT NULL,
            is_complete INTEGER DEFAULT 0,
            completed_at TEXT,
            completed_by TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL UNIQUE,
            count INTEGER NOT NULL DEFAULT 0,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        );

        CREATE TABLE IF NOT EXISTS cleaning_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_date TEXT NOT NULL,
            area TEXT NOT NULL,
            action TEXT NOT NULL,
            is_complete INTEGER DEFAULT 0,
            completed_at TEXT,
            completed_by TEXT,
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            urgency TEXT NOT NULL DEFAULT 'normal',
            status TEXT NOT NULL DEFAULT 'open',
            raised_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            resolved_at TEXT 
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_id TEXT,
            user_message TEXT,
            ai_model TEXT,
            ai_response TEXT,
            tool_name TEXT,
            tool_args TEXT,
            tool_result TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_name TEXT NOT NULL,
            schedule_date TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            cleaning INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS baked_goods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            recipe TEXT,
            price REAL NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS product_materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            material_id INTEGER NOT NULL,
            amount TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES baked_goods(id) ON DELETE CASCADE,
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
            UNIQUE(product_id, material_id)
        );

        CREATE TABLE IF NOT EXISTS raw_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            amount TEXT NOT NULL,
            price REAL NOT NULL,
            purchase_date TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS cooking_plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_date TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES baked_goods(id) ON DELETE CASCADE,
            UNIQUE(plan_date, product_id)
        );
    """)

    # Seed sanitation checklist if empty
    cursor.execute("SELECT COUNT(*) FROM checklist_items")
    if cursor.fetchone()[0] == 0:
        for item in SANITATION_ITEMS:
            cursor.execute(
                "INSERT INTO checklist_items (checklist_type, item_name) VALUES (?, ?)",
                ("sanitation", item),
            )

    # Seed materials if empty
    cursor.execute("SELECT COUNT(*) FROM materials")
    if cursor.fetchone()[0] == 0:
        for item in MATERIAL_ITEMS:
            cursor.execute(
                "INSERT INTO materials (item_name, count) VALUES (?, 0)",
                (item,),
            )

    # --- Migration: add amount_value / amount_unit columns ----------------
    _migrate_amount_columns(cursor)

    conn.commit()
    conn.close()


def _migrate_amount_columns(cursor: sqlite3.Cursor) -> None:
    """Add amount_value and amount_unit columns to product_materials and
    raw_purchases if they don't exist, then backfill from the text amount."""
    for table in ("product_materials", "raw_purchases"):
        cols = {row[1] for row in cursor.execute(f"PRAGMA table_info({table})")}
        if "amount_value" not in cols:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN amount_value REAL")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN amount_unit TEXT")

        # Backfill rows that haven't been parsed yet
        cursor.execute(f"SELECT id, amount FROM {table} WHERE amount_value IS NULL")
        for row in cursor.fetchall():
            val, unit = parse_amount(row["amount"])
            val, unit = to_base_units(val, unit)
            cursor.execute(
                f"UPDATE {table} SET amount_value = ?, amount_unit = ? WHERE id = ?",
                (val, unit, row["id"]),
            )


def get_all_checklist_items(checklist_type: str) -> list[dict]:
    """Get all items for a checklist type (complete and incomplete)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, checklist_type, item_name, is_complete, completed_at, completed_by, notes "
        "FROM checklist_items WHERE checklist_type = ? ORDER BY id",
        (checklist_type,),
    )
    items = [
        {
            "id": row["id"],
            "checklist_type": row["checklist_type"],
            "item_name": row["item_name"],
            "is_complete": bool(row["is_complete"]),
            "completed_at": row["completed_at"],
            "completed_by": row["completed_by"],
            "notes": row["notes"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return items


def get_incomplete_items(checklist_type: str) -> list[dict]:
    """Get all incomplete items for a checklist type."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, item_name FROM checklist_items WHERE checklist_type = ? AND is_complete = 0",
        (checklist_type,),
    )
    items = [{"id": row["id"], "name": row["item_name"]} for row in cursor.fetchall()]
    conn.close()
    return items


def mark_item_complete(item_id: int, notes: str | None = None, staff_id: str | None = None) -> dict:
    """Mark a checklist item as complete. Requires staff_id to be set."""
    if not staff_id:
        return {"status": "error", "message": "Cannot mark item complete without a staff member identified. Please scan your NFC card first."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE checklist_items SET is_complete = 1, completed_at = ?, completed_by = ?, notes = ? WHERE id = ?",
        (datetime.now().isoformat(), staff_id, notes, item_id),
    )
    conn.commit()

    cursor.execute("SELECT item_name, checklist_type FROM checklist_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "item_name": row["item_name"], "checklist_type": row["checklist_type"], "completed_by": staff_id}
    return {"status": "error", "message": f"Item {item_id} not found"}


def mark_item_incomplete(item_id: int, staff_id: str | None = None) -> dict:
    """Mark a checklist item as incomplete. Requires staff_id to be set."""
    if not staff_id:
        return {"status": "error", "message": "Cannot update item without a staff member identified. Please scan your NFC card first."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE checklist_items SET is_complete = 0, completed_at = NULL, completed_by = NULL, notes = NULL WHERE id = ?",
        (item_id,),
    )
    conn.commit()

    cursor.execute("SELECT item_name FROM checklist_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "item_name": row["item_name"]}
    return {"status": "error", "message": f"Item {item_id} not found"}


def update_material_count(item_name: str, count: int, staff_id: str | None = None) -> dict:
    """Update the count of a material. Creates it if it doesn't exist. Requires staff_id."""
    if not staff_id:
        return {"status": "error", "message": "Cannot update material without a staff member identified. Please scan your NFC card first."}

    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO materials (item_name, count, updated_at, updated_by) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(item_name) DO UPDATE SET count = ?, updated_at = ?, updated_by = ?",
        (item_name, count, now, staff_id, count, now, staff_id),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "item_name": item_name, "count": count, "updated_by": staff_id}


def get_materials() -> list[dict]:
    """Get all materials with their current counts."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, item_name, count, updated_at, updated_by FROM materials ORDER BY item_name"
    )
    materials = [
        {
            "id": row["id"],
            "item_name": row["item_name"],
            "count": row["count"],
            "updated_at": row["updated_at"],
            "updated_by": row["updated_by"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return materials


def get_stale_materials(days: int = 7) -> list[dict]:
    """Get materials that haven't been updated in the given number of days."""
    conn = get_connection()
    cursor = conn.cursor()
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    cursor.execute(
        "SELECT id, item_name, count, updated_at, updated_by FROM materials "
        "WHERE updated_at IS NULL OR updated_at < ? ORDER BY updated_at",
        (cutoff,),
    )
    materials = [
        {
            "id": row["id"],
            "item_name": row["item_name"],
            "count": row["count"],
            "updated_at": row["updated_at"],
            "updated_by": row["updated_by"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return materials


def ensure_daily_cleaning_tasks() -> None:
    """Create today's cleaning tasks if they don't exist yet. Called automatically."""
    today = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM cleaning_tasks WHERE task_date = ?", (today,)
    )
    if cursor.fetchone()[0] == 0:
        for task in CLEANING_TASKS:
            cursor.execute(
                "INSERT INTO cleaning_tasks (task_date, area, action) VALUES (?, ?, ?)",
                (today, task["area"], task["action"]),
            )
        conn.commit()
    conn.close()


def get_cleaning_tasks() -> list[dict]:
    """Get today's cleaning tasks with their completion status."""
    ensure_daily_cleaning_tasks()
    today = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, area, action, is_complete, completed_by, completed_at, notes "
        "FROM cleaning_tasks WHERE task_date = ? ORDER BY id",
        (today,),
    )
    tasks = [
        {
            "id": row["id"],
            "area": row["area"],
            "action": row["action"],
            "is_complete": bool(row["is_complete"]),
            "completed_by": row["completed_by"],
            "completed_at": row["completed_at"],
            "notes": row["notes"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return tasks


def get_incomplete_cleaning_tasks() -> list[dict]:
    """Get today's remaining incomplete cleaning tasks."""
    ensure_daily_cleaning_tasks()
    today = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, area, action FROM cleaning_tasks "
        "WHERE task_date = ? AND is_complete = 0 ORDER BY id",
        (today,),
    )
    tasks = [
        {"id": row["id"], "area": row["area"], "action": row["action"]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return tasks


def mark_cleaning_complete(task_id: int, notes: str | None = None, staff_id: str | None = None) -> dict:
    """Mark a cleaning task as complete. Requires staff_id."""
    if not staff_id:
        return {"status": "error", "message": "Cannot mark task complete without a staff member identified. Please scan your NFC card first."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cleaning_tasks SET is_complete = 1, completed_at = ?, completed_by = ?, notes = ? WHERE id = ?",
        (datetime.now().isoformat(), staff_id, notes, task_id),
    )
    conn.commit()

    cursor.execute("SELECT area, action FROM cleaning_tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "area": row["area"], "action": row["action"], "completed_by": staff_id}
    return {"status": "error", "message": f"Cleaning task {task_id} not found"}


def mark_cleaning_incomplete(task_id: int, staff_id: str | None = None) -> dict:
    """Mark a cleaning task as incomplete. Requires staff_id."""
    if not staff_id:
        return {"status": "error", "message": "Cannot update task without a staff member identified. Please scan your NFC card first."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cleaning_tasks SET is_complete = 0, completed_at = NULL, completed_by = NULL, notes = NULL WHERE id = ?",
        (task_id,),
    )
    conn.commit()

    cursor.execute("SELECT area FROM cleaning_tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "area": row["area"]}
    return {"status": "error", "message": f"Cleaning task {task_id} not found"}


def get_cleaning_summary() -> dict:
    """Get today's cleaning task completion summary."""
    ensure_daily_cleaning_tasks()
    today = date.today().isoformat()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as total FROM cleaning_tasks WHERE task_date = ?", (today,)
    )
    total = cursor.fetchone()["total"]
    cursor.execute(
        "SELECT COUNT(*) as done FROM cleaning_tasks WHERE task_date = ? AND is_complete = 1",
        (today,),
    )
    done = cursor.fetchone()["done"]
    conn.close()

    return {
        "date": today,
        "completed": done,
        "total": total,
        "remaining": total - done,
        "all_done": done == total,
    }


def get_checklist_summary(checklist_type: str) -> dict:
    """Get completion summary for a checklist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as total FROM checklist_items WHERE checklist_type = ?",
        (checklist_type,),
    )
    total = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT COUNT(*) as done FROM checklist_items WHERE checklist_type = ? AND is_complete = 1",
        (checklist_type,),
    )
    done = cursor.fetchone()["done"]
    conn.close()

    return {
        "checklist_type": checklist_type,
        "completed": done,
        "total": total,
        "remaining": total - done,
    }


def raise_ticket(
    title: str,
    description: str,
    category: str,
    urgency: str = "normal",
    raised_by: str | None = None,
) -> dict:
    """Raise a new ticket for the office."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tickets (title, description, category, urgency, raised_by) VALUES (?, ?, ?, ?, ?)",
        (title, description, category, urgency, raised_by),
    )
    ticket_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {
        "status": "success",
        "ticket_id": ticket_id,
        "title": title,
        "category": category,
        "urgency": urgency,
    }


def get_open_tickets() -> list[dict]:
    """Get all open tickets."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, description, category, urgency, raised_by, created_at FROM tickets WHERE status = 'open' ORDER BY CASE urgency WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 WHEN 'low' THEN 3 END, created_at DESC"
    )
    tickets = [
        {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "category": row["category"],
            "urgency": row["urgency"],
            "raised_by": row["raised_by"],
            "created_at": row["created_at"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return tickets


def close_ticket(ticket_id: int) -> dict:
    """Close a ticket by setting its status to 'close'."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE tickets SET status = 'close', resolved_at = ? WHERE id = ? AND status = 'open'",
        (datetime.utcnow().isoformat(), ticket_id),
    )
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    if affected == 0:
        return {"status": "error", "message": f"Ticket {ticket_id} not found or already closed"}
    return {"status": "ok", "ticket_id": ticket_id, "new_status": "close"}


def log_audit(
    staff_id: str | None = None,
    user_message: str | None = None,
    ai_model: str | None = None,
    ai_response: str | None = None,
    tool_name: str | None = None,
    tool_args: str | None = None,
    tool_result: str | None = None,
) -> dict:
    """Log an interaction to the audit table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO audit_log (staff_id, user_message, ai_model, ai_response, tool_name, tool_args, tool_result) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (staff_id, user_message, ai_model, ai_response, tool_name, tool_args, tool_result),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "audit_id": cursor.lastrowid}


def get_audit_log(limit: int = 50, staff_id: str | None = None) -> list[dict]:
    """Get recent audit log entries, optionally filtered by staff_id."""
    conn = get_connection()
    cursor = conn.cursor()
    if staff_id:
        cursor.execute(
            "SELECT id, staff_id, user_message, ai_model, ai_response, tool_name, tool_args, tool_result, created_at "
            "FROM audit_log WHERE staff_id = ? ORDER BY created_at DESC LIMIT ?",
            (staff_id, limit),
        )
    else:
        cursor.execute(
            "SELECT id, staff_id, user_message, ai_model, ai_response, tool_name, tool_args, tool_result, created_at "
            "FROM audit_log ORDER BY created_at DESC LIMIT ?",
            (limit,),
        )
    entries = [
        {
            "id": row["id"],
            "staff_id": row["staff_id"],
            "user_message": row["user_message"],
            "ai_model": row["ai_model"],
            "ai_response": row["ai_response"],
            "tool_name": row["tool_name"],
            "tool_args": row["tool_args"],
            "tool_result": row["tool_result"],
            "created_at": row["created_at"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return entries


def get_product_loss_analysis(start_date: str, end_date: str) -> list[dict]:
    """Analyse material losses attributed to each product/recipe.

    Uses proportional attribution: each material's unaccounted loss is
    distributed across products based on their share of that material's
    total expected usage.
    """
    # 1. Get per-material loss data from existing analysis
    material_losses = get_material_usage_analysis(start_date, end_date)
    loss_by_mid = {
        m["material_id"]: m for m in material_losses
    }

    # 2. Get per-(product, material) expected usage
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cp.product_id, bg.name AS product_name, bg.price AS product_price, "
        "pm.material_id, pm.amount_value, pm.amount_unit, "
        "SUM(cp.quantity) AS total_quantity "
        "FROM cooking_plans cp "
        "JOIN product_materials pm ON cp.product_id = pm.product_id "
        "JOIN baked_goods bg ON cp.product_id = bg.id "
        "WHERE cp.plan_date BETWEEN ? AND ? AND pm.amount_value IS NOT NULL "
        "GROUP BY cp.product_id, pm.material_id",
        (start_date, end_date),
    )
    rows = cursor.fetchall()
    conn.close()

    # 3. Compute total expected usage per material (across all products)
    total_usage_by_mid: dict[int, float] = {}
    for row in rows:
        mid = row["material_id"]
        usage = row["amount_value"] * row["total_quantity"]
        total_usage_by_mid[mid] = total_usage_by_mid.get(mid, 0.0) + usage

    # 4. Attribute losses per product
    products: dict[int, dict] = {}
    for row in rows:
        pid = row["product_id"]
        mid = row["material_id"]
        mat = loss_by_mid.get(mid)
        if not mat:
            continue  # material was skipped in analysis (incompatible units, etc.)

        usage = row["amount_value"] * row["total_quantity"]
        total_usage = total_usage_by_mid.get(mid, 0.0)
        share = usage / total_usage if total_usage > 0 else 0.0
        attributed = max(0.0, mat["unaccounted_loss"]) * mat["unit_price"] * share

        if pid not in products:
            products[pid] = {
                "product_id": pid,
                "product_name": row["product_name"],
                "product_price": row["product_price"] or 0.0,
                "total_units_planned": row["total_quantity"],
                "materials_count": 0,
                "attributed_loss_value": 0.0,
                "_material_ids": set(),
            }

        products[pid]["attributed_loss_value"] += attributed
        products[pid]["_material_ids"].add(mid)

    # 5. Finalise results
    results: list[dict] = []
    for p in products.values():
        p["materials_count"] = len(p.pop("_material_ids"))
        total_units = p["total_units_planned"]
        loss_val = p["attributed_loss_value"]
        price = p["product_price"]

        p["attributed_loss_value"] = round(loss_val, 2)
        p["loss_per_unit"] = round(loss_val / total_units, 4) if total_units > 0 else 0.0
        p["loss_pct_of_price"] = round(
            (p["loss_per_unit"] / price * 100) if price > 0 else 0.0, 1
        )
        p["flagged"] = p["loss_pct_of_price"] > 20
        results.append(p)

    results.sort(key=lambda r: r["attributed_loss_value"], reverse=True)
    return results


def get_product_loss_drilldown(
    product_id: int, start_date: str, end_date: str
) -> list[dict]:
    """Get per-material loss breakdown for a specific product."""
    # 1. Get per-material loss data
    material_losses = get_material_usage_analysis(start_date, end_date)
    loss_by_mid = {m["material_id"]: m for m in material_losses}

    # 2. Get this product's usage of each material
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT pm.material_id, m.item_name AS material_name, "
        "pm.amount_value, pm.amount_unit, "
        "SUM(cp.quantity) AS total_quantity "
        "FROM cooking_plans cp "
        "JOIN product_materials pm ON cp.product_id = pm.product_id "
        "JOIN materials m ON pm.material_id = m.id "
        "WHERE cp.product_id = ? AND cp.plan_date BETWEEN ? AND ? "
        "AND pm.amount_value IS NOT NULL "
        "GROUP BY pm.material_id",
        (product_id, start_date, end_date),
    )
    rows = cursor.fetchall()

    # 3. Get total usage per material across all products (for share calculation)
    cursor.execute(
        "SELECT pm.material_id, SUM(pm.amount_value * cp.quantity) AS total_usage "
        "FROM cooking_plans cp "
        "JOIN product_materials pm ON cp.product_id = pm.product_id "
        "WHERE cp.plan_date BETWEEN ? AND ? AND pm.amount_value IS NOT NULL "
        "GROUP BY pm.material_id",
        (start_date, end_date),
    )
    total_usage_by_mid = {
        row["material_id"]: row["total_usage"] for row in cursor.fetchall()
    }
    conn.close()

    # 4. Build per-material breakdown
    entries: list[dict] = []
    for row in rows:
        mid = row["material_id"]
        mat = loss_by_mid.get(mid)
        if not mat:
            continue

        product_usage = row["amount_value"] * row["total_quantity"]
        total_usage = total_usage_by_mid.get(mid, 0.0)
        share = product_usage / total_usage if total_usage > 0 else 0.0
        loss_qty = max(0.0, mat["unaccounted_loss"]) * share
        loss_val = loss_qty * mat["unit_price"]

        entries.append({
            "material_id": mid,
            "material_name": row["material_name"],
            "unit": row["amount_unit"] or "",
            "expected_usage": round(product_usage, 2),
            "material_total_loss": round(max(0.0, mat["unaccounted_loss"]), 2),
            "product_share_pct": round(share * 100, 1),
            "attributed_loss_qty": round(loss_qty, 2),
            "attributed_loss_value": round(loss_val, 2),
        })

    entries.sort(key=lambda e: e["attributed_loss_value"], reverse=True)
    return entries


def log_conversation(
    staff_id: str | None = None,
    user_message: str | None = None,
    ai_model: str | None = None,
    ai_response: str | None = None,
) -> dict:
    """Log a conversation turn (no tool call) to the audit table."""
    return log_audit(
        staff_id=staff_id,
        user_message=user_message,
        ai_model=ai_model,
        ai_response=ai_response,
    )


def reset_checklists() -> dict:
    """Reset all checklist items to incomplete for a new day."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE checklist_items SET is_complete = 0, completed_at = NULL, notes = NULL")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "All checklists reset for a new day"}


# ---------------------------------------------------------------------------
# Schedule helpers
# ---------------------------------------------------------------------------

def get_schedules(
    schedule_date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Get schedules, optionally filtered by date or date range."""
    conn = get_connection()
    cursor = conn.cursor()
    if schedule_date:
        cursor.execute(
            "SELECT id, employee_name, schedule_date, start_time, end_time, cleaning, created_at "
            "FROM schedules WHERE schedule_date = ? ORDER BY start_time",
            (schedule_date,),
        )
    elif start_date and end_date:
        cursor.execute(
            "SELECT id, employee_name, schedule_date, start_time, end_time, cleaning, created_at "
            "FROM schedules WHERE schedule_date >= ? AND schedule_date <= ? ORDER BY schedule_date, start_time",
            (start_date, end_date),
        )
    else:
        cursor.execute(
            "SELECT id, employee_name, schedule_date, start_time, end_time, cleaning, created_at "
            "FROM schedules ORDER BY schedule_date, start_time"
        )
    items = [
        {
            "id": row["id"],
            "employee_name": row["employee_name"],
            "schedule_date": row["schedule_date"],
            "start_time": row["start_time"],
            "end_time": row["end_time"],
            "cleaning": bool(row["cleaning"]),
            "created_at": row["created_at"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return items


def create_schedule(
    employee_name: str,
    schedule_date: str,
    start_time: str,
    end_time: str,
    cleaning: int = 0,
) -> dict:
    """Create a new schedule entry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO schedules (employee_name, schedule_date, start_time, end_time, cleaning) "
        "VALUES (?, ?, ?, ?, ?)",
        (employee_name, schedule_date, start_time, end_time, cleaning),
    )
    schedule_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "success", "id": schedule_id}


def update_schedule(schedule_id: int, **fields) -> dict:
    """Update a schedule entry. Pass only the fields to change."""
    allowed = {"employee_name", "schedule_date", "start_time", "end_time", "cleaning"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"status": "error", "message": "No valid fields to update"}
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [schedule_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE schedules SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Schedule {schedule_id} not found"}
    return {"status": "success", "id": schedule_id}


def delete_schedule(schedule_id: int) -> dict:
    """Delete a schedule entry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM schedules WHERE id = ?", (schedule_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Schedule {schedule_id} not found"}
    return {"status": "success", "id": schedule_id}


# ---------------------------------------------------------------------------
# Baked goods helpers
# ---------------------------------------------------------------------------

def get_baked_goods() -> list[dict]:
    """Get all baked goods (products)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, recipe, price, created_at FROM baked_goods ORDER BY name"
    )
    items = [
        {
            "id": row["id"],
            "name": row["name"],
            "recipe": row["recipe"],
            "price": row["price"],
            "created_at": row["created_at"],
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return items


def get_baked_good(product_id: int) -> dict | None:
    """Get a single baked good with its materials."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, recipe, price, created_at FROM baked_goods WHERE id = ?",
        (product_id,),
    )
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    product = {
        "id": row["id"],
        "name": row["name"],
        "recipe": row["recipe"],
        "price": row["price"],
        "created_at": row["created_at"],
    }
    cursor.execute(
        "SELECT pm.id, pm.material_id, m.item_name AS material_name, pm.amount "
        "FROM product_materials pm JOIN materials m ON pm.material_id = m.id "
        "WHERE pm.product_id = ? ORDER BY m.item_name",
        (product_id,),
    )
    product["materials"] = [
        {
            "id": r["id"],
            "material_id": r["material_id"],
            "material_name": r["material_name"],
            "amount": r["amount"],
        }
        for r in cursor.fetchall()
    ]
    conn.close()
    return product


def create_baked_good(name: str, price: float, recipe: str | None = None) -> dict:
    """Create a new baked good (product)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO baked_goods (name, price, recipe) VALUES (?, ?, ?)",
            (name, price, recipe),
        )
        product_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"status": "error", "message": f"Product '{name}' already exists"}
    conn.close()
    return {"status": "success", "id": product_id}


def update_baked_good(product_id: int, **fields) -> dict:
    """Update a baked good. Pass only the fields to change."""
    allowed = {"name", "price", "recipe"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"status": "error", "message": "No valid fields to update"}
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [product_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE baked_goods SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Product {product_id} not found"}
    return {"status": "success", "id": product_id}


def delete_baked_good(product_id: int) -> dict:
    """Delete a baked good (cascades to product_materials)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM baked_goods WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Product {product_id} not found"}
    return {"status": "success", "id": product_id}


# ---------------------------------------------------------------------------
# Product materials helpers
# ---------------------------------------------------------------------------

def get_product_materials(product_id: int) -> list[dict]:
    """Get all materials for a product."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT pm.id, pm.material_id, m.item_name AS material_name, pm.amount "
        "FROM product_materials pm JOIN materials m ON pm.material_id = m.id "
        "WHERE pm.product_id = ? ORDER BY m.item_name",
        (product_id,),
    )
    items = [
        {
            "id": r["id"],
            "material_id": r["material_id"],
            "material_name": r["material_name"],
            "amount": r["amount"],
        }
        for r in cursor.fetchall()
    ]
    conn.close()
    return items


def set_product_materials(product_id: int, materials: list[dict]) -> dict:
    """Replace all materials for a product. Each dict has material_id and amount."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_materials WHERE product_id = ?", (product_id,))
    for mat in materials:
        val, unit = parse_amount(mat["amount"])
        val, unit = to_base_units(val, unit)
        cursor.execute(
            "INSERT INTO product_materials (product_id, material_id, amount, amount_value, amount_unit) "
            "VALUES (?, ?, ?, ?, ?)",
            (product_id, mat["material_id"], mat["amount"], val, unit),
        )
    conn.commit()
    conn.close()
    return {"status": "success", "product_id": product_id, "count": len(materials)}


# ---------------------------------------------------------------------------
# Raw purchases helpers
# ---------------------------------------------------------------------------

def get_raw_purchases(
    material_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    """Get raw material purchases with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()
    query = (
        "SELECT rp.id, rp.material_id, m.item_name AS material_name, "
        "rp.amount, rp.price, rp.purchase_date, rp.created_at "
        "FROM raw_purchases rp JOIN materials m ON rp.material_id = m.id"
    )
    conditions = []
    params: list = []
    if material_id is not None:
        conditions.append("rp.material_id = ?")
        params.append(material_id)
    if start_date:
        conditions.append("rp.purchase_date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("rp.purchase_date <= ?")
        params.append(end_date)
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY rp.purchase_date DESC"
    cursor.execute(query, params)
    items = [
        {
            "id": r["id"],
            "material_id": r["material_id"],
            "material_name": r["material_name"],
            "amount": r["amount"],
            "price": r["price"],
            "purchase_date": r["purchase_date"],
            "created_at": r["created_at"],
        }
        for r in cursor.fetchall()
    ]
    conn.close()
    return items


def create_raw_purchase(
    material_id: int, amount: str, price: float, purchase_date: str
) -> dict:
    """Create a new raw material purchase."""
    val, unit = parse_amount(amount)
    val, unit = to_base_units(val, unit)
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO raw_purchases (material_id, amount, price, purchase_date, amount_value, amount_unit) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (material_id, amount, price, purchase_date, val, unit),
        )
        purchase_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"status": "error", "message": "Invalid material_id"}
    conn.close()
    return {"status": "success", "id": purchase_id}


def update_raw_purchase(purchase_id: int, **fields) -> dict:
    """Update a raw purchase. Pass only the fields to change."""
    allowed = {"material_id", "amount", "price", "purchase_date"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"status": "error", "message": "No valid fields to update"}
    # Keep parsed columns in sync when amount text changes
    if "amount" in updates:
        val, unit = parse_amount(updates["amount"])
        val, unit = to_base_units(val, unit)
        updates["amount_value"] = val
        updates["amount_unit"] = unit
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [purchase_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE raw_purchases SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Purchase {purchase_id} not found"}
    return {"status": "success", "id": purchase_id}


def delete_raw_purchase(purchase_id: int) -> dict:
    """Delete a raw material purchase."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM raw_purchases WHERE id = ?", (purchase_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Purchase {purchase_id} not found"}
    return {"status": "success", "id": purchase_id}


# ---------------------------------------------------------------------------
# Cooking plan helpers
# ---------------------------------------------------------------------------

def get_cooking_plans(plan_date: str | None = None) -> list[dict]:
    """Get cooking plans, optionally filtered by date."""
    conn = get_connection()
    cursor = conn.cursor()
    query = (
        "SELECT cp.id, cp.plan_date, cp.product_id, bg.name AS product_name, "
        "cp.quantity, cp.created_at "
        "FROM cooking_plans cp JOIN baked_goods bg ON cp.product_id = bg.id"
    )
    if plan_date:
        query += " WHERE cp.plan_date = ? ORDER BY bg.name"
        cursor.execute(query, (plan_date,))
    else:
        query += " ORDER BY cp.plan_date DESC, bg.name"
        cursor.execute(query)
    items = [
        {
            "id": r["id"],
            "plan_date": r["plan_date"],
            "product_id": r["product_id"],
            "product_name": r["product_name"],
            "quantity": r["quantity"],
            "created_at": r["created_at"],
        }
        for r in cursor.fetchall()
    ]
    conn.close()
    return items


def create_cooking_plan(plan_date: str, product_id: int, quantity: int) -> dict:
    """Create or update a cooking plan entry (upserts on date+product)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO cooking_plans (plan_date, product_id, quantity) VALUES (?, ?, ?) "
            "ON CONFLICT(plan_date, product_id) DO UPDATE SET quantity = ?",
            (plan_date, product_id, quantity, quantity),
        )
        plan_id = cursor.lastrowid
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return {"status": "error", "message": "Invalid product_id"}
    conn.close()
    return {"status": "success", "id": plan_id}


def update_cooking_plan(plan_id: int, **fields) -> dict:
    """Update a cooking plan entry. Pass only the fields to change."""
    allowed = {"plan_date", "product_id", "quantity"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return {"status": "error", "message": "No valid fields to update"}
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [plan_id]
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE cooking_plans SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Cooking plan {plan_id} not found"}
    return {"status": "success", "id": plan_id}


def delete_cooking_plan(plan_id: int) -> dict:
    """Delete a cooking plan entry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cooking_plans WHERE id = ?", (plan_id,))
    conn.commit()
    conn.close()
    if cursor.rowcount == 0:
        return {"status": "error", "message": f"Cooking plan {plan_id} not found"}
    return {"status": "success", "id": plan_id}


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def get_material_usage_analysis(start_date: str, end_date: str) -> list[dict]:
    """Analyse expected material usage from cooking plans vs purchases.

    Returns a list of materials sorted by estimated loss value (descending).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Expected usage from cooking plans × recipe amounts
    cursor.execute(
        "SELECT pm.material_id, m.item_name, pm.amount_value, pm.amount_unit, cp.quantity "
        "FROM cooking_plans cp "
        "JOIN product_materials pm ON cp.product_id = pm.product_id "
        "JOIN materials m ON pm.material_id = m.id "
        "WHERE cp.plan_date BETWEEN ? AND ? AND pm.amount_value IS NOT NULL",
        (start_date, end_date),
    )
    # Accumulate expected usage per (material_id, base_unit)
    usage: dict[int, dict] = {}  # material_id -> {name, value, unit}
    for row in cursor.fetchall():
        mid = row["material_id"]
        val = row["amount_value"] * row["quantity"]
        unit = row["amount_unit"] or ""
        if mid not in usage:
            usage[mid] = {"name": row["item_name"], "value": 0.0, "unit": unit}
        usage[mid]["value"] += val

    # 2. Purchases in the same date range
    cursor.execute(
        "SELECT material_id, amount_value, amount_unit, price "
        "FROM raw_purchases "
        "WHERE purchase_date BETWEEN ? AND ? AND amount_value IS NOT NULL",
        (start_date, end_date),
    )
    purchases: dict[int, dict] = {}  # material_id -> {total_amount, total_price}
    for row in cursor.fetchall():
        mid = row["material_id"]
        if mid not in purchases:
            purchases[mid] = {"total_amount": 0.0, "total_price": 0.0, "unit": row["amount_unit"] or ""}
        purchases[mid]["total_amount"] += row["amount_value"]
        purchases[mid]["total_price"] += row["price"]

    # 3. Current inventory (in base units — same unit as usage/purchases)
    cursor.execute("SELECT id, count FROM materials")
    stock = {row["id"]: row["count"] for row in cursor.fetchall()}

    conn.close()

    # 4. Build result for every material where purchased >= expected_usage.
    #    Skip materials where usage exceeds purchases (bad data).
    results: list[dict] = []
    for mid, u in usage.items():
        expected = u["value"]
        p = purchases.get(mid, {"total_amount": 0.0, "total_price": 0.0, "unit": ""})
        purchased = p["total_amount"]

        # Skip if units are incompatible between usage and purchase
        if purchased > 0 and p["unit"] and u["unit"] and p["unit"] != u["unit"]:
            continue

        # Skip if expected usage exceeds purchases (impossible scenario)
        if purchased < expected:
            continue

        # Unit price from purchases (cost per base unit)
        unit_price = p["total_price"] / purchased if purchased > 0 else 0.0

        current = stock.get(mid, 0)
        expected_remaining = purchased - expected
        unaccounted_loss = expected_remaining - current  # positive = missing
        loss_pct = (unaccounted_loss / purchased * 100) if purchased > 0 else 0.0
        flagged = unaccounted_loss > 0 and abs(loss_pct) > 20
        estimated_loss_value = max(0.0, unaccounted_loss) * unit_price

        results.append({
            "material_id": mid,
            "material_name": u["name"],
            "unit": u["unit"],
            "expected_usage": round(expected, 2),
            "total_purchased": round(purchased, 2),
            "current_stock": round(current, 2),
            "expected_remaining": round(expected_remaining, 2),
            "unaccounted_loss": round(unaccounted_loss, 2),
            "loss_pct": round(loss_pct, 1),
            "flagged": flagged,
            "unit_price": round(unit_price, 4),
            "estimated_loss_value": round(estimated_loss_value, 2),
        })

    # Sort by estimated loss value descending
    results.sort(key=lambda r: r["estimated_loss_value"], reverse=True)
    return results


def get_material_drilldown(
    material_id: int, start_date: str, end_date: str
) -> list[dict]:
    """Get per-day cooking plan breakdown for a specific material."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT cp.plan_date, bg.name AS product_name, cp.quantity, "
        "pm.amount, pm.amount_value, pm.amount_unit "
        "FROM cooking_plans cp "
        "JOIN product_materials pm ON cp.product_id = pm.product_id "
        "JOIN baked_goods bg ON cp.product_id = bg.id "
        "WHERE pm.material_id = ? AND cp.plan_date BETWEEN ? AND ? "
        "ORDER BY cp.plan_date DESC, bg.name",
        (material_id, start_date, end_date),
    )
    entries = []
    for row in cursor.fetchall():
        per_unit = row["amount_value"] or 0.0
        total_usage = per_unit * row["quantity"]
        entries.append({
            "plan_date": row["plan_date"],
            "product_name": row["product_name"],
            "quantity": row["quantity"],
            "amount_per_unit": row["amount"],
            "amount_value_per_unit": round(per_unit, 2),
            "unit": row["amount_unit"] or "",
            "total_usage": round(total_usage, 2),
        })
    conn.close()
    return entries
