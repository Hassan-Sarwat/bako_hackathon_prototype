"""Gemini-Funktionsdeklarationen für die Bäckerei-Assistenten-Tools."""

from google.genai import types

# Tool: Checklisten-Aufgabe als erledigt markieren
mark_item_complete_decl = types.FunctionDeclaration(
    name="mark_item_complete",
    description="Eine Checklisten-Aufgabe als erledigt markieren. Verwende dies, nachdem der Benutzer bestätigt hat, dass die Aufgabe abgeschlossen ist.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "item_id": types.Schema(
                type="INTEGER",
                description="Die ID der Checklisten-Aufgabe, die als erledigt markiert werden soll",
            ),
            "notes": types.Schema(
                type="STRING",
                description="Optionale Anmerkungen zur Erledigung",
            ),
        },
        required=["item_id"],
    ),
)

# Tool: Checklisten-Aufgabe als unerledigt markieren
mark_item_incomplete_decl = types.FunctionDeclaration(
    name="mark_item_incomplete",
    description="Eine Checklisten-Aufgabe als unerledigt markieren, um eine vorherige Erledigung rückgängig zu machen.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "item_id": types.Schema(
                type="INTEGER",
                description="Die ID der Checklisten-Aufgabe, die als unerledigt markiert werden soll",
            ),
        },
        required=["item_id"],
    ),
)

# Tool: Offene Aufgaben abrufen
get_remaining_items_decl = types.FunctionDeclaration(
    name="get_remaining_items",
    description="Alle noch offenen (unerledigten) Aufgaben einer Checkliste abrufen. Gibt IDs und Namen zurück.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "checklist_type": types.Schema(
                type="STRING",
                description="Der Typ der Checkliste",
                enum=["sanitation"],
            ),
        },
        required=["checklist_type"],
    ),
)

# Tool: Materialbestand aktualisieren
update_material_count_decl = types.FunctionDeclaration(
    name="update_material_count",
    description="Den aktuellen Bestand eines Materials aktualisieren. Erstellt das Material, falls es noch nicht existiert.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "item_name": types.Schema(
                type="STRING",
                description="Der Name des Materials",
            ),
            "count": types.Schema(
                type="INTEGER",
                description="Die aktuelle Anzahl oder Menge des Materials",
            ),
        },
        required=["item_name", "count"],
    ),
)

# Tool: Alle Materialien abrufen
get_materials_decl = types.FunctionDeclaration(
    name="get_materials",
    description="Alle Materialien mit aktuellem Bestand, letztem Aktualisierungszeitpunkt und wer zuletzt aktualisiert hat abrufen.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Veraltete Materialien abrufen (nicht in den letzten 7 Tagen aktualisiert)
get_stale_materials_decl = types.FunctionDeclaration(
    name="get_stale_materials",
    description="Materialien abrufen, die seit mehr als 7 Tagen nicht aktualisiert wurden. Diese sollten überprüft werden.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Heutige Reinigungsaufgaben abrufen
get_cleaning_tasks_decl = types.FunctionDeclaration(
    name="get_cleaning_tasks",
    description="Alle heutigen Reinigungsaufgaben mit ihrem Erledigungsstatus abrufen. Die Aufgaben werden jeden Tag automatisch neu erstellt.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Offene Reinigungsaufgaben abrufen
get_incomplete_cleaning_tasks_decl = types.FunctionDeclaration(
    name="get_incomplete_cleaning_tasks",
    description="Nur die noch offenen (unerledigten) Reinigungsaufgaben für heute abrufen.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Reinigungsaufgabe als erledigt markieren
mark_cleaning_complete_decl = types.FunctionDeclaration(
    name="mark_cleaning_complete",
    description="Eine tägliche Reinigungsaufgabe als erledigt markieren. Verwende dies, nachdem der Benutzer bestätigt hat, dass die Reinigung abgeschlossen ist.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "task_id": types.Schema(
                type="INTEGER",
                description="Die ID der Reinigungsaufgabe, die als erledigt markiert werden soll",
            ),
            "notes": types.Schema(
                type="STRING",
                description="Optionale Anmerkungen zur Reinigung",
            ),
        },
        required=["task_id"],
    ),
)

# Tool: Reinigungsaufgabe als unerledigt markieren
mark_cleaning_incomplete_decl = types.FunctionDeclaration(
    name="mark_cleaning_incomplete",
    description="Eine tägliche Reinigungsaufgabe als unerledigt markieren, um eine vorherige Erledigung rückgängig zu machen.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "task_id": types.Schema(
                type="INTEGER",
                description="Die ID der Reinigungsaufgabe, die als unerledigt markiert werden soll",
            ),
        },
        required=["task_id"],
    ),
)

