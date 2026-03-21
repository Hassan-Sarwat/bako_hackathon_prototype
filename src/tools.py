"""Gemini function declarations for the bakery assistant tools."""

from google.genai import types

# Tool: Mark a checklist item as complete
mark_item_complete_decl = types.FunctionDeclaration(
    name="mark_item_complete",
    description="Mark a checklist item as complete. Use after the user confirms they have finished a task.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "item_id": types.Schema(
                type="INTEGER",
                description="The ID of the checklist item to mark as complete",
            ),
            "notes": types.Schema(
                type="STRING",
                description="Optional notes about the completion",
            ),
        },
        required=["item_id"],
    ),
)

# Tool: Mark a checklist item as incomplete
mark_item_incomplete_decl = types.FunctionDeclaration(
    name="mark_item_incomplete",
    description="Mark a checklist item as incomplete, undoing a previous completion.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "item_id": types.Schema(
                type="INTEGER",
                description="The ID of the checklist item to mark as incomplete",
            ),
        },
        required=["item_id"],
    ),
)

# Tool: Get remaining incomplete items
get_remaining_items_decl = types.FunctionDeclaration(
    name="get_remaining_items",
    description="Get all remaining incomplete items for a checklist. Returns item IDs and names.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "checklist_type": types.Schema(
                type="STRING",
                description="The type of checklist",
                enum=["sanitation", "inventory"],
            ),
        },
        required=["checklist_type"],
    ),
)

# Tool: Log inventory count
add_inventory_count_decl = types.FunctionDeclaration(
    name="add_inventory_count",
    description="Log the current count or quantity for an inventory item.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "item_name": types.Schema(
                type="STRING",
                description="The name of the inventory item",
            ),
            "count": types.Schema(
                type="INTEGER",
                description="The current count or quantity of the item",
            ),
        },
        required=["item_name", "count"],
    ),
)

# Tool: Get today's cleaning tasks
get_cleaning_tasks_decl = types.FunctionDeclaration(
    name="get_cleaning_tasks",
    description="Get all of today's cleaning tasks with their completion status. Tasks refresh automatically each day.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Get remaining incomplete cleaning tasks
get_incomplete_cleaning_tasks_decl = types.FunctionDeclaration(
    name="get_incomplete_cleaning_tasks",
    description="Get only the remaining incomplete cleaning tasks for today.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Mark a cleaning task as complete
mark_cleaning_complete_decl = types.FunctionDeclaration(
    name="mark_cleaning_complete",
    description="Mark a daily cleaning task as complete. Use after the user confirms they have finished a cleaning task.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "task_id": types.Schema(
                type="INTEGER",
                description="The ID of the cleaning task to mark as complete",
            ),
            "notes": types.Schema(
                type="STRING",
                description="Optional notes about the cleaning",
            ),
        },
        required=["task_id"],
    ),
)

# Tool: Mark a cleaning task as incomplete
mark_cleaning_incomplete_decl = types.FunctionDeclaration(
    name="mark_cleaning_incomplete",
    description="Mark a daily cleaning task as incomplete, undoing a previous completion.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "task_id": types.Schema(
                type="INTEGER",
                description="The ID of the cleaning task to mark as incomplete",
            ),
        },
        required=["task_id"],
    ),
)

# Tool: Get cleaning summary
get_cleaning_summary_decl = types.FunctionDeclaration(
    name="get_cleaning_summary",
    description="Get a summary of today's cleaning progress showing completed vs total tasks.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# Tool: Get checklist summary
get_checklist_summary_decl = types.FunctionDeclaration(
    name="get_checklist_summary",
    description="Get a summary showing how many items are complete vs total for a checklist.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "checklist_type": types.Schema(
                type="STRING",
                description="The type of checklist",
                enum=["sanitation", "inventory"],
            ),
        },
        required=["checklist_type"],
    ),
)

# Tool: Raise a ticket for the office
raise_ticket_decl = types.FunctionDeclaration(
    name="raise_ticket",
    description=(
        "Raise a ticket to notify the office about an issue. "
        "Determine the urgency based on context: use 'urgent' for broken machines, "
        "employee no-shows, products completely out of stock, or safety hazards. "
        "Use 'high' for equipment malfunctioning but still usable, or stock very low. "
        "Use 'normal' for supplies running low soon or general maintenance requests. "
        "Use 'low' for nice-to-have improvements or non-time-sensitive requests."
    ),
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "title": types.Schema(
                type="STRING",
                description="Short summary of the issue",
            ),
            "description": types.Schema(
                type="STRING",
                description="Detailed description of the issue",
            ),
            "category": types.Schema(
                type="STRING",
                description="Category of the ticket",
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
                description="Urgency level determined by the nature of the issue",
                enum=["urgent", "high", "normal", "low"],
            ),
        },
        required=["title", "description", "category", "urgency"],
    ),
)

# Tool: Get open tickets
get_open_tickets_decl = types.FunctionDeclaration(
    name="get_open_tickets",
    description="Get all currently open tickets, sorted by urgency.",
    parameters=types.Schema(
        type="OBJECT",
        properties={},
    ),
)

# All tools bundled for the Gemini config
all_tools = types.Tool(
    function_declarations=[
        mark_item_complete_decl,
        mark_item_incomplete_decl,
        get_remaining_items_decl,
        add_inventory_count_decl,
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
