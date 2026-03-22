"""
Local test script for bakery tools — no backend/API/Gemini needed.

Tests cleaning tasks, inventory logging, ticket raising, and checklist operations
against a temporary SQLite database.

Run:  python test_tools.py
"""

import sqlite3
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Patch DB_PATH before importing anything from src
_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
TEST_DB = Path(_tmp.name)
_tmp.close()

patch("src.config.DB_PATH", TEST_DB).start()

from src import db  # noqa: E402

PASS = 0
FAIL = 0


def ok(label: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS  {label}")
    else:
        FAIL += 1
        print(f"  FAIL  {label}  — {detail}")


def section(title: str):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")


# ── Setup ────────────────────────────────────────────────────
db.init_db()

STAFF = "test-user"

# ─────────────────────────────────────────────────────────────
section("CHECKLIST — sanitation")
# ─────────────────────────────────────────────────────────────

# All items start incomplete
san_items = db.get_incomplete_items("sanitation")
ok("sanitation has 8 items", len(san_items) == 8, f"got {len(san_items)}")

# Mark first sanitation item complete
first = san_items[0]
res = db.mark_item_complete(first["id"], notes="sparkling clean", staff_id=STAFF)
ok("mark_item_complete succeeds", res["status"] == "success", str(res))
ok("completed_by recorded", res["completed_by"] == STAFF)

# Remaining should be 7
remaining = db.get_incomplete_items("sanitation")
ok("remaining sanitation = 7", len(remaining) == 7, f"got {len(remaining)}")

# Summary check
summary = db.get_checklist_summary("sanitation")
ok("summary: 1 completed", summary["completed"] == 1, str(summary))
ok("summary: 7 remaining", summary["remaining"] == 7, str(summary))

# Mark incomplete again
res = db.mark_item_incomplete(first["id"], staff_id=STAFF)
ok("mark_item_incomplete succeeds", res["status"] == "success", str(res))
remaining = db.get_incomplete_items("sanitation")
ok("back to 8 incomplete", len(remaining) == 8, f"got {len(remaining)}")

# Reject without staff_id
res = db.mark_item_complete(first["id"], staff_id=None)
ok("rejected without staff_id", res["status"] == "error", str(res))

# ─────────────────────────────────────────────────────────────
section("CLEANING TASKS")
# ─────────────────────────────────────────────────────────────

tasks = db.get_cleaning_tasks()
ok("10 cleaning tasks created", len(tasks) == 10, f"got {len(tasks)}")
ok("all start incomplete", all(not t["is_complete"] for t in tasks))

incomplete = db.get_incomplete_cleaning_tasks()
ok("10 incomplete tasks", len(incomplete) == 10, f"got {len(incomplete)}")

# Mark first two complete
t1, t2 = tasks[0], tasks[1]
res1 = db.mark_cleaning_complete(t1["id"], notes="done by morning shift", staff_id=STAFF)
ok("cleaning complete #1", res1["status"] == "success", str(res1))
ok("area returned", res1["area"] == t1["area"])

res2 = db.mark_cleaning_complete(t2["id"], staff_id=STAFF)
ok("cleaning complete #2", res2["status"] == "success", str(res2))

# Summary
cs = db.get_cleaning_summary()
ok("cleaning summary: 2 done", cs["completed"] == 2, str(cs))
ok("cleaning summary: 8 remaining", cs["remaining"] == 8, str(cs))
ok("all_done is False", cs["all_done"] is False)

# Incomplete list
inc = db.get_incomplete_cleaning_tasks()
ok("8 incomplete after marking 2", len(inc) == 8, f"got {len(inc)}")

# Undo one
res = db.mark_cleaning_incomplete(t1["id"], staff_id=STAFF)
ok("undo cleaning complete", res["status"] == "success", str(res))
inc2 = db.get_incomplete_cleaning_tasks()
ok("9 incomplete after undo", len(inc2) == 9, f"got {len(inc2)}")

# Mark all complete
for t in db.get_incomplete_cleaning_tasks():
    db.mark_cleaning_complete(t["id"], staff_id=STAFF)
cs_all = db.get_cleaning_summary()
ok("all_done is True when all complete", cs_all["all_done"] is True)

# Reject without staff_id
res = db.mark_cleaning_complete(t1["id"], staff_id=None)
ok("cleaning rejected without staff_id", res["status"] == "error")

# ─────────────────────────────────────────────────────────────
section("MATERIALS")
# ─────────────────────────────────────────────────────────────

# Should start with 8 seeded materials
materials = db.get_materials()
ok("8 materials seeded", len(materials) == 8, f"got {len(materials)}")

# Adjust a material count (relative delta)
# First get the current flour count
flour_before = [m for m in materials if m["item_name"] == "Weizenmehl"][0]["count"]
res = db.adjust_material_count("Weizenmehl", 25, staff_id=STAFF)
ok("adjust flour count", res["status"] == "success", str(res))
ok("new_count recorded", res["new_count"] == flour_before + 25)
ok("updated_by recorded", res["updated_by"] == STAFF)

res = db.adjust_material_count("Zucker", 10, staff_id=STAFF)
ok("adjust sugar count", res["status"] == "success")

# Adjust same item again (should add to current, not overwrite)
res = db.adjust_material_count("Weizenmehl", -1, staff_id=STAFF)
ok("second flour adjust", res["status"] == "success")

# Verify via raw SQL that Weizenmehl has count = original + 25 - 1
conn = db.get_connection()
cur = conn.cursor()
cur.execute("SELECT count FROM materials WHERE item_name = 'Weizenmehl'")
count = cur.fetchone()[0]
conn.close()
ok("flour count is original+24 (adjusted)", count == flour_before + 24, f"got {count}")

# Create a new material that wasn't seeded
res = db.adjust_material_count("Sahne", 5, staff_id=STAFF)
ok("new material created", res["status"] == "success")
materials = db.get_materials()
ok("9 materials after adding new one", len(materials) == 9, f"got {len(materials)}")

# Reject without staff_id
res = db.adjust_material_count("Butter", 5, staff_id=None)
ok("material rejected without staff_id", res["status"] == "error")

# Stale materials — all seeded items that weren't updated should be stale
# (updated_at defaults to CURRENT_TIMESTAMP on insert, so freshly seeded items
#  won't be stale yet — but we can check the function works)
stale = db.get_stale_materials(days=0)  # 0 days = everything not updated "just now"
ok("get_stale_materials returns list", isinstance(stale, list))

# ─────────────────────────────────────────────────────────────
section("RAISE TICKET")
# ─────────────────────────────────────────────────────────────

res = db.raise_ticket(
    title="Ofen 2 defekt",
    description="Ofen 2 heizt nicht mehr auf Temperatur, bleibt bei 150°C stehen",
    category="machine_breakdown",
    urgency="urgent",
    raised_by=STAFF,
)
ok("raise urgent ticket", res["status"] == "success", str(res))
ok("ticket_id returned", "ticket_id" in res)
ok("urgency is urgent", res["urgency"] == "urgent")

res2 = db.raise_ticket(
    title="Vanilleextrakt fast leer",
    description="Nur noch 1 Flasche Vanilleextrakt im Lager",
    category="stock_shortage",
    urgency="normal",
    raised_by=STAFF,
)
ok("raise normal ticket", res2["status"] == "success")

res3 = db.raise_ticket(
    title="Licht im Lager flackert",
    description="Die Neonröhre im Lagerraum flackert seit gestern",
    category="maintenance",
    urgency="low",
    raised_by=STAFF,
)
ok("raise low ticket", res3["status"] == "success")

# Get open tickets — should be sorted by urgency
tickets = db.get_open_tickets()
ok("3 open tickets", len(tickets) == 3, f"got {len(tickets)}")
ok("urgent ticket first", tickets[0]["urgency"] == "urgent")
ok("low ticket last", tickets[-1]["urgency"] == "low")
ok("title preserved", tickets[0]["title"] == "Ofen 2 defekt")
ok("category preserved", tickets[0]["category"] == "machine_breakdown")

# ─────────────────────────────────────────────────────────────
section("AUDIT LOG")
# ─────────────────────────────────────────────────────────────

log = db.log_audit(
    staff_id=STAFF,
    tool_name="mark_item_complete",
    tool_args='{"item_id": 1}',
    tool_result='{"status": "success"}',
)
ok("audit log entry created", log["status"] == "success")

entries = db.get_audit_log(limit=5)
ok("audit entries returned", len(entries) > 0)
ok("audit has tool_name", entries[0]["tool_name"] == "mark_item_complete")

# Filter by staff
filtered = db.get_audit_log(limit=50, staff_id=STAFF)
ok("filtered by staff_id", all(e["staff_id"] == STAFF for e in filtered))

# ─────────────────────────────────────────────────────────────
section("RESET CHECKLISTS")
# ─────────────────────────────────────────────────────────────

# Complete an item first
db.mark_item_complete(san_items[0]["id"], staff_id=STAFF)
s = db.get_checklist_summary("sanitation")
ok("1 completed before reset", s["completed"] == 1)

res = db.reset_checklists()
ok("reset succeeds", res["status"] == "success")
s2 = db.get_checklist_summary("sanitation")
ok("0 completed after reset", s2["completed"] == 0)

# ─────────────────────────────────────────────────────────────
# Cleanup
# ─────────────────────────────────────────────────────────────
TEST_DB.unlink(missing_ok=True)

print(f"\n{'='*60}")
print(f"  RESULTS: {PASS} passed, {FAIL} failed")
print(f"{'='*60}")
sys.exit(1 if FAIL else 0)
