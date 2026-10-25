# demo_tasks.py
r"""Pre-configured demo scenarios for the CentrAlign AI Operator.

Usage:
    .\.venv\Scripts\python demo_tasks.py --task invoice
    .\.venv\Scripts\python demo_tasks.py --task expense
"""

import argparse
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from agent.loop import EnterpriseAgentLoop
from memory.company_kb import index_company_documents

DEMO_TASKS = {
    "invoice": {
        "title": "Scenario A: Vendor Invoice Ingestion & Approval",
        "goal": (
            "There is a pending invoice from Acme Corp in the mock_enterprise/data/ folder. "
            "Check our company policy on spending approval, extract the invoice details, "
            "log into the company portal at http://127.0.0.1:8001 using username 'agent' and password 'company123', "
            "enter the invoice into the system, and tell me whether it needs manager approval before payment. "
            "If it does, pause and ask me before submitting."
        ),
        "context": (
            "Acme Corporation is an approved cloud vendor in vendor_catalog.json. "
            "According to SOP-FIN-2024-001, any purchase >= $2,000 requires human manager review."
        ),
    },
    "expense": {
        "title": "Scenario B: Employee Expense Audit & Flagging",
        "goal": (
            "Review the employee expense report at mock_enterprise/data/employee_expense_report.csv, "
            "check which expenses exceed our reimbursement guidelines, log the entries into the "
            "company portal at http://127.0.0.1:8001, and capture verification proof."
        ),
        "context": (
            "Standard department expense limit is $500.00 without prior executive sign-off."
        ),
    },
}


def ensure_mock_portal_running():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_open = sock.connect_ex(("127.0.0.1", 8001)) == 0
    sock.close()

    if not is_open:
        import uvicorn
        from mock_enterprise.portal.main import app as portal_app
        import threading
        config = uvicorn.Config(portal_app, host="127.0.0.1", port=8001, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1)


def run_demo(task_name: str = "invoice", auto_approve: bool = True):
    print("=" * 65)
    print("  CENTRALIGN AI OPERATOR: LIVE DEMO RUNNER")
    print("=" * 65)

    ensure_mock_portal_running()

    print("\n[1/3] Refreshing Corporate Memory & Vector Indices...")
    index_company_documents()

    task = DEMO_TASKS.get(task_name)
    if not task:
        print(f"Unknown task: {task_name}. Choose from: {list(DEMO_TASKS.keys())}")
        return

    print(f"\n[2/3] Initiating Demo: {task['title']}")
    print(f"Goal: {task['goal']}\n")

    operator = EnterpriseAgentLoop(max_steps=20)
    final_state = operator.run(
        goal=task["goal"],
        company_context=task["context"],
        auto_approve_hitl=auto_approve,
    )

    print("\n[3/3] Execution Summary & Outcome Verification:")
    print(f"  -> Final Status: {final_state.status.value.upper()}")
    print(f"  -> Steps Executed: {final_state.step_count}")
    print(f"  -> Outcome Verified: {final_state.verified}")
    print(f"  -> Verification Report: {final_state.verification_details.get('details')}")

    if final_state.evidence:
        print(f"  -> Visual Screenshot Proof: {final_state.evidence[-1]}")

    print("\n" + "=" * 65)
    print("  DEMO EXECUTION COMPLETE!")
    print("=" * 65)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CentrAlign AI Operator Demo Runner")
    parser.add_argument("--task", choices=list(DEMO_TASKS.keys()), default="invoice")
    parser.add_argument("--require-human", action="store_true", help="Pause for manual HITL approval via CLI or Dashboard")
    args = parser.parse_args()

    run_demo(task_name=args.task, auto_approve=not args.require_human)
