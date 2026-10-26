# ⚡ Autonomous Enterprise AI Operator

> **CentrAlign Founding Engineer Technical Submission**  
> An autonomous AI operator that takes high-level business goals and executes them end-to-end across web portals, business documents, enterprise APIs, and corporate policy knowledge bases with strict Human-in-the-Loop (HITL) governance and automated outcome verification.

---

## 🗺️ Architectural Blueprint

The operator operates on a closed **Goal $\to$ Plan $\to$ Execute $\to$ Verify $\to$ Audit** lifecycle:

```
[Business Request]
        │
        ▼
┌──────────────────┐
│  Goal Planner    │ ──► Decomposes request into concrete sub-steps & risk tiers
└──────────────────┘
        │
        ▼
┌──────────────────┐
│  Corporate RAG   │ ──► Retrieves spending limits, SOPs & permissions from ChromaDB
└──────────────────┘
        │
        ▼
┌──────────────────┐     ┌───────────────────────┐
│   ReAct Loop     │ ◄──►│  Tool Abstraction     │ (Browser, PDF/CSV, REST APIs)
└──────────────────┘     └───────────────────────┘
        │
   (If Threshold Exceeded)
        ▼
┌──────────────────┐
│   HITL Gateway   │ ──► Pauses execution for human manager review & authorization
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ Outcome Verifier │ ──► Dual-strategy verification (Database API check + DOM check)
└──────────────────┘
        │
        ▼
┌──────────────────┐
│ Evidence Report  │ ──► Full audit log + timestamped visual screenshot proof
└──────────────────┘
```

---

## 🌟 Key Capabilities

1. **Strategic Goal Decomposition ([`agent/planner.py`](agent/planner.py))**
   - Deconstructs underspecified natural language requests into ordered operational steps.
   - Maps each sub-task to required tools and determines which corporate policies must be checked prior to execution.
   - Assigns risk classifications (`low`, `medium`, `high`) to identify governance decision points.

2. **Persistent Playwright Automation ([`tools/browser_tools.py`](tools/browser_tools.py))**
   - Maintains a persistent `BrowserSession` across multiple tool calls so the agent stays authenticated.
   - Automates forms, selector navigation, button clicks, and DOM text extraction.
   - Full-page timestamped visual screenshot evidence capture for compliance auditing.

3. **Multi-Modal Document Parsing ([`tools/file_tools.py`](tools/file_tools.py))**
   - Ingests commercial vendor invoices from PDF (`pdfplumber` / PyMuPDF) extracting line items, PO references, and totals.
   - Parses structured CSV and Excel corporate expense reports (`pandas`).

4. **Corporate Policy Memory & RAG ([`memory/company_kb.py`](memory/company_kb.py))**
   - Vectorizes standard operating procedures (SOPs), financial approval thresholds, and vendor directories into ChromaDB.
   - AI operator queries policies (`query_company_policy`) before taking any irreversible action.

5. **Human-in-the-Loop (HITL) Governance ([`hitl/approval_gate.py`](hitl/approval_gate.py))**
   - Guardrail policy: Purchases $\ge \$2,000.00$ automatically pause for manager review.
   - Real-time file-based IPC communication with the Operator Control Center.
   - **Enterprise Safety Default**: Automatically defaults to *REJECTED* if human review times out.

6. **Tri-Modal Outcome Verification Engine ([`agent/verifier.py`](agent/verifier.py))**
   - **Strategy 1 (Database Verification)**: Directly queries the backend ERP REST API to audit that records exist with exact dollar amounts.
   - **Strategy 2 (Visual DOM Verification)**: Inspects live page confirmation messages and captures visual proof.
   - **Strategy 3 (LLM Judge)**: Independent evaluation of evidence artifacts against initial success criteria.

7. **Streamlit Operator Control Center ([`dashboard/app.py`](dashboard/app.py))**
   - Dark SaaS aesthetic (Inter + JetBrains Mono).
   - Live step cards, HITL approval banner, real-time log terminal, and visual evidence gallery.

---

## 📂 Repository Structure

