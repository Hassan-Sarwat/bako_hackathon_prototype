"""SQLite database setup, schema, seed data, and query helpers."""

import sqlite3
from datetime import date, datetime
from pathlib import Path

from .config import DB_PATH

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

INVENTORY_ITEMS = [
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
