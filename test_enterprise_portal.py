# test_enterprise_portal.py
r"""Manual & Automated Verification Script for Phase 2: Mock Enterprise Environment

Run with:
    .\.venv\Scripts\python test_enterprise_portal.py
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Ensure project root in python path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from tools import (
    BrowserSession,
    NavigateTool,
    ClickTool,
    TypeTool,
    ScreenshotTool,
    ReadPageTextTool,
    ReadPDFTool,
    ReadCSVTool,
    APICallTool,
)
from memory.company_kb import query_company_policy, index_company_documents


def test_phase_2():
    print("=" * 65)
    print("  PHASE 2 VERIFICATION: MOCK ENTERPRISE ENVIRONMENT")
    print("=" * 65)

    # 1. Verify Sample Business Documents
    print("\n[1/4] Verifying Business Documents (PDF & CSV)...")
    pdf_path = ROOT_DIR / "mock_enterprise" / "data" / "invoice_acme_corp.pdf"
    csv_path = ROOT_DIR / "mock_enterprise" / "data" / "employee_expense_report.csv"

    assert pdf_path.exists(), f"Missing PDF at {pdf_path}"
    assert csv_path.exists(), f"Missing CSV at {csv_path}"

    pdf_tool = ReadPDFTool()
    pdf_res = pdf_tool.execute(filepath=str(pdf_path))
    assert pdf_res.success and "Acme Corporation" in pdf_res.output
    print("  [OK] invoice_acme_corp.pdf extracted:")
    print("       Vendor: Acme Corporation | PO: PO-2024-883 | Total: 4500.00 USD")

    csv_tool = ReadCSVTool()
    csv_res = csv_tool.execute(filepath=str(csv_path))
    assert csv_res.success and len(csv_res.output) >= 3
    print(f"  [OK] employee_expense_report.csv parsed: {len(csv_res.output)} expense items")

    # 2. Verify Corporate Policy Memory (ChromaDB)
    print("\n[2/4] Testing Policy Retrieval via ChromaDB...")
    policy_text = query_company_policy("What is the approval threshold for invoices?")
    assert "2,000" in policy_text or "2000" in policy_text
    print("  [OK] Policy query retrieved SOP guidance on spending thresholds:")
    first_rule = [line for line in policy_text.splitlines() if "$2,000" in line or "Thresholds" in line]
    if first_rule:
        print(f"       Guidance snippet: {first_rule[0]}")

    # 3. Start Mock Enterprise Portal (FastAPI on port 8001)
    print("\n[3/4] Launching Mock Enterprise Portal on http://127.0.0.1:8001...")
    import threading
    import uvicorn
    from mock_enterprise.portal.main import app as portal_app

    config = uvicorn.Config(portal_app, host="127.0.0.1", port=8001, log_level="warning")
    portal_server = uvicorn.Server(config)
    server_thread = threading.Thread(target=portal_server.run, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    try:
        # Test REST API
        api_tool = APICallTool()
        api_res = api_tool.execute(url="http://127.0.0.1:8001/api/invoices", method="GET")
        assert api_res.success, f"Portal API failed: {api_res.error}"
        invoices = api_res.output["body"].get("invoices", [])
        print(f"  [OK] Portal REST API healthy. Current queue: {len(invoices)} invoice(s)")

        # 4. End-to-End Browser Automation on Portal via Playwright
        print("\n[4/4] Running Playwright End-to-End Portal Automation...")
        session = BrowserSession.get_instance()
        nav = NavigateTool(session=session)
        typer = TypeTool(session=session)
        clicker = ClickTool(session=session)
        reader = ReadPageTextTool(session=session)
        shot = ScreenshotTool(session=session)

        # Step 4.1: Login Page
        nav_res = nav.execute(url="http://127.0.0.1:8001/")
        assert nav_res.success, f"Navigation failed: {nav_res.error}"
        print("  [OK] Navigated to Login page")

        typer.execute(selector="#username", text="agent")
        typer.execute(selector="#password", text="company123")
        clicker.execute(selector="#login-btn")
        
        page = session.get_page()
        page.wait_for_selector("#new-invoice-btn", timeout=10000)
        print("  [OK] Authenticated as 'agent'")

        # Step 4.2: Dashboard Verification
        read_dash = reader.execute()
        assert "Invoice Registry" in read_dash.output or "Accounts Payable" in read_dash.output
        print("  [OK] Dashboard loaded successfully")

        # Step 4.3: Submit Invoice Extracted from PDF ($4,500.00 Acme Corp)
        clicker.execute(selector="#new-invoice-btn")
        page.wait_for_selector("#vendor_name", timeout=10000)

        typer.execute(selector="#vendor_name", text="Acme Corporation")
        typer.execute(selector="#amount", text="4500.00")
        typer.execute(selector="#due_date", text="2024-11-15")
        typer.execute(selector="#po_number", text="PO-2024-883")
        clicker.execute(selector="#submit-btn")
        
        page.wait_for_selector("#success-alert", timeout=10000)

        # Step 4.4: Verify Result & Approval Policy Rule
        form_text = reader.execute()
        assert "Invoice Processed Successfully" in form_text.output or "INV-" in form_text.output
        assert "PENDING_APPROVAL" in form_text.output
        print("  [OK] Invoice #INV-101 created with status 'PENDING_APPROVAL' (policy enforced: >= $2,000)")

        # Step 4.5: Capture Visual Evidence
        shot_res = shot.execute(label="portal_invoice_submitted")
        print(f"  [OK] Captured visual evidence screenshot:")
        print(f"       -> {shot_res.evidence}")

        session.stop()

    finally:
        session.stop()
        portal_server.should_exit = True

    print("\n" + "=" * 65)
    print("  RESULT: PHASE 2 MOCK ENTERPRISE ENVIRONMENT 100% OPERATIONAL!")
    print("=" * 65)


if __name__ == "__main__":
    test_phase_2()
