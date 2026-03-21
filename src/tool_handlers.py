"""Handler that dispatches Gemini tool calls to database operations."""

import asyncio

from . import db


async def handle_tool_call(function_name: str, args: dict, staff_id: str | None = None) -> dict:
    """Route a Gemini function call to the appropriate DB operation.

    Uses asyncio.to_thread to avoid blocking the event loop with synchronous SQLite calls.

    Args:
        function_name: The tool function name from Gemini.
        args: The arguments Gemini provided for the tool.
        staff_id: The currently identified staff member (from NFC or manual login).
                  Write operations will be rejected if this is None.
    """
    if function_name == "mark_item_complete":
        result = await asyncio.to_thread(
            db.mark_item_complete, args["item_id"], args.get("notes"), staff_id
        )
    elif function_name == "mark_item_incomplete":
        result = await asyncio.to_thread(db.mark_item_incomplete, args["item_id"], staff_id)
    elif function_name == "get_remaining_items":
        items = await asyncio.to_thread(
            db.get_incomplete_items, args["checklist_type"]
        )
        result = {"items": items}
    elif function_name == "add_inventory_count":
        result = await asyncio.to_thread(
            db.add_inventory_count, args["item_name"], args["count"], staff_id
        )
    elif function_name == "get_cleaning_tasks":
        tasks = await asyncio.to_thread(db.get_cleaning_tasks)
        result = {"tasks": tasks}
    elif function_name == "get_incomplete_cleaning_tasks":
        tasks = await asyncio.to_thread(db.get_incomplete_cleaning_tasks)
        result = {"tasks": tasks}
    elif function_name == "mark_cleaning_complete":
        result = await asyncio.to_thread(
            db.mark_cleaning_complete, args["task_id"], args.get("notes"), staff_id
        )
    elif function_name == "mark_cleaning_incomplete":
        result = await asyncio.to_thread(
            db.mark_cleaning_incomplete, args["task_id"], staff_id
        )
    elif function_name == "get_cleaning_summary":
        result = await asyncio.to_thread(db.get_cleaning_summary)
    elif function_name == "get_checklist_summary":
        result = await asyncio.to_thread(
            db.get_checklist_summary, args["checklist_type"]
        )
    elif function_name == "raise_ticket":
        result = await asyncio.to_thread(
            db.raise_ticket,
            args["title"],
            args["description"],
            args["category"],
            args["urgency"],
            staff_id,
        )
    elif function_name == "get_open_tickets":
        tickets = await asyncio.to_thread(db.get_open_tickets)
        result = {"tickets": tickets}
    else:
        result = {"status": "error", "message": f"Unknown tool: {function_name}"}

    print(f"  [Tool] {function_name}({args}) -> {result}")
    return result
