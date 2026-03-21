"""
Interactive text chat with the bakery assistant — no voice, no backend server.

Uses Gemini text API with the same tools/system prompt as production.
After each exchange you can type:
  /db       — dump current database state (checklists, cleaning, materials, tickets)
  /logs     — show recent audit log entries
  /reset    — reset checklists to incomplete
  /quit     — exit

Uses a separate test database (test_bakery.db) so your real data is untouched.

Run:  python test_chat.py
      python test_chat.py --use-real-db   (to use the real bakery.db instead)
"""

import argparse
import asyncio
import json
import os
import sqlite3
import sys
from datetime import date
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv

load_dotenv()

# ── Parse args ───────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Interactive bakery assistant text chat")
parser.add_argument("--staff-id", default="test-user", help="Staff ID (default: test-user)")
parser.add_argument("--use-real-db", action="store_true", help="Use the real bakery.db instead of a test copy")
args = parser.parse_args()

# ── Patch DB path for test isolation ─────────────────────────
if not args.use_real_db:
    TEST_DB = Path(__file__).parent / "test_bakery.db"
    # Monkey-patch before importing src modules
    import src.config
    src.config.DB_PATH = TEST_DB
    print(f"[setup] Using test database: {TEST_DB}")
else:
    print("[setup] Using real database: bakery.db")

from src import db
from src.config import SYSTEM_INSTRUCTION
from src.tool_handlers import handle_tool_call
from src.tools import all_tools

# ── Init ─────────────────────────────────────────────────────
db.init_db()

STAFF_ID = args.staff_id
TEXT_MODEL = "gemini-2.5-flash"

# ── Gemini client setup ──────────────────────────────────────
from google import genai

client = genai.Client()


def dump_db():
    """Print a formatted snapshot of the database."""
    conn = db.get_connection()
    cur = conn.cursor()

    print("\n" + "=" * 60)
    print("  DATABASE STATE")
    print("=" * 60)

    # Sanitation checklist
    print("\n-- Sanitation Checklist --")
    cur.execute("SELECT id, item_name, is_complete, completed_by, notes FROM checklist_items WHERE checklist_type='sanitation'")
    for row in cur.fetchall():
        status = "DONE" if row["is_complete"] else "    "
        by = f" (by {row['completed_by']})" if row["completed_by"] else ""
        notes = f" [{row['notes']}]" if row["notes"] else ""
        print(f"  [{status}] #{row['id']} {row['item_name']}{by}{notes}")

    # Materials
    print("\n-- Materials --")
    cur.execute("SELECT id, item_name, count, updated_at, updated_by FROM materials ORDER BY item_name")
    for row in cur.fetchall():
        by = f" (by {row['updated_by']})" if row["updated_by"] else ""
        at = f" [{row['updated_at']}]" if row["updated_at"] else ""
        print(f"  #{row['id']} {row['item_name']}: {row['count']}{by}{at}")

    # Cleaning tasks
    today = date.today().isoformat()
    print(f"\n-- Cleaning Tasks ({today}) --")
    cur.execute("SELECT id, area, action, is_complete, completed_by, notes FROM cleaning_tasks WHERE task_date=?", (today,))
    rows = cur.fetchall()
    if rows:
        for row in rows:
            status = "DONE" if row["is_complete"] else "    "
            by = f" (by {row['completed_by']})" if row["completed_by"] else ""
            notes = f" [{row['notes']}]" if row["notes"] else ""
            print(f"  [{status}] #{row['id']} {row['area']}: {row['action']}{by}{notes}")
    else:
        print("  (no tasks for today yet)")

    # Tickets
    print("\n-- Open Tickets --")
    cur.execute("SELECT id, title, category, urgency, raised_by, created_at FROM tickets WHERE status='open' ORDER BY CASE urgency WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 WHEN 'low' THEN 3 END")
    rows = cur.fetchall()
    if rows:
        for row in rows:
            print(f"  [{row['urgency'].upper()}] #{row['id']} {row['title']} ({row['category']}) — by {row['raised_by']}, {row['created_at']}")
    else:
        print("  (no open tickets)")

    print("=" * 60 + "\n")
    conn.close()


def dump_logs(limit=10):
    """Print recent audit log entries."""
    entries = db.get_audit_log(limit=limit)
    print("\n" + "=" * 60)
    print(f"  AUDIT LOG (last {limit} entries)")
    print("=" * 60)
    if not entries:
        print("  (empty)")
    for e in reversed(entries):  # show oldest first
        print(f"\n  [{e['created_at']}] staff={e['staff_id']}")
        if e["tool_name"]:
            print(f"    tool: {e['tool_name']}({e['tool_args']})")
            print(f"    result: {e['tool_result']}")
        if e["user_message"]:
            print(f"    user: {e['user_message']}")
        if e["ai_response"]:
            resp = e["ai_response"][:200] + "..." if len(e["ai_response"] or "") > 200 else e["ai_response"]
            print(f"    ai: {resp}")
    print("=" * 60 + "\n")


async def chat_loop():
    """Main interactive chat loop."""
    print("\n" + "=" * 60)
    print("  BAKERY ASSISTANT — Text Chat Test")
    print(f"  Staff: {STAFF_ID} | Model: {TEXT_MODEL}")
    print("  Commands: /db /logs /reset /quit")
    print("=" * 60 + "\n")

    # Build chat with tools
    chat = client.chats.create(
        model=TEXT_MODEL,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "tools": [all_tools],
        },
    )

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not user_input:
            continue

        # Handle slash commands
        if user_input.lower() == "/quit":
            print("Bye!")
            break
        if user_input.lower() == "/db":
            dump_db()
            continue
        if user_input.lower() == "/logs":
            dump_logs()
            continue
        if user_input.lower() == "/reset":
            res = db.reset_checklists()
            print(f"  -> {res}")
            continue

        # Send to Gemini
        response = chat.send_message(user_input)

        # Process tool calls in a loop (Gemini may chain multiple)
        while response.function_calls:
            tool_results = []
            for fc in response.function_calls:
                fn_name = fc.name
                fn_args = dict(fc.args) if fc.args else {}

                print(f"\n  [Tool Call] {fn_name}({json.dumps(fn_args, ensure_ascii=False)})")

                result = await handle_tool_call(
                    function_name=fn_name,
                    args=fn_args,
                    staff_id=STAFF_ID,
                    user_message=user_input,
                    ai_response=None,
                )
                print(f"  [Tool Result] {json.dumps(result, ensure_ascii=False)}")

                tool_results.append(
                    genai.types.FunctionResponse(
                        name=fn_name,
                        response=result,
                    )
                )

            # Send tool results back to Gemini
            response = chat.send_message(tool_results)

        # Print final text response
        if response.text:
            # Log the conversation
            db.log_conversation(
                staff_id=STAFF_ID,
                user_message=user_input,
                ai_response=response.text,
            )
            print(f"\nAssistant: {response.text}")
        print()


if __name__ == "__main__":
    asyncio.run(chat_loop())
