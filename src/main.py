"""Bakery Voice Assistant - FastAPI backend.

Exposes REST API endpoints for checklist, cleaning, inventory,
and ticket management. The voice assistant (Gemini Live API)
runs alongside the API server.
"""

from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import db

load_dotenv()


# ---------------------------------------------------------------------------
# Lifespan: initialise DB on startup
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    print("Database initialized with bakery checklists.")
    yield


app = FastAPI(
    title="Bakery Assistant API",
    description="Backend API for the Bakery Voice Assistant",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS – allow the frontend (any origin for now during development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class CompleteItemRequest(BaseModel):
    notes: str | None = None


class UpdateMaterialRequest(BaseModel):
    item_name: str
    count: int


class RaiseTicketRequest(BaseModel):
    title: str
    description: str
    category: str
    urgency: str = "normal"


# ---------------------------------------------------------------------------
# Checklist endpoints
# ---------------------------------------------------------------------------
@app.get("/api/checklist/{checklist_type}/items")
async def get_checklist_items(checklist_type: str):
    """Get all items (complete and incomplete) for a checklist type."""
    items = db.get_all_checklist_items(checklist_type)
    return {"items": items}


@app.get("/api/checklist/{checklist_type}/remaining")
async def get_remaining_items(checklist_type: str):
    """Get all incomplete items for a checklist type."""
    items = db.get_incomplete_items(checklist_type)
    return {"items": items}


@app.put("/api/checklist/items/{item_id}/complete")
async def mark_item_complete(
    item_id: int,
    body: CompleteItemRequest | None = None,
    x_staff_id: str | None = Header(None),
):
    """Mark a checklist item as complete."""
    notes = body.notes if body else None
    result = db.mark_item_complete(item_id, notes, staff_id=x_staff_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.put("/api/checklist/items/{item_id}/incomplete")
async def mark_item_incomplete(
    item_id: int,
    x_staff_id: str | None = Header(None),
):
    """Mark a checklist item as incomplete."""
    result = db.mark_item_incomplete(item_id, staff_id=x_staff_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.get("/api/checklist/{checklist_type}/summary")
async def get_checklist_summary(checklist_type: str):
    """Get completion summary for a checklist."""
    return db.get_checklist_summary(checklist_type)


# ---------------------------------------------------------------------------
# Cleaning endpoints
# ---------------------------------------------------------------------------
@app.get("/api/cleaning/tasks")
async def get_cleaning_tasks():
    """Get all of today's cleaning tasks."""
    tasks = db.get_cleaning_tasks()
    return {"tasks": tasks}


@app.get("/api/cleaning/tasks/incomplete")
async def get_incomplete_cleaning_tasks():
    """Get today's remaining incomplete cleaning tasks."""
    tasks = db.get_incomplete_cleaning_tasks()
    return {"tasks": tasks}


@app.put("/api/cleaning/tasks/{task_id}/complete")
async def mark_cleaning_complete(
    task_id: int,
    body: CompleteItemRequest | None = None,
    x_staff_id: str | None = Header(None),
):
    """Mark a cleaning task as complete."""
    notes = body.notes if body else None
    result = db.mark_cleaning_complete(task_id, notes, staff_id=x_staff_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.put("/api/cleaning/tasks/{task_id}/incomplete")
async def mark_cleaning_incomplete(
    task_id: int,
    x_staff_id: str | None = Header(None),
):
    """Mark a cleaning task as incomplete."""
    result = db.mark_cleaning_incomplete(task_id, staff_id=x_staff_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.get("/api/cleaning/summary")
async def get_cleaning_summary():
    """Get today's cleaning progress summary."""
    return db.get_cleaning_summary()


# ---------------------------------------------------------------------------
# Materials endpoints
# ---------------------------------------------------------------------------
@app.get("/api/materials")
async def get_materials():
    """Get all materials with current counts and last update info."""
    materials = db.get_materials()
    return {"materials": materials}


@app.put("/api/materials")
async def update_material_count(
    body: UpdateMaterialRequest,
    x_staff_id: str | None = Header(None),
):
    """Update the count of a material."""
    result = db.update_material_count(body.item_name, body.count, staff_id=x_staff_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.get("/api/materials/stale")
async def get_stale_materials():
    """Get materials not updated in the last 7 days — a checklist of items to recount."""
    materials = db.get_stale_materials()
    return {"materials": materials}


# ---------------------------------------------------------------------------
# Ticket endpoints
# ---------------------------------------------------------------------------
@app.post("/api/tickets")
async def raise_ticket(
    body: RaiseTicketRequest,
    x_staff_id: str | None = Header(None),
):
    """Raise a new ticket for the office."""
    result = db.raise_ticket(
        title=body.title,
        description=body.description,
        category=body.category,
        urgency=body.urgency,
        raised_by=x_staff_id,
    )
    return result


@app.get("/api/tickets")
async def get_open_tickets():
    """Get all currently open tickets."""
    tickets = db.get_open_tickets()
    return {"tickets": tickets}


@app.put("/api/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: int,
    x_staff_id: str | None = Header(None),
):
    """Close a ticket (set status to 'close')."""
    result = db.close_ticket(ticket_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# ---------------------------------------------------------------------------
# Inventory endpoints (maps materials table to inventory log shape)
# ---------------------------------------------------------------------------
@app.get("/api/inventory")
async def get_inventory():
    """Get all inventory items (alias of materials, with dashboard-friendly field names)."""
    materials = db.get_materials()
    items = [
        {
            "id": m["id"],
            "item_name": m["item_name"],
            "count": m["count"],
            "logged_by": m["updated_by"],
            "logged_at": m["updated_at"],
        }
        for m in materials
    ]
    return {"items": items}


# ---------------------------------------------------------------------------
# Dashboard aggregate endpoint
# ---------------------------------------------------------------------------
@app.get("/api/dashboard")
async def get_dashboard():
    """Return all data needed to render the dashboard in one request."""
    sanitation_items = db.get_all_checklist_items("sanitation")
    sanitation_summary = db.get_checklist_summary("sanitation")
    cleaning_tasks = db.get_cleaning_tasks()
    cleaning_summary = db.get_cleaning_summary()
    tickets = db.get_open_tickets()
    materials = db.get_materials()
    inventory_items = [
        {
            "id": m["id"],
            "item_name": m["item_name"],
            "count": m["count"],
            "logged_by": m["updated_by"],
            "logged_at": m["updated_at"],
        }
        for m in materials
    ]
    return {
        "sanitation": {"items": sanitation_items, "summary": sanitation_summary},
        "cleaning": {"tasks": cleaning_tasks, "summary": cleaning_summary},
        "inventory": {"items": inventory_items},
        "tickets": tickets,
    }


# ---------------------------------------------------------------------------
# Audit log endpoints
# ---------------------------------------------------------------------------
@app.get("/api/audit")
async def get_audit_log(
    limit: int = 50,
    staff_id: str | None = None,
):
    """Get recent audit log entries, optionally filtered by staff_id."""
    entries = db.get_audit_log(limit=limit, staff_id=staff_id)
    return {"entries": entries}


# ---------------------------------------------------------------------------
# Utility endpoints
# ---------------------------------------------------------------------------
@app.post("/api/checklists/reset")
async def reset_checklists():
    """Reset all checklist items to incomplete for a new day."""
    return db.reset_checklists()


@app.get("/api/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------
def main():
    """Run the API server via uvicorn."""
    import uvicorn

    print("=" * 50)
    print("  Bakery Assistant API")
    print("  Sanitation & Inventory Checklist Manager")
    print("=" * 50)
    print()

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()
