# mock_enterprise/portal/main.py
import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
DB_FILE = BASE_DIR / "db.json"

app = FastAPI(title="CentrAlign Mock Enterprise Portal", version="1.0.0")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def load_db() -> Dict[str, List[Dict[str, Any]]]:
    """Load the portal JSON database or return seed defaults."""
    if not DB_FILE.exists():
        initial = {
            "invoices": [],
            "submitted": [
                {
                    "id": 100,
                    "vendor": "CloudScale Systems",
                    "amount": 1450.00,
                    "due_date": "2024-11-01",
                    "po_number": "PO-2024-101",
                    "status": "AUTO_APPROVED",
                    "submitted_at": "2024-10-10 09:30:00",
                }
            ],
        }
        save_db(initial)
        return initial

    try:
        return json.loads(DB_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"invoices": [], "submitted": []}


def save_db(data: Dict[str, Any]) -> None:
    """Save portal database to JSON file."""
    DB_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# HTML Web Pages (Targeted by Playwright Browser Tools)
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request, error: Optional[int] = None):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": bool(error)}
    )


@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == "agent" and password == "company123":
        return RedirectResponse("/dashboard", status_code=303)
    return RedirectResponse("/?error=1", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = load_db()
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={"invoices": list(reversed(db.get("submitted", [])))}
    )


@app.get("/invoice/new", response_class=HTMLResponse)
async def new_invoice_form(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="invoice_form.html",
        context={"success": False, "invoice": None}
    )


@app.post("/invoice/submit", response_class=HTMLResponse)
async def submit_invoice(
    request: Request,
    vendor_name: str = Form(...),
    amount: float = Form(...),
    due_date: str = Form(...),
    po_number: str = Form(...),
):
    db = load_db()
    submitted = db.get("submitted", [])
    new_id = (max([inv.get("id", 100) for inv in submitted]) + 1) if submitted else 101

    # Apply company approval policy: > $2000 requires human manager approval
    status = "PENDING_APPROVAL" if amount >= 2000.0 else "AUTO_APPROVED"
    timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    invoice = {
        "id": new_id,
        "vendor": vendor_name.strip(),
        "amount": round(float(amount), 2),
        "due_date": due_date.strip(),
        "po_number": po_number.strip(),
        "status": status,
        "submitted_at": timestamp_str,
    }

    submitted.append(invoice)
    db["submitted"] = submitted
    save_db(db)

    return templates.TemplateResponse(
        request=request,
        name="invoice_form.html",
        context={"success": True, "invoice": invoice}
    )


# ---------------------------------------------------------------------------
# REST API Endpoints (Used by APICallTool & Outcome Verifier)
# ---------------------------------------------------------------------------

class InvoiceCreatePayload(BaseModel):
    vendor_name: str
    amount: float
    due_date: str
    po_number: str


@app.get("/api/invoices")
async def api_list_invoices():
    db = load_db()
    return {"invoices": db.get("submitted", [])}


@app.get("/api/invoices/{invoice_id}")
async def api_get_invoice(invoice_id: int):
    db = load_db()
    for inv in db.get("submitted", []):
        if inv.get("id") == invoice_id:
            return inv
    raise HTTPException(status_code=404, detail="Invoice not found")


@app.post("/api/invoices", status_code=201)
async def api_create_invoice(payload: InvoiceCreatePayload):
    db = load_db()
    submitted = db.get("submitted", [])
    new_id = (max([inv.get("id", 100) for inv in submitted]) + 1) if submitted else 101
    status = "PENDING_APPROVAL" if payload.amount >= 2000.0 else "AUTO_APPROVED"

    invoice = {
        "id": new_id,
        "vendor": payload.vendor_name.strip(),
        "amount": round(payload.amount, 2),
        "due_date": payload.due_date.strip(),
        "po_number": payload.po_number.strip(),
        "status": status,
        "submitted_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    submitted.append(invoice)
    db["submitted"] = submitted
    save_db(db)
    return invoice


@app.post("/api/reset")
async def api_reset_db():
    initial = {
        "invoices": [],
        "submitted": [
            {
                "id": 100,
                "vendor": "CloudScale Systems",
                "amount": 1450.00,
                "due_date": "2024-11-01",
                "po_number": "PO-2024-101",
                "status": "AUTO_APPROVED",
                "submitted_at": "2024-10-10 09:30:00",
            }
        ],
    }
    save_db(initial)
    return {"status": "reset", "count": 1}


def main():
    import uvicorn
    uvicorn.run("mock_enterprise.portal.main:app", host="0.0.0.0", port=8001, reload=False)


if __name__ == "__main__":
    main()