# Tool: Reinigungsfortschritt abrufen
get_cleaning_summary_decl = types.FunctionDeclaration(
    name="get_cleaning_summary",
    description="Eine Zusammenfassung des heutigen Reinigungsfortschritts abrufen — erledigte vs. gesamte Aufgaben.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Checklisten-Zusammenfassung abrufen
get_checklist_summary_decl = types.FunctionDeclaration(
    name="get_checklist_summary",
    description="Eine Zusammenfassung abrufen, die zeigt, wie viele Aufgaben erledigt vs. insgesamt vorhanden sind.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "checklist_type": types.Schema(
                type="STRING",
                description="Der Typ der Checkliste",
                enum=["sanitation"],
            ),
        },
        required=["checklist_type"],
    ),
)

# Tool: Ticket für das Büro erstellen
raise_ticket_decl = types.FunctionDeclaration(
    name="raise_ticket",
    description=(
        "Ein Ticket erstellen, um das Büro über ein Problem zu informieren. "
        "Bestimme die Dringlichkeit anhand des Kontexts: 'urgent' für defekte Maschinen, "
        "nicht erschienene Mitarbeiter, komplett ausverkaufte Produkte oder Sicherheitsrisiken. "
        "'high' für eingeschränkt funktionierende Geräte oder sehr niedrigen Bestand. "
        "'normal' für bald zur Neige gehende Vorräte oder allgemeine Wartung. "
        "'low' für Verbesserungswünsche oder nicht zeitkritische Anfragen."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "title": types.Schema(
                type="STRING",
                description="Kurze Zusammenfassung des Problems",
            ),
            "description": types.Schema(
                type="STRING",
                description="Ausführliche Beschreibung des Problems",
            ),
            "category": types.Schema(
                type="STRING",
                description="Kategorie des Tickets",
                enum=[
                    "machine_breakdown",
                    "employee_no_show",
                    "stock_shortage",
                    "maintenance",
                    "safety",
                    "other",
                ],
            ),
            "urgency": types.Schema(
                type="STRING",
                description="Dringlichkeitsstufe basierend auf der Art des Problems",
                enum=["urgent", "high", "normal", "low"],
            ),
        },
        required=["title", "description", "category", "urgency"],
    ),
)

# Tool: Offene Tickets abrufen
get_open_tickets_decl = types.FunctionDeclaration(
    name="get_open_tickets",
    description="Alle aktuell offenen Tickets abrufen, sortiert nach Dringlichkeit.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Alle Tools gebündelt für die Gemini-Konfiguration
all_tools = types.Tool(
    function_declarations=[
        mark_item_complete_decl,
        mark_item_incomplete_decl,
        get_remaining_items_decl,
        update_material_count_decl,
        get_materials_decl,
        get_stale_materials_decl,
        get_cleaning_tasks_decl,
        get_incomplete_cleaning_tasks_decl,
        mark_cleaning_complete_decl,
        mark_cleaning_incomplete_decl,
        get_cleaning_summary_decl,
        get_checklist_summary_decl,
        raise_ticket_decl,
        get_open_tickets_decl,
    ]
)
