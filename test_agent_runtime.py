# test_agent_runtime.py
r"""Manual & Automated Verification Script for Phase 3: Rebuild the Agent Runtime

Run with:
    .\.venv\Scripts\python test_agent_runtime.py
"""

import sys
import time
import threading
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from agent import AgentState, AgentStatus, EnterpriseAgentLoop, OutcomeVerifier, decompose_goal
from mock_enterprise.portal.main import app as portal_app


def test_phase_3():
    print("=" * 65)
    print("  PHASE 3 VERIFICATION: ENTERPRISE AGENT RUNTIME")
    print("=" * 65)

    # 1. Test Goal Decomposition (Planner)
    print("\n[1/4] Testing Goal Decomposition (agent/planner.py)...")
    goal = "Process vendor invoice for Acme Corporation located in mock_enterprise/data/invoice_acme_corp.pdf and submit to ERP"
    plan = decompose_goal(goal)
    assert "steps" in plan and len(plan["steps"]) >= 4, "Planner failed to decompose goal"
    print(f"  [OK] Goal decomposed into {len(plan['steps'])} structured sub-steps:")
    for s in plan["steps"]:
        print(f"       Step {s.get('step')}: [{s.get('tool')}] {s.get('action')}")

    # 2. Test Agent State Machine
    print("\n[2/4] Testing Agent State Machine (agent/state.py)...")
    state = AgentState(goal=goal)
    assert state.status == AgentStatus.IDLE
    state.status = AgentStatus.PLANNING
    state.record_action(
        tool_name="query_company_policy",
        params={"question": "thresholds"},
        output="Under $2000 auto-approved; >= $2000 requires manager review",
        success=True,
        thought="Checking corporate limits.",
    )
    assert len(state.action_log) == 1
    print("  [OK] State transitions and audit logging verified.")

    # 3. Start In-Process Mock Enterprise Portal
    print("\n[3/4] Starting Mock Enterprise Portal on http://127.0.0.1:8001...")
    config = uvicorn.Config(portal_app, host="127.0.0.1", port=8001, log_level="warning")
    portal_server = uvicorn.Server(config)
    server_thread = threading.Thread(target=portal_server.run, daemon=True)
    server_thread.start()
    time.sleep(1.5)

    try:
        # 4. Run Complete Enterprise Agent Loop
        print("\n[4/4] Executing Enterprise Agent Loop (agent/loop.py)...")
        operator = EnterpriseAgentLoop(max_steps=15)
        final_state = operator.run(
            goal=goal,
            company_context="Acme Corp is an approved vendor. Threshold for review is $2000.",
            auto_approve_hitl=True,
        )

        print("\n  [Execution Audit Trail Summary]")
        for entry in final_state.action_log:
            print(f"   -> Step {entry['step']}: {entry['tool']} (Success: {entry['success']})")

        print(f"\n  [OK] Agent Status: {final_state.status.value.upper()}")
        print(f"  [OK] Outcome Verified: {final_state.verified}")
        print(f"  [OK] Verification Details: {final_state.verification_details.get('details')}")
        if final_state.evidence:
            print(f"  [OK] Captured Evidence File: {final_state.evidence[-1]}")

        assert final_state.status == AgentStatus.COMPLETED, f"Agent ended in state {final_state.status}"
        assert final_state.verified, "Outcome verification failed"

    finally:
        portal_server.should_exit = True

    print("\n" + "=" * 65)
    print("  RESULT: PHASE 3 AGENT RUNTIME 100% OPERATIONAL & VERIFIED!")
    print("=" * 65)


if __name__ == "__main__":
    test_phase_3()
