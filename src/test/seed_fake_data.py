"""Populate the bakery database with realistic fake data in German.

Usage:
    python seed_fake_data.py          # Seeds bakery.db (creates if needed)
    python seed_fake_data.py --reset  # Wipes all data first, then seeds
"""

import json
import random
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = Path(__file__).parent.parent.parent / "bakery.db"

# ---------------------------------------------------------------------------
# Reference date: 21.03.2026
# ---------------------------------------------------------------------------
TODAY = datetime(2026, 3, 21)
TODAY_DATE = TODAY.date().isoformat()  # "2026-03-21"

# ---------------------------------------------------------------------------
# Staff members
# ---------------------------------------------------------------------------
STAFF = [
    "mueller_anna",
    "schmidt_jan",
    "weber_lisa",
    "fischer_tom",
    "becker_sarah",
]

# ---------------------------------------------------------------------------
# Sanitation checklist items (the same 8 the app uses + a few extras)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Materials with realistic bakery counts (in kg / Stück / Liter / Packungen)
# ---------------------------------------------------------------------------
MATERIALS = [
    ("Weizenmehl", random.randint(80, 200)),
    ("Roggenmehl", random.randint(30, 80)),
    ("Dinkelmehl", random.randint(20, 60)),
    ("Zucker", random.randint(40, 100)),
    ("Puderzucker", random.randint(10, 30)),
    ("Butter", random.randint(20, 60)),
    ("Eier", random.randint(100, 500)),
    ("Hefe", random.randint(5, 25)),
    ("Trockenhefe", random.randint(3, 15)),
    ("Vanilleextrakt", random.randint(2, 10)),
    ("Schokoladenstückchen", random.randint(5, 30)),
    ("Backpulver", random.randint(5, 20)),
    ("Sahne", random.randint(10, 40)),
    ("Milch", random.randint(20, 60)),
    ("Marzipanrohmasse", random.randint(5, 20)),
    ("Mandeln gehobelt", random.randint(3, 15)),
    ("Haselnüsse gemahlen", random.randint(3, 12)),
    ("Rosinen", random.randint(2, 10)),
    ("Zimt", random.randint(1, 5)),
    ("Salz", random.randint(5, 20)),
    ("Sonnenblumenöl", random.randint(5, 15)),
    ("Mohn", random.randint(2, 8)),
    ("Sesam", random.randint(2, 8)),
    ("Kürbiskerne", random.randint(2, 10)),
    ("Leinsamen", random.randint(2, 8)),
]

