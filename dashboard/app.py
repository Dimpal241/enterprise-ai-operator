# dashboard/app.py
"""CentrAlign AI Operator Control Center.

Streamlit Frontend for Autonomous Enterprise AI Operator:
- Goal Input & Pre-configured Scenarios
- Live ReAct Execution Loop & Step Cards
- Human-in-the-Loop (HITL) Governance & Approval Center
- Visual Evidence Gallery (Playwright Screenshots)
- Outcome Verification & Audit Trail Report
- Corporate Policy Knowledge Base (ChromaDB)
"""

import datetime
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from agent.loop import EnterpriseAgentLoop
from agent.planner import decompose_goal
from agent.state import AgentState, AgentStatus
from hitl.approval_gate import get_pending_request, provide_approval
from memory.company_kb import query_company_policy

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CentrAlign AI Operator Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling — Dark SaaS Operator Theme (Inter + JetBrains Mono)
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [data-testid="stApp"] {
    background: #0B0E14;
    color: #E2E8F0;
    font-family: 'Inter', sans-serif;
}

[data-testid="stSidebar"] {
    background: #111622 !important;
    border-right: 1px solid #1E293B !important;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background: #151C2C;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 14px 20px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
[data-testid="stMetricValue"] {
    color: #F8FAFC !important;
    font-weight: 800;
    font-size: 1.6rem !important;
}
[data-testid="stMetricLabel"] {
    color: #94A3B8 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 1px;
    font-weight: 600;
}

/* Custom Cards */
.panel-card {
    background: #151C2C;
    border: 1px solid #1E293B;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
}

.step-card {
    background: #151C2C;
    border: 1px solid #1E293B;
    border-left: 4px solid #3B82F6;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
    font-size: 0.88rem;
    line-height: 1.5;
}
.step-card.success { border-left-color: #10B981; }
.step-card.hitl { border-left-color: #F59E0B; }
.step-card.failed { border-left-color: #EF4444; }

.tool-badge {
    display: inline-block;
    background: #1E293B;
    color: #38BDF8;
    padding: 3px 8px;
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    font-weight: 600;
    margin-bottom: 6px;
}

.hitl-alert {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid #F59E0B;
    border-radius: 12px;
    padding: 20px;
    margin: 16px 0;
}

.log-terminal {
    background: #06080C;
    border: 1px solid #1E293B;
    border-radius: 8px;
    padding: 14px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    color: #94A3B8;
    max-height: 260px;
    overflow-y: auto;
    white-space: pre-wrap;
}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Background Enterprise Portal Management
# ---------------------------------------------------------------------------
def ensure_mock_portal_running():
    """Ensure mock enterprise portal is running on port 8001."""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    is_open = sock.connect_ex(("127.0.0.1", 8001)) == 0
    sock.close()

    if not is_open:
        import uvicorn
        from mock_enterprise.portal.main import app as portal_app
        config = uvicorn.Config(portal_app, host="127.0.0.1", port=8001, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        time.sleep(1)


ensure_mock_portal_running()


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
if "agent_state" not in st.session_state:
    st.session_state.agent_state = None
if "is_running" not in st.session_state:
    st.session_state.is_running = False
if "execution_logs" not in st.session_state:
    st.session_state.execution_logs = []
if "selected_goal" not in st.session_state:
    st.session_state.selected_goal = (
        "There is a pending invoice from Acme Corp in mock_enterprise/data/invoice_acme_corp.pdf. "
        "Check our company policy on spending approval, extract the invoice details, log into the "
        "company portal at http://127.0.0.1:8001, enter the invoice, and pause for manager approval if needed."
    )


# ---------------------------------------------------------------------------
# Header Section
# ---------------------------------------------------------------------------
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.title("⚡ CentrAlign AI Operator")
    st.caption("Autonomous Enterprise AI Employee · Goal Decomposition · Playwright Browser Automation · Outcome Verification")
with col_h2:
    st.markdown(
        """
        <div style="text-align:right; margin-top:14px;">
            <span style="background:#10B981; color:#064E3B; font-weight:700; font-size:11px; padding:4px 10px; border-radius:12px;">SYSTEM READY</span>
            <div style="font-size:12px; color:#94A3B8; margin-top:4px;">Portal: <a href="http://127.0.0.1:8001" target="_blank" style="color:#38BDF8;">http://127.0.0.1:8001</a></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")


# ---------------------------------------------------------------------------
# Real-time Metrics Bar
# ---------------------------------------------------------------------------
m1, m2, m3, m4 = st.columns(4)
current_state: Optional[AgentState] = st.session_state.agent_state

status_text = current_state.status.value.upper() if current_state else "IDLE"
step_count = f"{current_state.step_count} Steps" if current_state else "0 Steps"
verified_text = "VERIFIED (100%)" if (current_state and current_state.verified) else ("AWAITING" if current_state else "READY")
evidence_count = f"{len(current_state.evidence)} Screenshot(s)" if current_state else "0 Artifacts"

with m1:
    st.metric("Operator Status", status_text)
with m2:
    st.metric("Execution Progress", step_count)
with m3:
    st.metric("Outcome Verification", verified_text)
with m4:
    st.metric("Evidence Captured", evidence_count)

st.write("")


# ---------------------------------------------------------------------------
# Sidebar: Corporate Knowledge Base & Policy Search
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📚 Corporate Memory (RAG)")
    st.caption("ChromaDB vector store containing company SOPs, limits, and vendor rules.")

    kb_query = st.text_input("Search Company Policies", placeholder="e.g. invoice approval thresholds")
    if kb_query:
        policy_result = query_company_policy(kb_query, n_results=2)
        st.markdown("**Retrieved Policy Guidance:**")
        st.info(policy_result[:600] + ("..." if len(policy_result) > 600 else ""))

    st.markdown("---")
    st.markdown("### 📑 Policy Documents")
    st.markdown("- [x] `SOP-FIN-2024-001`: Approval Thresholds")
    st.markdown("- [x] `SOP-AP-2024-002`: Invoicing SOP")
    st.markdown("- [x] `vendor_catalog.json`: 3 Active Vendors")
    st.markdown("- [x] `permissions.json`: Operator Guardrails")

    st.markdown("---")
    st.markdown("### ⚙️ Quick Actions")
    if st.button("🔄 Reset Portal DB", use_container_width=True):
        from tools import APICallTool
        APICallTool().execute(url="http://127.0.0.1:8001/api/reset", method="POST")
        st.success("Ledger reset to baseline!")

    if st.button("🗑️ Clear Screenshots", use_container_width=True):
        import shutil
        sc_dir = ROOT_DIR / "evidence" / "screenshots"
        if sc_dir.exists():
            for f in sc_dir.glob("*.png"):
                try:
                    f.unlink()
                except Exception:
                    pass
        st.success("Evidence cleared.")


# ---------------------------------------------------------------------------
# Main View: Two Column Layout
# ---------------------------------------------------------------------------
left_col, right_col = st.columns([1.1, 1.0], gap="large")

with left_col:
    # -----------------------------------------------------------------------
    # Panel 1: Goal Input & Scenario Selector
    # -----------------------------------------------------------------------
    st.subheader("🎯 Goal Specification")

    scenario = st.selectbox(
        "Load Pre-Configured Demo Scenario:",
        [
            "Scenario A: Acme Corp Invoice ($4,500.00 — Requires Manager Review)",
            "Scenario B: Beta Ltd Security Testing ($1,800.00 — Auto-Approved)",
            "Scenario C: Employee Expense Claims Review & Flagging",
            "Custom Goal Input",
        ],
    )

    if "Scenario A" in scenario:
        goal_text = (
            "There is a pending invoice from Acme Corp in mock_enterprise/data/invoice_acme_corp.pdf. "
            "Check our company policy on spending approval, extract the invoice details, log into the "
            "company portal at http://127.0.0.1:8001, enter the invoice, and pause for manager approval if needed."
        )
    elif "Scenario B" in scenario:
        goal_text = (
            "Process the security penetration testing invoice at mock_enterprise/data/invoice_beta_ltd.pdf. "
            "Check company spending thresholds, submit to the accounts payable portal at http://127.0.0.1:8001, "
            "and verify that it is automatically approved without needing human escalation."
        )
    elif "Scenario C" in scenario:
        goal_text = (
            "Review the employee expense claims in mock_enterprise/data/employee_expense_report.csv. "
            "Identify expenses exceeding standard guidelines, log approved entries into the ERP system, "
            "and generate a visual verification report."
        )
    else:
        goal_text = st.session_state.selected_goal

    goal_input = st.text_area("Business Request (Natural Language):", value=goal_text, height=110)

    col_btn1, col_btn2 = st.columns([1, 1])
    with col_btn1:
        run_btn = st.button("🚀 Execute Business Goal", type="primary", use_container_width=True)
    with col_btn2:
        auto_hitl = st.checkbox("Auto-Approve HITL Gates (Fast Demo)", value=True)

    # -----------------------------------------------------------------------
    # Agent Execution Trigger
    # -----------------------------------------------------------------------
    if run_btn:
        st.session_state.is_running = True
        st.session_state.execution_logs = []
        progress_bar = st.progress(0, text="Initializing Enterprise AI Operator...")

        operator = EnterpriseAgentLoop(max_steps=20)
        time.sleep(0.5)

        progress_bar.progress(25, text="Decomposing goal into structured execution plan...")
        time.sleep(0.5)

        progress_bar.progress(50, text="Executing tools (browser, PDF parsing, policy checks)...")
        final_state = operator.run(
            goal=goal_input,
            company_context="Acme Corp is an active approved vendor. Threshold for review is $2000.",
            auto_approve_hitl=auto_hitl,
        )

        progress_bar.progress(100, text="Execution completed & verified!")
        st.session_state.agent_state = final_state
        st.session_state.is_running = False
        st.rerun()

    # -----------------------------------------------------------------------
    # Panel 2: Human-in-the-Loop (HITL) Approval Center
    # -----------------------------------------------------------------------
    pending_hitl = get_pending_request()
    if pending_hitl:
        st.markdown(
            f"""
            <div class="hitl-alert">
                <div style="font-size:1.1rem; font-weight:700; color:#F59E0B; margin-bottom:8px;">
                    ⚠️ HUMAN APPROVAL REQUIRED (Risk Level: {pending_hitl.get('risk_level', 'MEDIUM').upper()})
                </div>
                <div style="font-size:0.92rem; color:#F8FAFC; margin-bottom:12px;">
                    <strong>Reason:</strong> {pending_hitl.get('reason')}
                </div>
                <div style="font-size:0.84rem; color:#CBD5E1; margin-bottom:14px;">
                    <strong>Recommendation:</strong> {pending_hitl.get('recommended_action', 'Authorize invoice entry under Q4 allocated budget.')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Show transaction payload
        if pending_hitl.get("data"):
            st.json(pending_hitl["data"])

        hitl_comment = st.text_input("Reviewer Notes / Authorization ID", value="Approved by Department Director", key="hitl_note")
        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("✅ AUTHORIZE TRANSACTION", type="primary", use_container_width=True):
                provide_approval(approved=True, comment=hitl_comment)
                st.success("Approval granted. Agent resuming...")
                time.sleep(1)
                st.rerun()
        with btn_c2:
            if st.button("❌ REJECT & HALT", use_container_width=True):
                provide_approval(approved=False, comment=hitl_comment or "Transaction declined by manager.")
                st.error("Transaction rejected. Agent halting.")
                time.sleep(1)
                st.rerun()

    # -----------------------------------------------------------------------
    # Panel 3: Live Action Log & Step Cards
    # -----------------------------------------------------------------------
    st.subheader("📋 Operator Actions & Audit Trail")

    if current_state and current_state.action_log:
        for entry in current_state.action_log:
            step_no = entry.get("step", 1)
            tool_name = entry.get("tool", "action")
            is_ok = entry.get("success", True)
            thought = entry.get("thought", "")
            output = str(entry.get("output", ""))[:140]

            card_class = "success" if is_ok else "failed"
            if tool_name == "request_human_approval":
                card_class = "hitl"

            icon = "✓" if is_ok else "✗"
            if tool_name == "request_human_approval":
                icon = "👤"

            st.markdown(
                f"""
                <div class="step-card {card_class}">
                    <span class="tool-badge">{tool_name}</span>
                    <strong style="color:#F8FAFC; margin-left:8px;">Step {step_no}</strong>
                    <div style="color:#94A3B8; font-style:italic; margin-top:4px;">{thought or 'Executing step...'}</div>
                    <div style="color:#CBD5E1; font-family:'JetBrains Mono',monospace; font-size:0.8rem; margin-top:6px;">
                        {icon} {output}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("No active run yet. Select a scenario above and click 'Execute Business Goal'.")


with right_col:
    # -----------------------------------------------------------------------
    # Panel 4: Outcome Verification Report
    # -----------------------------------------------------------------------
    st.subheader("🔍 Outcome Verification Report")

    if current_state and current_state.verified:
        details = current_state.verification_details or {}
        st.success(f"**GOAL COMPLETED & AUDITED**\n\n{details.get('details', 'Outcome verified against ERP database.')}")

        v1, v2 = st.columns(2)
        with v1:
            st.markdown(f"**Verification Method:** `{details.get('method', 'database_check')}`")
            st.markdown(f"**Confidence Score:** `{details.get('confidence', 1.0) * 100:.0f}%`")
        with v2:
            st.markdown(f"**Status Tier:** `{current_state.retrieved_data.get('vendor', 'Acme Corp')}`")
            st.markdown(f"**Approval Gate:** `PASSED`")

        if details.get("evidence"):
            with st.expander("Ledger Entry Record (Live Database Proof)", expanded=True):
                st.json(details["evidence"])
    elif current_state:
        st.warning("Verification Pending or Execution Incomplete.")
    else:
        st.markdown(
            """
            <div class="panel-card" style="text-align:center; padding:30px;">
                <div style="font-size:2rem; margin-bottom:10px;">🔍</div>
                <div style="font-weight:600; color:#F8FAFC;">Verification Engine Ready</div>
                <div style="font-size:0.85rem; color:#94A3B8; margin-top:6px;">
                    The verifier will cross-check the database record via REST API and inspect DOM confirmation text automatically.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # Panel 5: Visual Evidence Gallery (Playwright Screenshots)
    # -----------------------------------------------------------------------
    st.subheader("📸 Visual Evidence Gallery")

    evidence_dir = ROOT_DIR / "evidence" / "screenshots"
    screenshots = sorted(evidence_dir.glob("*.png"), key=os.path.getmtime, reverse=True) if evidence_dir.exists() else []

    if screenshots:
        selected_shot = screenshots[0]
        st.image(str(selected_shot), caption=f"Latest Evidence: {selected_shot.stem}", use_container_width=True)

        if len(screenshots) > 1:
            with st.expander(f"📁 Additional Evidence Snapshots ({len(screenshots)} total)", expanded=False):
                cols = st.columns(min(3, len(screenshots) - 1))
                for idx, extra_shot in enumerate(screenshots[1:4]):
                    with cols[idx]:
                        st.image(str(extra_shot), caption=extra_shot.stem[:24], use_container_width=True)
    else:
        st.markdown(
            """
            <div class="panel-card" style="text-align:center; padding:30px;">
                <div style="font-size:2rem; margin-bottom:10px;">📸</div>
                <div style="font-weight:600; color:#F8FAFC;">Evidence Capture Ready</div>
                <div style="font-size:0.85rem; color:#94A3B8; margin-top:6px;">
                    Browser screenshots captured during execution will be rendered here as audit evidence.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
