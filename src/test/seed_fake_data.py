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


EMPLOYEE_NAMES = [
    "Anna Müller",
    "Jan Schmidt",
    "Lisa Weber",
    "Tom Fischer",
    "Sarah Becker",
    "Marco Schulz",
    "Julia Meier",
]

SHIFT_PATTERNS = [
    ("04:00", "12:00"),  # Frühschicht
    ("05:00", "13:00"),  # Frühschicht
    ("06:00", "14:00"),  # Normalschicht
    ("08:00", "16:00"),  # Tagschicht
    ("10:00", "18:00"),  # Spätschicht
    ("12:00", "20:00"),  # Spätschicht
]

BAKED_GOODS = [
    {
        "name": "Croissant",
        "price": 1.80,
        "recipe": "Blätterteig herstellen: Mehl, Wasser, Salz, Hefe und Butter zu einem Teig verarbeiten. "
                  "Mehrfach falten und kühlen. In Dreiecke schneiden, aufrollen. "
                  "Bei 200°C ca. 15 Minuten goldbraun backen.",
        "materials": [("Weizenmehl", "500g"), ("Butter", "250g"), ("Hefe", "20g"), ("Zucker", "30g"), ("Salz", "10g"), ("Eier", "1 Stück")],
    },
    {
        "name": "Vollkornbrot",
        "price": 3.50,
        "recipe": "Roggenmehl, Dinkelmehl, Hefe, Salz und Wasser vermengen. "
                  "Teig 1 Stunde gehen lassen. In Kastenform geben. "
                  "Bei 220°C 45 Minuten backen.",
        "materials": [("Roggenmehl", "400g"), ("Dinkelmehl", "200g"), ("Hefe", "25g"), ("Salz", "15g"), ("Leinsamen", "30g"), ("Kürbiskerne", "20g")],
    },
    {
        "name": "Schokoladenkuchen",
        "price": 2.90,
        "recipe": "Butter und Zucker cremig rühren. Eier einzeln unterrühren. "
                  "Mehl, Backpulver und Schokoladenstückchen unterheben. "
                  "Bei 180°C 35 Minuten backen. Abkühlen lassen und mit Puderzucker bestäuben.",
        "materials": [("Weizenmehl", "300g"), ("Zucker", "200g"), ("Butter", "150g"), ("Eier", "4 Stück"), ("Schokoladenstückchen", "200g"), ("Backpulver", "10g"), ("Puderzucker", "30g")],
    },
    {
        "name": "Brezeln",
        "price": 1.20,
        "recipe": "Mehl, Hefe, Salz und Wasser zu einem glatten Teig kneten. "
                  "Teiglinge formen und in Natronlauge tauchen. "
                  "Mit grobem Salz bestreuen. Bei 220°C 12-15 Minuten backen.",
        "materials": [("Weizenmehl", "500g"), ("Hefe", "15g"), ("Salz", "20g"), ("Butter", "30g")],
    },
    {
        "name": "Mohnkuchen",
        "price": 2.50,
        "recipe": "Hefeteig herstellen und ausrollen. Mohnfüllung aus gemahlenem Mohn, "
                  "Milch, Zucker und Rosinen zubereiten. Auf Teig verteilen. "
                  "Bei 180°C 40 Minuten backen.",
        "materials": [("Weizenmehl", "400g"), ("Mohn", "200g"), ("Zucker", "150g"), ("Milch", "200ml"), ("Butter", "100g"), ("Rosinen", "50g"), ("Hefe", "20g")],
    },
    {
        "name": "Mandelkuchen",
        "price": 3.20,
        "recipe": "Butter und Zucker aufschlagen. Eier unterrühren. Mehl und gehobelte Mandeln unterheben. "
                  "Mit Marzipanrohmasse verfeinern. Bei 175°C 45 Minuten backen.",
        "materials": [("Weizenmehl", "250g"), ("Mandeln gehobelt", "150g"), ("Marzipanrohmasse", "100g"), ("Zucker", "180g"), ("Butter", "200g"), ("Eier", "4 Stück")],
    },
    {
        "name": "Sesambrötchen",
        "price": 0.80,
        "recipe": "Mehl, Hefe, Salz und Wasser verkneten. 30 Minuten gehen lassen. "
                  "Brötchen formen, mit Wasser bestreichen und Sesam bestreuen. "
                  "Bei 230°C 18 Minuten backen.",
        "materials": [("Weizenmehl", "500g"), ("Hefe", "20g"), ("Salz", "10g"), ("Sesam", "40g"), ("Sonnenblumenöl", "20ml")],
    },
    {
        "name": "Vanillekipferl",
        "price": 4.50,
        "recipe": "Mehl, Butter, Zucker und gemahlene Haselnüsse zu einem Mürbteig verarbeiten. "
                  "Kipferl formen. Bei 180°C 10-12 Minuten backen. "
                  "Warm in Vanillezucker wälzen.",
        "materials": [("Weizenmehl", "300g"), ("Butter", "200g"), ("Zucker", "80g"), ("Haselnüsse gemahlen", "100g"), ("Vanilleextrakt", "10ml"), ("Puderzucker", "50g")],
    },
]