# ---------------------------------------------------------------------------
# Cleaning tasks (area + action)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Tickets – realistic bakery issues
# ---------------------------------------------------------------------------
TICKET_TEMPLATES = [
    {
        "title": "Knetmaschine macht laute Geräusche",
        "description": "Die große Knetmaschine (Modell KM-500) macht seit heute Morgen ein ungewöhnliches Schleifgeräusch beim Kneten von schwerem Teig. Funktioniert noch, aber klingt nicht normal.",
        "category": "machine_breakdown",
        "urgency": "high",
    },
    {
        "title": "Mehllieferung unvollständig",
        "description": "Die heutige Lieferung von Bäcker-Müller enthielt nur 15 Sack Weizenmehl statt der bestellten 25. Wir brauchen den Rest bis spätestens Donnerstag.",
        "category": "stock_shortage",
        "urgency": "urgent",
    },
    {
        "title": "Kühlraum-Temperatur schwankt",
        "description": "Der Kühlraum zeigt Temperaturschwankungen zwischen 2°C und 8°C. Sollte konstant bei 4°C liegen. Möglicherweise Dichtung defekt.",
        "category": "maintenance",
        "urgency": "urgent",
    },
    {
        "title": "Boden in der Backstube rutschig",
        "description": "Trotz regelmäßiger Reinigung bleibt der Boden im Bereich vor den Öfen rutschig. Eventuell muss die Anti-Rutsch-Beschichtung erneuert werden.",
        "category": "safety",
        "urgency": "high",
    },
    {
        "title": "Marco Schulz krank gemeldet",
        "description": "Marco hat sich für heute und morgen krank gemeldet. Wir brauchen Vertretung für die Frühschicht am Samstag.",
        "category": "employee_no_show",
        "urgency": "normal",
    },
    {
        "title": "Kassenbon-Drucker druckt nicht mehr",
        "description": "Der Bondrucker an Kasse 2 gibt seit gestern Nachmittag keine Bons mehr aus. Papier wurde schon gewechselt, Problem bleibt.",
        "category": "machine_breakdown",
        "urgency": "normal",
    },
    {
        "title": "Schimmelbefall im Lagerraum",
        "description": "An der hinteren Wand im trockenen Lagerraum wurde Schimmelbefall entdeckt. Betroffene Ware (3 Kartons Verpackungsmaterial) wurde entsorgt.",
        "category": "safety",
        "urgency": "urgent",
    },
    {
        "title": "Beleuchtung im Verkaufsraum flackert",
        "description": "Die LED-Leiste über der Brottheke flackert seit Montag. Stört Kunden und Mitarbeiter. Elektriker sollte kommen.",
        "category": "maintenance",
        "urgency": "low",
    },
    {
        "title": "Vanilleextrakt fast aufgebraucht",
        "description": "Nur noch 2 Flaschen Vanilleextrakt vorhanden. Bei aktuellem Verbrauch reicht das maximal bis Mittwoch. Bitte Nachbestellung aufgeben.",
        "category": "stock_shortage",
        "urgency": "normal",
    },
    {
        "title": "Neue Mitarbeiterin braucht Einweisung",
        "description": "Julia Meier fängt am Montag an. Sie braucht eine Einweisung in Hygiene-Vorschriften, Kassensystem und Backstuben-Abläufe.",
        "category": "other",
        "urgency": "low",
    },
]

# ---------------------------------------------------------------------------
# Audit log – sample voice interactions
# ---------------------------------------------------------------------------
AUDIT_INTERACTIONS = [
    {
        "user_message": "Wie viel Mehl haben wir noch?",
        "ai_response": "Ich schaue kurz nach. Wir haben aktuell 120 kg Weizenmehl, 45 kg Roggenmehl und 30 kg Dinkelmehl auf Lager.",
        "tool_name": "get_materials",
        "tool_args": "{}",
    },
    {
        "user_message": "Arbeitsflächen sind desinfiziert.",
        "ai_response": "Perfekt, ich habe 'Arbeitsflächen desinfizieren' als erledigt markiert. Danke!",
        "tool_name": "mark_checklist_item_complete",
        "tool_args": '{"item_id": 1, "notes": "Mit Desinfektionsmittel gereinigt"}',
    },
    {
        "user_message": "Was muss ich noch putzen?",
        "ai_response": "Du hast noch 6 offene Reinigungsaufgaben für heute: Öfen reinigen, Mischgeräte waschen, Vitrinen reinigen, Abflüsse desinfizieren, Lagerbereiche ordnen und Toiletten reinigen.",
        "tool_name": "get_incomplete_cleaning_tasks",
        "tool_args": "{}",
    },
    {
        "user_message": "Wir haben 350 Eier gezählt.",
        "ai_response": "Alles klar, ich habe den Eierbestand auf 350 Stück aktualisiert.",
        "tool_name": "update_material_count",
        "tool_args": '{"item_name": "Eier", "count": 350}',
    },
    {
        "user_message": "Die Knetmaschine macht komische Geräusche, kannst du ein Ticket erstellen?",
        "ai_response": "Ich habe ein Ticket mit hoher Priorität erstellt: 'Knetmaschine macht laute Geräusche'. Das wird an die Wartung weitergeleitet.",
        "tool_name": "raise_ticket",
        "tool_args": '{"title": "Knetmaschine macht laute Geräusche", "category": "machine_breakdown", "urgency": "high"}',
    },
    {
        "user_message": "Boden ist gewischt.",
        "ai_response": "Super, ich markiere 'Bäckereiboden kehren und wischen' als erledigt.",
        "tool_name": "mark_cleaning_complete",
        "tool_args": '{"task_id": 4, "notes": "Komplett gewischt und desinfiziert"}',
    },
    {
        "user_message": "Gibt es offene Tickets?",
        "ai_response": "Ja, es gibt aktuell 4 offene Tickets. Das dringendste ist die unvollständige Mehllieferung mit Priorität 'dringend'.",
        "tool_name": "get_open_tickets",
        "tool_args": "{}",
    },
    {
        "user_message": "Wie sieht die Checkliste aus?",
        "ai_response": "Von 8 Aufgaben auf der Hygiene-Checkliste sind 3 erledigt und 5 offen. Ihr seid bei 37% Fortschritt.",
        "tool_name": "get_checklist_summary",
        "tool_args": '{"checklist_type": "sanitation"}',
    },
    {
        "user_message": "Mülleimer sind geleert.",
        "ai_response": "Erledigt! 'Mülleimer leeren' ist jetzt abgehakt.",
        "tool_name": "mark_checklist_item_complete",
        "tool_args": '{"item_id": 7}',
    },
    {
        "user_message": "Wir brauchen mehr Hefe, bitte Ticket erstellen.",
        "ai_response": "Ticket erstellt: 'Hefe-Nachbestellung nötig' mit normaler Priorität unter Kategorie 'Materialmangel'.",
        "tool_name": "raise_ticket",
        "tool_args": '{"title": "Hefe-Nachbestellung nötig", "category": "stock_shortage", "urgency": "normal"}',
    },
]


