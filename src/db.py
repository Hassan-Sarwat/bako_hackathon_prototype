"""SQLite database setup, schema, seed data, and query helpers."""

import sqlite3
from datetime import datetime
from pathlib import Path

from .config import DB_PATH

# Default checklist items for a bakery
SANITATION_ITEMS = [
    "Sanitize prep surfaces",
    "Clean oven interiors",
    "Wash mixing bowls and utensils",
    "Mop bakery floor",
    "Clean display cases",
    "Sanitize sink and drain",
    "Empty trash bins",
    "Wipe down equipment handles",
]

INVENTORY_ITEMS = [
    "All-purpose flour",
    "Sugar",
    "Butter",
    "Eggs",
    "Yeast",
    "Vanilla extract",
    "Chocolate chips",
    "Baking powder",
]


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
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

        CREATE TABLE IF NOT EXISTS inventory_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            count INTEGER NOT NULL,
            logged_by TEXT,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cleaning_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT NOT NULL,
            action TEXT NOT NULL,
            logged_by TEXT,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
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
    """)

    # Seed data if checklist is empty
    cursor.execute("SELECT COUNT(*) FROM checklist_items")
    if cursor.fetchone()[0] == 0:
        for item in SANITATION_ITEMS:
            cursor.execute(
                "INSERT INTO checklist_items (checklist_type, item_name) VALUES (?, ?)",
                ("sanitation", item),
            )
        for item in INVENTORY_ITEMS:
            cursor.execute(
                "INSERT INTO checklist_items (checklist_type, item_name) VALUES (?, ?)",
                ("inventory", item),
            )

    conn.commit()
    conn.close()


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


def add_inventory_count(item_name: str, count: int, staff_id: str | None = None) -> dict:
    """Log an inventory count for an item. Requires staff_id to be set."""
    if not staff_id:
        return {"status": "error", "message": "Cannot log inventory without a staff member identified. Please scan your NFC card first."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO inventory_log (item_name, count, logged_by) VALUES (?, ?, ?)",
        (item_name, count, staff_id),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "item_name": item_name, "count": count, "logged_by": staff_id}


def log_cleaning(area: str, action: str, staff_id: str | None = None) -> dict:
    """Log a cleaning activity. Requires staff_id to be set."""
    if not staff_id:
        return {"status": "error", "message": "Cannot log cleaning without a staff member identified. Please scan your NFC card first."}

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cleaning_log (area, action, logged_by) VALUES (?, ?, ?)",
        (area, action, staff_id),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "area": area, "action": action, "logged_by": staff_id}


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


def reset_checklists() -> dict:
    """Reset all checklist items to incomplete for a new day."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE checklist_items SET is_complete = 0, completed_at = NULL, notes = NULL")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "All checklists reset for a new day"}
