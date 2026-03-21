"""Populate the bakery database with realistic fake data in German.

The seed data is designed so that purchases, cooking plans, and inventory
are internally consistent.  A few materials intentionally have suspicious
losses (>20 %) to make the Analysis tab demo meaningful.

Usage:
    python seed_fake_data.py          # Seeds bakery.db (creates if needed)
    python seed_fake_data.py --reset  # Wipes all data first, then seeds
"""

import json
import random
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

DB_PATH = Path(__file__).parent.parent.parent / "bakery.db"

# ---------------------------------------------------------------------------
# Amount parsing (duplicated from db.py so the seed script is standalone)
# ---------------------------------------------------------------------------
_AMOUNT_RE = re.compile(r'^([\d.,]+)\s*(.*)$')
_UNIT_TO_BASE = {
    'kg': ('g', 1000), 'g': ('g', 1),
    'l': ('ml', 1000), 'ml': ('ml', 1),
    'stück': ('Stuck', 1), 'stuck': ('Stuck', 1), 'stk': ('Stuck', 1),
}


def parse_amount(text: str) -> tuple[float, str]:
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
    key = unit.lower().rstrip('.')
    if key in _UNIT_TO_BASE:
        base_unit, factor = _UNIT_TO_BASE[key]
        return (value * factor, base_unit)
    return (value, unit)


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
# Materials – all raw materials the bakery uses
# ---------------------------------------------------------------------------
MATERIAL_NAMES = [
    "Weizenmehl",
    "Roggenmehl",
    "Dinkelmehl",
    "Zucker",
    "Puderzucker",
    "Butter",
    "Eier",
    "Hefe",
    "Trockenhefe",
    "Vanilleextrakt",
    "Schokoladenstückchen",
    "Backpulver",
    "Sahne",
    "Milch",
    "Marzipanrohmasse",
    "Mandeln gehobelt",
    "Haselnüsse gemahlen",
    "Rosinen",
    "Zimt",
    "Salz",
    "Sonnenblumenöl",
    "Mohn",
    "Sesam",
    "Kürbiskerne",
    "Leinsamen",
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

# ---------------------------------------------------------------------------
# Baked goods with per-unit recipe material amounts
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Purchase templates: what a single order looks like for each material
# (material_name, amount_text, base_price_for_that_amount)
# ---------------------------------------------------------------------------
RAW_PURCHASE_TEMPLATES = {
    "Weizenmehl":           ("25kg", 18.50),
    "Roggenmehl":           ("25kg", 22.00),
    "Dinkelmehl":           ("10kg", 14.00),
    "Zucker":               ("25kg", 19.00),
    "Puderzucker":          ("5kg",   6.50),
    "Butter":               ("10kg", 45.00),
    "Eier":                 ("360 Stück", 72.00),
    "Hefe":                 ("5kg",  12.00),
    "Trockenhefe":          ("1kg",   8.00),
    "Vanilleextrakt":       ("1L",   28.00),
    "Schokoladenstückchen": ("5kg",  32.00),
    "Backpulver":           ("2kg",   8.00),
    "Sahne":                ("10L",  24.00),
    "Milch":                ("20L",  16.00),
    "Marzipanrohmasse":     ("5kg",  42.00),
    "Mandeln gehobelt":     ("2kg",  24.00),
    "Haselnüsse gemahlen":  ("2kg",  22.00),
    "Rosinen":              ("2kg",   9.00),
    "Zimt":                 ("500g",  6.00),
    "Salz":                 ("10kg",  4.00),
    "Sonnenblumenöl":       ("5L",    8.50),
    "Mohn":                 ("1kg",  11.00),
    "Sesam":                ("1kg",   7.00),
    "Kürbiskerne":          ("2kg",  12.00),
    "Leinsamen":            ("2kg",   7.00),
}

# Materials that should show suspicious loss in the demo.
# Purchases cover usage normally, but inventory is mysteriously near zero.
# The analysis will flag: purchased - expected_usage = expected_remaining,
# but actual inventory ≈ 0  →  unaccounted_loss ≈ expected_remaining.
LOSS_MATERIALS = {
    "Butter",               # expensive — high monetary loss
    "Eier",                 # noticeable loss in pieces
    "Schokoladenstückchen", # significant shortage
    "Vanilleextrakt",       # very expensive per unit — small volume, big € impact
}

# All materials get purchases covering usage + 5-15% buffer
PURCHASE_COVER_RANGE = (1.05, 1.15)


# ═══════════════════════════════════════════════════════════════════════════
# Table creation
# ═══════════════════════════════════════════════════════════════════════════

def create_tables(cursor: sqlite3.Cursor) -> None:
    """Ensure all tables exist (mirrors src/db.py schema + new columns)."""
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
            amount_value REAL,
            amount_unit TEXT,
            FOREIGN KEY (product_id) REFERENCES baked_goods(id) ON DELETE CASCADE,
            FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE,
            UNIQUE(product_id, material_id)
        );
        CREATE TABLE IF NOT EXISTS raw_purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            amount TEXT NOT NULL,
            amount_value REAL,
            amount_unit TEXT,
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