RAW_PURCHASE_TEMPLATES = [
    ("Weizenmehl", "25kg", 18.50),
    ("Weizenmehl", "50kg", 35.00),
    ("Roggenmehl", "25kg", 22.00),
    ("Dinkelmehl", "10kg", 14.00),
    ("Zucker", "25kg", 19.00),
    ("Puderzucker", "5kg", 6.50),
    ("Butter", "10kg", 45.00),
    ("Butter", "20kg", 88.00),
    ("Eier", "360 Stück", 72.00),
    ("Eier", "180 Stück", 38.00),
    ("Hefe", "5kg", 12.00),
    ("Vanilleextrakt", "1L", 28.00),
    ("Schokoladenstückchen", "5kg", 32.00),
    ("Backpulver", "2kg", 8.00),
    ("Sahne", "10L", 24.00),
    ("Milch", "20L", 16.00),
    ("Marzipanrohmasse", "5kg", 42.00),
    ("Mandeln gehobelt", "2kg", 24.00),
    ("Haselnüsse gemahlen", "2kg", 22.00),
    ("Rosinen", "2kg", 9.00),
    ("Mohn", "1kg", 11.00),
    ("Sesam", "1kg", 7.00),
    ("Salz", "10kg", 4.00),
    ("Sonnenblumenöl", "5L", 8.50),
]


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


def seed_schedules(cursor: sqlite3.Cursor) -> None:
    """Seed schedules for current week + next week (Mon-Sat)."""
    total = 0
    # Find Monday of the current week
    today = TODAY.date()
    monday = today - timedelta(days=today.weekday())

    for week_offset in range(3):  # previous week, this week, next week
        week_start = monday + timedelta(weeks=week_offset - 1)
        for day_offset in range(6):  # Mon-Sat (bakery closed Sunday)
            day = week_start + timedelta(days=day_offset)
            day_str = day.isoformat()

            # Schedule 3-5 employees per day
            n_employees = random.randint(3, 5)
            day_employees = random.sample(EMPLOYEE_NAMES, n_employees)

            # One person gets cleaning duty
            cleaning_person = random.choice(day_employees)

            for emp in day_employees:
                shift = random.choice(SHIFT_PATTERNS)
                cleaning = 1 if emp == cleaning_person else 0
                cursor.execute(
                    "INSERT INTO schedules (employee_name, schedule_date, start_time, end_time, cleaning) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (emp, day_str, shift[0], shift[1], cleaning),
                )
                total += 1

    print(f"  schedules: {total} Einträge eingefügt (3 Wochen)")