```
ai-ticket-agent/
│
├── agent/                         # Core Agent Runtime
│   ├── loop.py                    # Autonomous ReAct loop with tool registry & recovery
│   ├── planner.py                 # Goal decomposition engine
│   ├── verifier.py                # Outcome verification engine
│   └── state.py                   # Agent state machine & audit logger
│
├── tools/                         # Tool Abstraction Layer
│   ├── base.py                    # BaseTool & ToolResult interfaces
│   ├── browser_tools.py           # Playwright automation (navigate, click, type, screenshot)
│   ├── file_tools.py              # PDF invoice & CSV report parsers
│   └── api_tools.py               # REST API HTTP client
│
├── mock_enterprise/               # Simulated Enterprise Environment
│   ├── portal/                    # FastAPI Invoicing & Accounts Payable Portal
│   │   ├── main.py                # FastAPI web server (port 8001)
│   │   ├── templates/             # Modern HTML templates with Playwright target IDs
│   │   └── db.json                # Local JSON ledger database
│   └── data/                      # Sample business documents (Acme Corp PDF, CSVs)
│
├── memory/                        # Corporate Memory (RAG)
│   ├── company_kb.py              # ChromaDB vector store logic & PolicyQueryTool
│   └── knowledge_base/            # SOPs, spending thresholds, vendor catalog
│
├── hitl/                          # Human-in-the-Loop Governance
│   └── approval_gate.py           # Approval request IPC gate
│
├── dashboard/                     # Streamlit Operator Control Center
│   └── app.py                     # Operator dashboard UI
│
├── demo_tasks.py                  # Pre-configured demo scenarios
├── test_tools.py                  # Phase 1 verification suite
├── test_enterprise_portal.py      # Phase 2 verification suite
├── test_agent_runtime.py          # Phase 3 verification suite
├── test_hitl.py                   # Phase 4 verification suite
├── requirements.txt               # Project dependencies
└── .env.example                   # Environment configuration template
```

---

## 🚀 Quick Start Guide

### 1. Environment Setup
```powershell
# Create & activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies & Playwright browser binaries
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment Variables (Optional)
```powershell
cp .env.example .env
```
*(Note: The system includes resilient deterministic fallbacks, allowing full end-to-end execution even without an active OpenAI API key).*

### 3. Launch the Operator Control Center
```powershell
streamlit run dashboard/app.py
```
*(The dashboard automatically detects and manages the background Mock Enterprise Portal at http://127.0.0.1:8001).*

### 4. Run Pre-Configured Demo Scenarios via CLI
```powershell
# Run Scenario A (Acme Corp Invoice - $4,500.00 with manager approval)
python demo_tasks.py --task invoice

# Run Scenario B (Beta Ltd Security Audit - $1,800.00 auto-approved)
python demo_tasks.py --task expense
```

---

## 🧪 Comprehensive Verification Suites

Each phase of the architecture has an automated verification suite:

```powershell
# Test Tool Abstraction Layer (Browser, PDF, CSV, REST API)
python test_tools.py

# Test Mock Enterprise Portal & Playwright End-to-End
python test_enterprise_portal.py

# Test Agent Runtime (Goal Decomposition, ReAct Loop, Outcome Verification)
python test_agent_runtime.py

# Test Human-in-the-Loop (HITL) Governance & Timeout Safeguards
python test_hitl.py
```

---

## 💡 Key Design Decisions & Trade-offs

1. **Persistent Browser Session vs Stateless Requests**:
   - *Decision*: Maintained a persistent Chromium browser context across sequential tool executions.
   - *Rationale*: Enterprise portals require authentication and session state. Re-launching a browser per action is slow and loses authentication cookies.

2. **Tri-Modal Outcome Verification**:
   - *Decision*: Verified goal completion via backend REST API database queries combined with DOM text scanning and LLM judge evaluation.
   - *Rationale*: LLM self-reporting is notoriously prone to hallucinated success. True enterprise automation requires ground-truth proof in the underlying database.

3. **Enterprise Safety Defaults on Timeout**:
   - *Decision*: If an HITL approval request is not answered by a human manager before timeout, the agent defaults to **REJECTION**.
   - *Rationale*: In financial workflows, inaction must never trigger unauthorized fund disbursement.

---

## ⚖️ License
MIT License. Developed for the CentrAlign Founding Engineer Technical Evaluation.
#
