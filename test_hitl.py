# test_hitl.py
r"""Manual Verification Script for Phase 4: Human-in-the-Loop (HITL) Module

Run with:
    .\.venv\Scripts\python test_hitl.py
"""

import os
import sys
import time
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from hitl import (
    HITLRequest,
    HITLTool,
    request_approval,
    provide_approval,
    get_pending_request,
)


def run_hitl_verification():
    print("=" * 65)
    print("  PHASE 4 MANUAL VERIFICATION: HUMAN-IN-THE-LOOP GATEWAY")
    print("=" * 65)

    # 1. Verify HITLTool Schema
    print("\n[1/3] Verifying HITL Tool Schema for LLM Calling...")
    tool = HITLTool()
    schema = tool.schema()
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "request_human_approval"
    print(f"  [OK] Tool registered: {tool.name}")
    print(f"  [OK] Parameters: {list(schema['function']['parameters']['properties'].keys())}")

    # 2. Verify Approval Handshake (IPC via hitl_workspace/)
    print("\n[2/3] Simulating Human Manager Approval Handshake...")
    
    def simulate_human_manager():
        time.sleep(1.0)
        pending = get_pending_request()
        assert pending is not None, "Pending request file was not created on disk!"
        print(f"  -> Human reviewer detected pending request on disk:")
        print(f"     Reason: '{pending['reason']}'")
        print(f"     Invoice Amount: ${pending['data'].get('amount')}")
        print(f"     Risk Level: {pending['risk_level'].upper()}")
        print(f"  -> Reviewer clicking 'APPROVE' with note...")
        provide_approval(approved=True, comment="Authorized by Finance Director")

    t = threading.Thread(target=simulate_human_manager)
    t.start()

    req = HITLRequest(
        reason="Acme Corp invoice ($4,500.00) exceeds $2,000 auto-approval threshold",
        data={"vendor": "Acme Corporation", "amount": 4500.00, "po": "PO-2024-883"},
        risk_level="medium",
        recommended_action="Authorize payment under Q4 cloud infrastructure allocation",
    )
    
    approved, comment = request_approval(req, timeout_seconds=10)
    t.join()

    assert approved is True
    print(f"  [OK] Agent received approval: {approved}")
    print(f"  [OK] Reviewer comment: '{comment}'")

    # 3. Verify Enterprise Safety Default (Timeout -> Automatic Reject)
    print("\n[3/3] Testing Enterprise Safety Fallback (Timeout -> Safe Rejection)...")
    timeout_req = HITLRequest(
        reason="Unrecognized vendor invoice requiring audit",
        data={"vendor": "Unknown Corp", "amount": 9900.00},
        risk_level="high",
    )
    # 2 second timeout with no reviewer response
    start_t = time.time()
    auto_rejected, rej_comment = request_approval(timeout_req, timeout_seconds=2)
    duration = time.time() - start_t

    assert auto_rejected is False
    assert "Timed out" in rej_comment
    print(f"  [OK] Unanswered request automatically rejected in {duration:.1f}s for enterprise safety.")
    print(f"  [OK] Rejection reason: '{rej_comment}'")

    print("\n" + "=" * 65)
    print("  RESULT: PHASE 4 HITL APPROVAL GATEWAY FULLY OPERATIONAL!")
    print("=" * 65)


if __name__ == "__main__":
    run_hitl_verification()