# ═══════════════════════════════════════════════════════════════════════════
# Seed helpers (unchanged from before)
# ═══════════════════════════════════════════════════════════════════════════

def seed_checklist_items(cursor: sqlite3.Cursor) -> None:
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
    print(f"  checklist_items: {len(SANITATION_ITEMS)} rows")


def seed_materials(cursor: sqlite3.Cursor) -> None:
    """Seed materials – counts will be updated later once we know usage."""
    for item_name in MATERIAL_NAMES:
        days_ago = random.randint(0, 3)
        updated = TODAY - timedelta(days=days_ago)
        cursor.execute(
            "INSERT OR REPLACE INTO materials (item_name, count, updated_at, updated_by) "
            "VALUES (?, ?, ?, ?)",
            (item_name, 0, random_time(updated), random.choice(STAFF)),
        )
    print(f"  materials: {len(MATERIAL_NAMES)} rows")


def seed_cleaning_tasks(cursor: sqlite3.Cursor) -> None:
    total = 0
    for days_back in range(7, -1, -1):
        task_date = (TODAY - timedelta(days=days_back)).date().isoformat()
        is_today = days_back == 0
        for task in CLEANING_TASKS:
            completed = random.random() < (0.4 if is_today else 0.9)
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
    print(f"  cleaning_tasks: {total} rows (8 days)")


def seed_tickets(cursor: sqlite3.Cursor) -> None:
    for t in TICKET_TEMPLATES:
        days_ago = random.randint(0, 10)
        created = TODAY - timedelta(days=days_ago)
        created_at = random_time(created, (6, 17))
        staff = random.choice(STAFF)
        resolved = days_ago > 3 and random.random() < 0.7
        status = "resolved" if resolved else "open"
        resolved_at = random_time(created + timedelta(days=random.randint(1, 3)), (8, 17)) if resolved else None
        cursor.execute(
            "INSERT INTO tickets (title, description, category, urgency, status, raised_by, created_at, resolved_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (t["title"], t["description"], t["category"], t["urgency"], status, staff, created_at, resolved_at),
        )
    print(f"  tickets: {len(TICKET_TEMPLATES)} rows")


def seed_audit_log(cursor: sqlite3.Cursor) -> None:
    total = 0
    for days_back in range(5, -1, -1):
        day_dt = TODAY - timedelta(days=days_back)
        for _ in range(random.randint(5, 15)):
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
    print(f"  audit_log: {total} rows (6 days)")


def seed_schedules(cursor: sqlite3.Cursor) -> None:
    total = 0
    today = TODAY.date()
    monday = today - timedelta(days=today.weekday())
    for week_offset in range(3):
        week_start = monday + timedelta(weeks=week_offset - 1)
        for day_offset in range(6):
            day = week_start + timedelta(days=day_offset)
            day_str = day.isoformat()
            n_employees = random.randint(3, 5)
            day_employees = random.sample(EMPLOYEE_NAMES, n_employees)
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
    print(f"  schedules: {total} rows (3 weeks)")


# ═══════════════════════════════════════════════════════════════════════════
# Coherent baked goods → cooking plans → purchases → inventory
# ═══════════════════════════════════════════════════════════════════════════

def seed_baked_goods(cursor: sqlite3.Cursor) -> None:
    """Seed baked goods with recipes and material links (incl. parsed amounts)."""
    cursor.execute("SELECT id, item_name FROM materials")
    mat_map = {row[1]: row[0] for row in cursor.fetchall()}

    for bg in BAKED_GOODS:
        cursor.execute(
            "INSERT OR IGNORE INTO baked_goods (name, price, recipe) VALUES (?, ?, ?)",
            (bg["name"], bg["price"], bg["recipe"]),
        )
        cursor.execute("SELECT id FROM baked_goods WHERE name = ?", (bg["name"],))
        product_id = cursor.fetchone()[0]

        for mat_name, amount_text in bg["materials"]:
            if mat_name in mat_map:
                val, unit = parse_amount(amount_text)
                bval, bunit = to_base_units(val, unit)
                cursor.execute(
                    "INSERT OR IGNORE INTO product_materials "
                    "(product_id, material_id, amount, amount_value, amount_unit) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (product_id, mat_map[mat_name], amount_text, bval, bunit),
                )
    print(f"  baked_goods: {len(BAKED_GOODS)} products with recipes")


