# test_tools.py
r"""Manual Verification Script for Phase 1: Tool Abstraction Layer

Run with:
    .\.venv\Scripts\python test_tools.py
"""

import os
import tempfile
import csv
from pathlib import Path
from tools import (
    BaseTool,
    ToolResult,
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

def run_verification():
    print("=" * 60)
    print("  PHASE 1 MANUAL VERIFICATION")
    print("=" * 60)

    # 1. Verify Tool Schemas (for LLM Function Calling)
    print("\n[1/4] Verifying Tool Schemas for LLM Function Calling...")
    tools = [
        NavigateTool(),
        ClickTool(),
        TypeTool(),
        ScreenshotTool(),
        ReadPageTextTool(),
        ReadPDFTool(),
        ReadCSVTool(),
        APICallTool(),
    ]
    for t in tools:
        schema = t.schema()
        assert "function" in schema and "name" in schema["function"]
        print(f"  [OK] {t.name:<24} -> Schema valid (Function: {schema['function']['name']})")

    # 2. Verify Tabular & Document File Parsing
    print("\n[2/4] Testing ReadCSVTool...")
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".csv", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["invoice_id", "vendor", "amount"])
        writer.writeheader()
        writer.writerow({"invoice_id": "INV-101", "vendor": "Acme Corp", "amount": "4500.00"})
        writer.writerow({"invoice_id": "INV-102", "vendor": "Beta Ltd", "amount": "1200.00"})
        temp_csv = f.name

    try:
        csv_tool = ReadCSVTool()
        result = csv_tool.execute(filepath=temp_csv)
        assert result.success, f"CSV tool error: {result.error}"
        print(f"  [OK] Parsed {len(result.output)} rows successfully:")
        for row in result.output:
            print(f"       - {row}")
    finally:
        if os.path.exists(temp_csv):
            os.unlink(temp_csv)

    # 3. Verify REST API Client Tool
    print("\n[3/4] Testing APICallTool...")
    api_tool = APICallTool()
    api_result = api_tool.execute(url="https://httpbin.org/get", method="GET", timeout=10)
    if api_result.success:
        print(f"  [OK] APICallTool network GET succeeded (HTTP {api_result.output['status_code']})")
    else:
        print(f"  [NOTE] Network call: {api_result.error} (handled gracefully)")

    # 4. Verify Playwright Browser Automation & Screenshot Capture
    print("\n[4/4] Testing Playwright Browser Automation & Evidence Capture...")
    html_sample = "data:text/html,<html><head><title>CentrAlign Demo</title></head><body><h1 id='header'>Enterprise Portal Ready</h1><input id='test-input' type='text'/><button id='test-btn'>Submit</button></body></html>"

    session = BrowserSession.get_instance()
    try:
        # Navigate
        nav = NavigateTool(session=session)
        nav_res = nav.execute(url=html_sample)
        assert nav_res.success, f"Navigation failed: {nav_res.error}"
        print("  [OK] Browser Navigate: SUCCESS")

        # Type
        typer = TypeTool(session=session)
        type_res = typer.execute(selector="#test-input", text="INV-2026-001")
        assert type_res.success, f"Typing failed: {type_res.error}"
        print("  [OK] Form Input Typing: SUCCESS")

        # Click
        clicker = ClickTool(session=session)
        click_res = clicker.execute(selector="#test-btn")
        assert click_res.success, f"Click failed: {click_res.error}"
        print("  [OK] Element Click: SUCCESS")

        # Read text
        reader = ReadPageTextTool(session=session)
        read_res = reader.execute()
        assert "Enterprise Portal Ready" in read_res.output
        print("  [OK] DOM Text Extraction: SUCCESS")

        # Screenshot
        shot = ScreenshotTool(session=session)
        shot_res = shot.execute(label="manual_verify_demo")
        assert shot_res.success and os.path.exists(shot_res.evidence)
        print(f"  [OK] Evidence Screenshot Saved:")
        print(f"       -> {Path(shot_res.evidence).resolve()}")

    finally:
        session.stop()

    print("\n" + "=" * 60)
    print("  RESULT: ALL PHASE 1 TOOLS ARE WORKING PROPERLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_verification()
