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
            notes TEXT
        );

        CREATE TABLE IF NOT EXISTS inventory_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            count INTEGER NOT NULL,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cleaning_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT NOT NULL,
            action TEXT NOT NULL,
            logged_at TEXT DEFAULT CURRENT_TIMESTAMP
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


def mark_item_complete(item_id: int, notes: str | None = None) -> dict:
    """Mark a checklist item as complete."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE checklist_items SET is_complete = 1, completed_at = ?, notes = ? WHERE id = ?",
        (datetime.now().isoformat(), notes, item_id),
    )
    conn.commit()

    # Return the item info
    cursor.execute("SELECT item_name, checklist_type FROM checklist_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "item_name": row["item_name"], "checklist_type": row["checklist_type"]}
    return {"status": "error", "message": f"Item {item_id} not found"}


def mark_item_incomplete(item_id: int) -> dict:
    """Mark a checklist item as incomplete."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE checklist_items SET is_complete = 0, completed_at = NULL, notes = NULL WHERE id = ?",
        (item_id,),
    )
    conn.commit()

    cursor.execute("SELECT item_name FROM checklist_items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {"status": "success", "item_name": row["item_name"]}
    return {"status": "error", "message": f"Item {item_id} not found"}


def add_inventory_count(item_name: str, count: int) -> dict:
    """Log an inventory count for an item."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO inventory_log (item_name, count) VALUES (?, ?)",
        (item_name, count),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "item_name": item_name, "count": count}


def log_cleaning(area: str, action: str) -> dict:
    """Log a cleaning activity."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO cleaning_log (area, action) VALUES (?, ?)",
        (area, action),
    )
    conn.commit()
    conn.close()
    return {"status": "success", "area": area, "action": action}


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


def reset_checklists() -> dict:
    """Reset all checklist items to incomplete for a new day."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE checklist_items SET is_complete = 0, completed_at = NULL, notes = NULL")
    conn.commit()
    conn.close()
    return {"status": "success", "message": "All checklists reset for a new day"}