def seed_cooking_plans(cursor: sqlite3.Cursor) -> dict[str, float]:
    """Seed cooking plans for the past 2 weeks + today.

    Returns a dict of material_name → total expected usage in base units,
    so that purchases and inventory can be generated consistently.
    """
    cursor.execute("SELECT id, name FROM baked_goods")
    products = cursor.fetchall()
    if not products:
        print("  cooking_plans: no products, skipped")
        return {}

    # Build recipe lookup: product_id -> [(material_name, base_value, base_unit)]
    cursor.execute(
        "SELECT pm.product_id, m.item_name, pm.amount_value, pm.amount_unit "
        "FROM product_materials pm JOIN materials m ON pm.material_id = m.id"
    )
    recipe_map: dict[int, list[tuple[str, float, str]]] = {}
    for row in cursor.fetchall():
        pid = row[0]
        recipe_map.setdefault(pid, []).append((row[1], row[2] or 0.0, row[3] or ""))

    # Accumulate total expected usage per material
    total_usage: dict[str, float] = {}  # material_name -> base units
    total = 0

    for days_back in range(14, -1, -1):
        plan_date = (TODAY - timedelta(days=days_back)).date().isoformat()
        n_products = random.randint(3, min(6, len(products)))
        day_products = random.sample(products, n_products)

        for prod_id, prod_name in day_products:
            if prod_name in ("Croissant", "Brezeln", "Sesambrötchen"):
                qty = random.randint(50, 150)
            elif prod_name == "Vanillekipferl":
                qty = random.randint(80, 200)
            else:
                qty = random.randint(10, 40)

            cursor.execute(
                "INSERT OR IGNORE INTO cooking_plans (plan_date, product_id, quantity) "
                "VALUES (?, ?, ?)",
                (plan_date, prod_id, qty),
            )
            total += 1

            # Accumulate usage
            for mat_name, base_val, _ in recipe_map.get(prod_id, []):
                total_usage[mat_name] = total_usage.get(mat_name, 0.0) + base_val * qty

    print(f"  cooking_plans: {total} rows (15 days)")
    return total_usage


def seed_raw_purchases(
    cursor: sqlite3.Cursor,
    total_usage: dict[str, float],
) -> dict[str, float]:
    """Seed purchases that are coherent with cooking plan usage.

    - For most materials: purchases cover usage + 5-15 % normal waste.
    - For LOSS_MATERIALS: purchases only cover a fraction of usage (demo flag).

    Returns dict of material_name → total purchased (base units).
    """
    cursor.execute("SELECT id, item_name FROM materials")
    mat_map = {row[1]: row[0] for row in cursor.fetchall()}

    total_purchased: dict[str, float] = {}
    total_rows = 0

    for mat_name, expected_base in total_usage.items():
        if mat_name not in mat_map:
            continue
        mid = mat_map[mat_name]
        template = RAW_PURCHASE_TEMPLATES.get(mat_name)
        if not template:
            continue

        order_text, order_base_price = template
        order_val, order_unit = parse_amount(order_text)
        order_base_val, order_base_unit = to_base_units(order_val, order_unit)
        if order_base_val <= 0:
            continue

        # All materials get enough purchases to cover usage + small buffer.
        # The loss for LOSS_MATERIALS shows up via low inventory, not low purchases.
        cover_ratio = random.uniform(*PURCHASE_COVER_RANGE)

        target_purchased = expected_base * cover_ratio

        # How many orders needed? (at least 1)
        n_orders = max(1, round(target_purchased / order_base_val))

        # Spread orders over the last 14 days
        purchased_total = 0.0
        for _ in range(n_orders):
            days_back = random.randint(0, 14)
            purchase_date = (TODAY - timedelta(days=days_back)).date().isoformat()

            # Slight price variation ±10 %
            price = round(order_base_price * random.uniform(0.90, 1.10), 2)

            cursor.execute(
                "INSERT INTO raw_purchases "
                "(material_id, amount, amount_value, amount_unit, price, purchase_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (mid, order_text, order_base_val, order_base_unit, price, purchase_date),
            )
            purchased_total += order_base_val
            total_rows += 1

        total_purchased[mat_name] = purchased_total

    # Also add a handful of purchases for materials NOT used in any recipe
    # (e.g. Sahne, Zimt, Trockenhefe) so the purchases tab isn't empty for them
    unused_in_recipes = set(mat_map.keys()) - set(total_usage.keys())
    for mat_name in unused_in_recipes:
        template = RAW_PURCHASE_TEMPLATES.get(mat_name)
        if not template:
            continue
        # 1-2 random purchases in the last 2 weeks
        for _ in range(random.randint(1, 2)):
            order_text, order_base_price = template
            order_val, order_unit = parse_amount(order_text)
            order_base_val, order_base_unit = to_base_units(order_val, order_unit)
            days_back = random.randint(0, 14)
            purchase_date = (TODAY - timedelta(days=days_back)).date().isoformat()
            price = round(order_base_price * random.uniform(0.90, 1.10), 2)
            cursor.execute(
                "INSERT INTO raw_purchases "
                "(material_id, amount, amount_value, amount_unit, price, purchase_date) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (mat_map[mat_name], order_text, order_base_val, order_base_unit, price, purchase_date),
            )
            total_purchased[mat_name] = total_purchased.get(mat_name, 0.0) + order_base_val
            total_rows += 1

    print(f"  raw_purchases: {total_rows} rows (14 days)")
    return total_purchased