def seed_baked_goods(cursor: sqlite3.Cursor) -> None:
    """Seed baked goods with recipes and material links."""
    # First build a material name → id map
    cursor.execute("SELECT id, item_name FROM materials")
    mat_map = {row[1]: row[0] for row in cursor.fetchall()}

    for bg in BAKED_GOODS:
        cursor.execute(
            "INSERT OR IGNORE INTO baked_goods (name, price, recipe) VALUES (?, ?, ?)",
            (bg["name"], bg["price"], bg["recipe"]),
        )
        cursor.execute("SELECT id FROM baked_goods WHERE name = ?", (bg["name"],))
        product_id = cursor.fetchone()[0]

        for mat_name, amount in bg["materials"]:
            if mat_name in mat_map:
                cursor.execute(
                    "INSERT OR IGNORE INTO product_materials (product_id, material_id, amount) "
                    "VALUES (?, ?, ?)",
                    (product_id, mat_map[mat_name], amount),
                )

    print(f"  baked_goods: {len(BAKED_GOODS)} Produkte mit Rezepten eingefügt")


def seed_raw_purchases(cursor: sqlite3.Cursor) -> None:
    """Seed raw material purchases over the past 30 days."""
    cursor.execute("SELECT id, item_name FROM materials")
    mat_map = {row[1]: row[0] for row in cursor.fetchall()}

    total = 0
    for days_back in range(30, -1, -1):
        # 0-3 purchases per day
        n_purchases = random.randint(0, 3)
        purchase_date = (TODAY - timedelta(days=days_back)).date().isoformat()

        for _ in range(n_purchases):
            template = random.choice(RAW_PURCHASE_TEMPLATES)
            mat_name, amount, base_price = template
            if mat_name not in mat_map:
                continue
            # Add some price variation (±15%)
            price = round(base_price * random.uniform(0.85, 1.15), 2)
            cursor.execute(
                "INSERT INTO raw_purchases (material_id, amount, price, purchase_date) "
                "VALUES (?, ?, ?, ?)",
                (mat_map[mat_name], amount, price, purchase_date),
            )
            total += 1

    print(f"  raw_purchases: {total} Einträge eingefügt (30 Tage)")


def seed_cooking_plans(cursor: sqlite3.Cursor) -> None:
    """Seed cooking plans for the past 2 weeks + today."""
    cursor.execute("SELECT id, name FROM baked_goods")
    products = cursor.fetchall()
    if not products:
        print("  cooking_plans: Keine Produkte vorhanden, übersprungen")
        return

    total = 0
    for days_back in range(14, -1, -1):
        plan_date = (TODAY - timedelta(days=days_back)).date().isoformat()
        # Plan 3-6 products per day
        n_products = random.randint(3, min(6, len(products)))
        day_products = random.sample(products, n_products)

        for prod_id, prod_name in day_products:
            # Realistic quantities
            if prod_name in ("Croissant", "Brezeln", "Sesambrötchen"):
                qty = random.randint(50, 150)
            elif prod_name in ("Vanillekipferl",):
                qty = random.randint(80, 200)
            else:
                qty = random.randint(10, 40)

            cursor.execute(
                "INSERT OR IGNORE INTO cooking_plans (plan_date, product_id, quantity) "
                "VALUES (?, ?, ?)",
                (plan_date, prod_id, qty),
            )
            total += 1

    print(f"  cooking_plans: {total} Einträge eingefügt (15 Tage)")


def main() -> None:
    reset = "--reset" in sys.argv

    print(f"Datenbank: {DB_PATH}")
    print(f"Datum: {TODAY_DATE}")
    print()

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    create_tables(cursor)

    cursor.execute("PRAGMA foreign_keys = ON")

    if reset:
        print("Lösche vorhandene Daten ...")
        for table in [
            "cooking_plans", "raw_purchases", "product_materials", "baked_goods",
            "schedules", "checklist_items", "materials", "cleaning_tasks",
            "tickets", "audit_log",
        ]:
            cursor.execute(f"DELETE FROM {table}")
        print()

    print("Füge Fake-Daten ein ...")
    seed_checklist_items(cursor)
    seed_materials(cursor)
    seed_cleaning_tasks(cursor)
    seed_tickets(cursor)
    seed_audit_log(cursor)
    seed_schedules(cursor)
    seed_baked_goods(cursor)
    seed_raw_purchases(cursor)
    seed_cooking_plans(cursor)

    conn.commit()
    conn.close()
    print()
    print("Fertig! Datenbank wurde mit Testdaten befüllt.")


if __name__ == "__main__":
    main()
