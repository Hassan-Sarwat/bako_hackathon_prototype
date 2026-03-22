"""Bakery Voice Assistant - FastAPI backend.

Exposes REST API endpoints for checklist, cleaning, inventory,
and ticket management. The voice assistant (Gemini Live API)
runs alongside the API server.
"""

from contextlib import asynccontextmanager
from datetime import date

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


class ScheduleRequest(BaseModel):
    employee_name: str
    schedule_date: str
    start_time: str
    end_time: str
    cleaning: int = 0


class ScheduleUpdateRequest(BaseModel):
    employee_name: str | None = None
    schedule_date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    cleaning: int | None = None


class BakedGoodRequest(BaseModel):
    name: str
    price: float
    recipe: str | None = None


class BakedGoodUpdateRequest(BaseModel):
    name: str | None = None
    price: float | None = None
    recipe: str | None = None


class ProductMaterialEntry(BaseModel):
    material_id: int
    amount: str


class SetProductMaterialsRequest(BaseModel):
    materials: list[ProductMaterialEntry]


class RawPurchaseRequest(BaseModel):
    material_id: int
    amount: str
    price: float
    purchase_date: str


class RawPurchaseUpdateRequest(BaseModel):
    material_id: int | None = None
    amount: str | None = None
    price: float | None = None
    purchase_date: str | None = None


class CookingPlanRequest(BaseModel):
    plan_date: str
    product_id: int
    quantity: int