def update_material_counts(
    cursor: sqlite3.Cursor,
    total_usage: dict[str, float],
    total_purchased: dict[str, float],
) -> None:
    """Set material inventory counts in BASE UNITS (g, ml, or Stück).

    All three numbers share the same unit:
        purchased (base units) - expected_usage (base units) = expected_remaining
        actual_inventory (base units) = expected_remaining - unaccounted_loss

    For normal materials:  inventory ≈ expected_remaining (small random variance)
    For LOSS_MATERIALS:    inventory is near zero or very low, making the
                           unaccounted loss clearly visible in the analysis.
    """
    cursor.execute("SELECT id, item_name FROM materials")
    mat_map = {row[1]: row[0] for row in cursor.fetchall()}

    for mat_name, mid in mat_map.items():
        purchased = total_purchased.get(mat_name, 0.0)
        used = total_usage.get(mat_name, 0.0)
        expected_remaining = purchased - used

        if mat_name in LOSS_MATERIALS:
            # These materials have mysteriously low inventory.
            # Inventory is only 0-10% of expected_remaining → big unaccounted loss.
            count = round(max(0, expected_remaining * random.uniform(0.0, 0.10)))
        elif purchased > 0 and used > 0:
            # Normal materials: inventory ≈ expected_remaining with small variance (±5%)
            variance = random.uniform(-0.05, 0.05) * expected_remaining
            count = round(max(0, expected_remaining + variance))
        else:
            # Materials not used in recipes — just some stock on hand
            count = round(purchased * random.uniform(0.5, 0.9)) if purchased > 0 else random.randint(500, 5000)

        days_ago = random.randint(0, 2)
        updated = TODAY - timedelta(days=days_ago)
        cursor.execute(
            "UPDATE materials SET count = ?, updated_at = ?, updated_by = ? WHERE id = ?",
            (count, random_time(updated), random.choice(STAFF), mid),
        )

    print(f"  materials: counts updated for {len(mat_map)} items (base units)")


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

def main() -> None:
    reset = "--reset" in sys.argv

    print(f"Database: {DB_PATH}")
    print(f"Date:     {TODAY_DATE}")
    print()

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")

    create_tables(cursor)

    if reset:
        print("Deleting existing data ...")
        for table in [
            "cooking_plans", "raw_purchases", "product_materials", "baked_goods",
            "schedules", "checklist_items", "materials", "cleaning_tasks",
            "tickets", "audit_log",
        ]:
            cursor.execute(f"DELETE FROM {table}")
        print()

    print("Seeding data ...")
    seed_checklist_items(cursor)
    seed_materials(cursor)
    seed_cleaning_tasks(cursor)
    seed_tickets(cursor)
    seed_audit_log(cursor)
    seed_schedules(cursor)
    seed_baked_goods(cursor)

    # These three are tightly coupled for consistency
    total_usage = seed_cooking_plans(cursor)
    total_purchased = seed_raw_purchases(cursor, total_usage)
    update_material_counts(cursor, total_usage, total_purchased)

    # Read back inventory for summary
    cursor.execute("SELECT item_name, count FROM materials")
    inventory = {row[0]: row[1] for row in cursor.fetchall()}

    conn.commit()
    conn.close()
    print()
    print("Done! Database seeded with coherent test data.")
    print()

    # Print a summary of the analysis scenario
    print("=== Analysis scenario summary ===")
    print(f"  {'Material':<23} {'Purchased':>10} {'Expected':>10} {'Inventory':>10} {'Unaccounted':>12}  Flag")
    print("  " + "-" * 80)
    for mat_name in sorted(total_usage.keys()):
        expected = total_usage[mat_name]
        purchased = total_purchased.get(mat_name, 0.0)
        inv = inventory.get(mat_name, 0)
        expected_remaining = purchased - expected
        unaccounted = expected_remaining - inv
        flag = " !!!" if mat_name in LOSS_MATERIALS and unaccounted > 0 else ""
        print(f"  {mat_name:<23} {purchased:>10.0f} {expected:>10.0f} {inv:>10} {unaccounted:>+11.0f}{flag}")


if __name__ == "__main__":
    main()
