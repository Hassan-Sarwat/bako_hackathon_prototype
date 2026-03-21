"""Handler that dispatches Gemini tool calls to database operations."""

import asyncio

from . import db


async def handle_tool_call(function_name: str, args: dict) -> dict:
    """Route a Gemini function call to the appropriate DB operation.

    Uses asyncio.to_thread to avoid blocking the event loop with synchronous SQLite calls.
    """
    if function_name == "mark_item_complete":
        result = await asyncio.to_thread(
            db.mark_item_complete, args["item_id"], args.get("notes")
        )
    elif function_name == "mark_item_incomplete":
        result = await asyncio.to_thread(db.mark_item_incomplete, args["item_id"])
    elif function_name == "get_remaining_items":
        items = await asyncio.to_thread(
            db.get_incomplete_items, args["checklist_type"]
        )
        result = {"items": items}
    elif function_name == "add_inventory_count":
        result = await asyncio.to_thread(
            db.add_inventory_count, args["item_name"], args["count"]
        )
    elif function_name == "log_cleaning_activity":
        result = await asyncio.to_thread(
            db.log_cleaning, args["area"], args["action"]
        )
    elif function_name == "get_checklist_summary":
        result = await asyncio.to_thread(
            db.get_checklist_summary, args["checklist_type"]
        )
    else:
        result = {"status": "error", "message": f"Unknown tool: {function_name}"}

    print(f"  [Tool] {function_name}({args}) -> {result}")
    return result