def random_time(base_date: datetime, hour_range: tuple[int, int] = (5, 18)) -> str:
    """Generate a random ISO timestamp on base_date within working hours."""
    h = random.randint(*hour_range)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return base_date.replace(hour=h, minute=m, second=s).isoformat()


def create_tables(cursor: sqlite3.Cursor) -> None:
    """Ensure all tables exist (mirrors src/db.py schema)."""
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
    """)


def seed_checklist_items(cursor: sqlite3.Cursor) -> None:
    """Seed sanitation checklist – some completed, some not."""
    notes_options = [
        "Mit Desinfektionsmittel gereinigt",
        "Gründlich geputzt",
        "Wie vorgeschrieben erledigt",
        "Alles sauber",
        None,
    ]

    for item in SANITATION_ITEMS:
        completed = random.random() < 0.5
        staff = random.choice(STAFF) if completed else None
        completed_at = random_time(TODAY, (5, 14)) if completed else None
        notes = random.choice(notes_options) if completed else None
        cursor.execute(
            "INSERT INTO checklist_items (checklist_type, item_name, is_complete, completed_at, completed_by, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            ("sanitation", item, int(completed), completed_at, staff, notes),
        )
    print(f"  checklist_items: {len(SANITATION_ITEMS)} Einträge eingefügt")


def seed_materials(cursor: sqlite3.Cursor) -> None:
    """Seed materials with realistic counts and recent update timestamps."""
    for item_name, count in MATERIALS:
        days_ago = random.randint(0, 5)
        updated = TODAY - timedelta(days=days_ago)
        cursor.execute(
            "INSERT OR REPLACE INTO materials (item_name, count, updated_at, updated_by) "
            "VALUES (?, ?, ?, ?)",
            (item_name, count, random_time(updated), random.choice(STAFF)),
        )
    print(f"  materials: {len(MATERIALS)} Einträge eingefügt")


def seed_cleaning_tasks(cursor: sqlite3.Cursor) -> None:
    """Seed cleaning tasks for the past 7 days + today."""
    total = 0
    for days_back in range(7, -1, -1):  # 7 days ago → today
        task_date = (TODAY - timedelta(days=days_back)).date().isoformat()
        is_today = days_back == 0

        for task in CLEANING_TASKS:
            if is_today:
                # Today: ~40% done so far (it's mid-morning)
                completed = random.random() < 0.4
            else:
                # Past days: ~90% completed
                completed = random.random() < 0.9

            staff = random.choice(STAFF) if completed else None
            day_dt = TODAY - timedelta(days=days_back)
            completed_at = random_time(day_dt, (5, 16)) if completed else None
            notes = random.choice(["Erledigt", "Gründlich gemacht", "Alles sauber", None]) if completed else None

            cursor.execute(
                "INSERT INTO cleaning_tasks (task_date, area, action, is_complete, completed_at, completed_by, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (task_date, task["area"], task["action"], int(completed), completed_at, staff, notes),
            )
            total += 1
    print(f"  cleaning_tasks: {total} Einträge eingefügt (8 Tage)")


def seed_tickets(cursor: sqlite3.Cursor) -> None:
    """Seed tickets – mix of open and resolved."""
    for i, t in enumerate(TICKET_TEMPLATES):
        days_ago = random.randint(0, 10)
        created = TODAY - timedelta(days=days_ago)
        created_at = random_time(created, (6, 17))
        staff = random.choice(STAFF)

        # Older tickets are more likely resolved
        resolved = days_ago > 3 and random.random() < 0.7
        status = "resolved" if resolved else "open"
        resolved_at = random_time(created + timedelta(days=random.randint(1, 3)), (8, 17)) if resolved else None

        cursor.execute(
            "INSERT INTO tickets (title, description, category, urgency, status, raised_by, created_at, resolved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (t["title"], t["description"], t["category"], t["urgency"], status, staff, created_at, resolved_at),
        )
    print(f"  tickets: {len(TICKET_TEMPLATES)} Einträge eingefügt")


def seed_audit_log(cursor: sqlite3.Cursor) -> None:
    """Seed audit log with realistic voice interactions over the past few days."""
    total = 0
    for days_back in range(5, -1, -1):
        day_dt = TODAY - timedelta(days=days_back)
        # 5-15 interactions per day
        n_interactions = random.randint(5, 15)
        for _ in range(n_interactions):
            interaction = random.choice(AUDIT_INTERACTIONS)
            staff = random.choice(STAFF)
            cursor.execute(
                "INSERT INTO audit_log (staff_id, user_message, ai_model, ai_response, tool_name, tool_args, tool_result, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    staff,
                    interaction["user_message"],
                    "gemini-2.5-flash-preview-native-audio-dialog",
                    interaction["ai_response"],
                    interaction["tool_name"],
                    interaction["tool_args"],
                    json.dumps({"status": "success"}, ensure_ascii=False),
                    random_time(day_dt, (5, 18)),
                ),
            )
            total += 1
    print(f"  audit_log: {total} Einträge eingefügt (6 Tage)")


def main() -> None:
    reset = "--reset" in sys.argv

    print(f"Datenbank: {DB_PATH}")
    print(f"Datum: {TODAY_DATE}")
    print()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    create_tables(cursor)

    if reset:
        print("Lösche vorhandene Daten ...")
        for table in ["checklist_items", "materials", "cleaning_tasks", "tickets", "audit_log"]:
            cursor.execute(f"DELETE FROM {table}")
        print()

    print("Füge Fake-Daten ein ...")
    seed_checklist_items(cursor)
    seed_materials(cursor)
    seed_cleaning_tasks(cursor)
    seed_tickets(cursor)
    seed_audit_log(cursor)

    conn.commit()
    conn.close()
    print()
    print("Fertig! Datenbank wurde mit Testdaten befüllt.")


if __name__ == "__main__":
    main()