class CookingPlanUpdateRequest(BaseModel):
    plan_date: str | None = None
    product_id: int | None = None
    quantity: int | None = None


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
# Schedule endpoints
# ---------------------------------------------------------------------------
@app.get("/api/schedules")
async def get_schedules(
    date: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get schedules, optionally filtered by date or date range."""
    schedules = db.get_schedules(schedule_date=date, start_date=start_date, end_date=end_date)
    return {"schedules": schedules}


@app.post("/api/schedules")
async def create_schedule(body: ScheduleRequest):
    """Create a new schedule entry."""
    result = db.create_schedule(
        employee_name=body.employee_name,
        schedule_date=body.schedule_date,
        start_time=body.start_time,
        end_time=body.end_time,
        cleaning=body.cleaning,
    )
    return result


@app.put("/api/schedules/{schedule_id}")
async def update_schedule(schedule_id: int, body: ScheduleUpdateRequest):
    """Update a schedule entry."""
    result = db.update_schedule(
        schedule_id,
        employee_name=body.employee_name,
        schedule_date=body.schedule_date,
        start_time=body.start_time,
        end_time=body.end_time,
        cleaning=body.cleaning,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: int):
    """Delete a schedule entry."""
    result = db.delete_schedule(schedule_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# ---------------------------------------------------------------------------
# Baked goods endpoints
# ---------------------------------------------------------------------------
@app.get("/api/baked-goods")
async def get_baked_goods():
    """Get all baked goods (products)."""
    items = db.get_baked_goods()
    return {"baked_goods": items}


@app.get("/api/baked-goods/{product_id}")
async def get_baked_good(product_id: int):
    """Get a single baked good with its materials."""
    item = db.get_baked_good(product_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return item


@app.post("/api/baked-goods")
async def create_baked_good(body: BakedGoodRequest):
    """Create a new baked good (product)."""
    result = db.create_baked_good(name=body.name, price=body.price, recipe=body.recipe)
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.put("/api/baked-goods/{product_id}")
async def update_baked_good(product_id: int, body: BakedGoodUpdateRequest):
    """Update a baked good."""
    result = db.update_baked_good(product_id, name=body.name, price=body.price, recipe=body.recipe)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.delete("/api/baked-goods/{product_id}")
async def delete_baked_good(product_id: int):
    """Delete a baked good (cascades to product_materials)."""
    result = db.delete_baked_good(product_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.get("/api/baked-goods/{product_id}/materials")
async def get_product_materials(product_id: int):
    """Get all materials for a product."""
    materials = db.get_product_materials(product_id)
    return {"materials": materials}


@app.put("/api/baked-goods/{product_id}/materials")
async def set_product_materials(product_id: int, body: SetProductMaterialsRequest):
    """Replace all materials for a product."""
    materials = [{"material_id": m.material_id, "amount": m.amount} for m in body.materials]
    result = db.set_product_materials(product_id, materials)
    return result


# ---------------------------------------------------------------------------
# Raw purchases endpoints
# ---------------------------------------------------------------------------
@app.get("/api/purchases")
async def get_purchases(
    material_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get raw material purchases with optional filters."""
    items = db.get_raw_purchases(material_id=material_id, start_date=start_date, end_date=end_date)
    return {"purchases": items}


@app.post("/api/purchases")
async def create_purchase(body: RawPurchaseRequest):
    """Create a new raw material purchase."""
    result = db.create_raw_purchase(
        material_id=body.material_id,
        amount=body.amount,
        price=body.price,
        purchase_date=body.purchase_date,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.put("/api/purchases/{purchase_id}")
async def update_purchase(purchase_id: int, body: RawPurchaseUpdateRequest):
    """Update a raw material purchase."""
    result = db.update_raw_purchase(
        purchase_id,
        material_id=body.material_id,
        amount=body.amount,
        price=body.price,
        purchase_date=body.purchase_date,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.delete("/api/purchases/{purchase_id}")
async def delete_purchase(purchase_id: int):
    """Delete a raw material purchase."""
    result = db.delete_raw_purchase(purchase_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# ---------------------------------------------------------------------------
# Cooking plan endpoints
# ---------------------------------------------------------------------------
@app.get("/api/cooking-plans")
async def get_cooking_plans(date: str | None = None):
    """Get cooking plans, optionally filtered by date."""
    items = db.get_cooking_plans(plan_date=date)
    return {"cooking_plans": items}


@app.post("/api/cooking-plans")
async def create_cooking_plan(body: CookingPlanRequest):
    """Create or update a cooking plan entry."""
    result = db.create_cooking_plan(
        plan_date=body.plan_date,
        product_id=body.product_id,
        quantity=body.quantity,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result


@app.put("/api/cooking-plans/{plan_id}")
async def update_cooking_plan(plan_id: int, body: CookingPlanUpdateRequest):
    """Update a cooking plan entry."""
    result = db.update_cooking_plan(
        plan_id,
        plan_date=body.plan_date,
        product_id=body.product_id,
        quantity=body.quantity,
    )
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


@app.delete("/api/cooking-plans/{plan_id}")
async def delete_cooking_plan(plan_id: int):
    """Delete a cooking plan entry."""
    result = db.delete_cooking_plan(plan_id)
    if result.get("status") == "error":
        raise HTTPException(status_code=404, detail=result["message"])
    return result


# ---------------------------------------------------------------------------
# Inventory endpoints (maps materials table to inventory log shape)
# ---------------------------------------------------------------------------
@app.get("/api/inventory")
async def get_inventory():
    """Get all inventory items with unit info."""
    materials = db.get_inventory_with_units()
    items = [
        {
            "id": m["id"],
            "item_name": m["item_name"],
            "count": m["count"],
            "unit": m["unit"],
            "logged_by": m["updated_by"],
            "logged_at": m["updated_at"],
        }
        for m in materials
    ]
    return {"items": items}


@app.get("/api/inventory/material-needs")
async def get_material_needs(days: int = 3):
    """Calculate material needs for the next N days based on predictions."""
    needs = db.get_material_needs(days)
    return {"needs": needs, "days": days}


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
    today = date.today().isoformat()
    schedules = db.get_schedules(schedule_date=today)
    cooking_plans = db.get_cooking_plans(plan_date=today)
    return {
        "sanitation": {"items": sanitation_items, "summary": sanitation_summary},
        "cleaning": {"tasks": cleaning_tasks, "summary": cleaning_summary},
        "inventory": {"items": inventory_items},
        "tickets": tickets,
        "schedules": schedules,
        "cooking_plans": cooking_plans,
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
# Analysis endpoints
# ---------------------------------------------------------------------------
@app.get("/api/analysis/material-usage")
async def get_material_usage_analysis(start_date: str, end_date: str):
    """Analyse expected material usage from cooking plans vs actual purchases."""
    materials = db.get_material_usage_analysis(start_date, end_date)
    return {"materials": materials}


@app.get("/api/analysis/material-drilldown/{material_id}")
async def get_material_drilldown(material_id: int, start_date: str, end_date: str):
    """Get per-day cooking plan breakdown for a specific material."""
    entries = db.get_material_drilldown(material_id, start_date, end_date)
    return {"entries": entries}


@app.get("/api/analysis/product-loss")
async def get_product_loss_analysis(start_date: str, end_date: str):
    """Analyse material losses attributed to each product/recipe."""
    products = db.get_product_loss_analysis(start_date, end_date)
    return {"products": products}


@app.get("/api/analysis/product-loss-drilldown/{product_id}")
async def get_product_loss_drilldown(product_id: int, start_date: str, end_date: str):
    """Get per-material loss breakdown for a specific product."""
    entries = db.get_product_loss_drilldown(product_id, start_date, end_date)
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
# Sales endpoints
# ---------------------------------------------------------------------------
@app.get("/api/sales")
async def get_sales(
    start_date: str | None = None,
    end_date: str | None = None,
    product_id: int | None = None,
):
    """Get sales data with optional filters."""
    items = db.get_sales(start_date=start_date, end_date=end_date, product_id=product_id)
    return {"sales": items}


# ---------------------------------------------------------------------------
# Prediction endpoints
# ---------------------------------------------------------------------------
@app.get("/api/predictions")
async def get_predictions(
    start_date: str | None = None,
    end_date: str | None = None,
):
    """Get predictions for a date range."""
    items = db.get_predictions(start_date=start_date, end_date=end_date)
    return {"predictions": items}


@app.get("/api/predictions/daily-plan")
async def get_daily_plan(date: str):
    """Get the recommended cooking plan for a specific day."""
    plan = db.get_prediction_daily_plan(date)
    return {"date": date, "plan": plan}


@app.get("/api/predictions/product/{product_id}/history")
async def get_product_prediction_history(product_id: int):
    """Get last 2 weeks of actual sales + next 3 days predictions."""
    history = db.get_product_sales_history(product_id, 14)
    predictions = db.get_product_predictions(product_id, 3)
    product = db.get_baked_good(product_id)
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    return {
        "product": {"id": product["id"], "name": product["name"], "price": product["price"]},
        "history": history,
        "predictions": predictions,
    }


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
