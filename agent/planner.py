# agent/planner.py
import json
import os
import re
from typing import Any, Dict, Optional

PLANNER_SYSTEM_PROMPT = """You are an enterprise task planner for an autonomous AI operator.

Given a natural language business request and company context, you must:
1. Identify the ultimate goal (what does success look like?).
2. Break the goal into ordered, concrete sub-steps.
3. Identify what tools will be needed (browser_navigate, browser_click, browser_type, read_pdf, read_csv, call_api, query_company_policy, request_human_approval, browser_screenshot).
4. Identify which company policies or SOPs need to be consulted before action.
5. Identify decision points where human approval may be needed.

You must respond with ONLY a valid JSON object matching this schema:
{
    "goal_summary": "One sentence description of the ultimate business goal",
    "success_criteria": "Concrete criteria that must be verified for completion",
    "steps": [
        {"step": 1, "action": "Description of action", "tool": "tool_name", "requires_human": false}
    ],
    "policies_to_check": ["approval_thresholds", "invoicing_policy"],
    "risk_level": "low|medium|high"
}
"""


def _rule_based_fallback_plan(user_request: str) -> Dict[str, Any]:
    """Deterministic fallback planner when LLM API is unavailable or offline."""
    req_lower = user_request.lower()

    if "invoice" in req_lower:
        return {
            "goal_summary": f"Process and register vendor invoice: {user_request.strip()}",
            "success_criteria": "Invoice record appears in ERP database and confirmation screenshot captured",
            "steps": [
                {
                    "step": 1,
                    "action": "Consult corporate spending threshold and invoicing SOPs",
                    "tool": "query_company_policy",
                    "requires_human": False,
                },
                {
                    "step": 2,
                    "action": "Parse vendor invoice PDF to extract vendor name, amount, date, and PO number",
                    "tool": "read_pdf",
                    "requires_human": False,
                },
                {
                    "step": 3,
                    "action": "Navigate to ERP portal and authenticate operator credentials",
                    "tool": "browser_navigate",
                    "requires_human": False,
                },
                {
                    "step": 4,
                    "action": "Evaluate spending policy: request human approval if amount exceeds threshold",
                    "tool": "request_human_approval",
                    "requires_human": True,
                },
                {
                    "step": 5,
                    "action": "Submit verified invoice form on enterprise portal",
                    "tool": "browser_type",
                    "requires_human": False,
                },
                {
                    "step": 6,
                    "action": "Capture screenshot evidence of submission ledger receipt",
                    "tool": "browser_screenshot",
                    "requires_human": False,
                },
                {
                    "step": 7,
                    "action": "Verify database record via ERP REST API",
                    "tool": "call_api",
                    "requires_human": False,
                },
            ],
            "policies_to_check": ["approval_thresholds", "invoicing_policy"],
            "risk_level": "medium",
        }

    return {
        "goal_summary": user_request.strip(),
        "success_criteria": "Requested business action completed and verified with evidence",
        "steps": [
            {
                "step": 1,
                "action": "Check company operational policies and permissions",
                "tool": "query_company_policy",
                "requires_human": False,
            },
            {
                "step": 2,
                "action": "Execute required tool operations",
                "tool": "browser_navigate",
                "requires_human": False,
            },
            {
                "step": 3,
                "action": "Verify outcome and capture evidence",
                "tool": "browser_screenshot",
                "requires_human": False,
            },
        ],
        "policies_to_check": ["permissions"],
        "risk_level": "low",
    }


def decompose_goal(user_request: str, company_context: str = "") -> Dict[str, Any]:
    """Turn a natural language business goal into an ordered, executable plan."""
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("HF_TOKEN") or os.getenv("API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL") or os.getenv("API_BASE_URL")
    model_name = os.getenv("MODEL_NAME") or "gpt-4o"

    if not api_key or api_key in ("dummy", "test", ""):
        return _rule_based_fallback_plan(user_request)

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Company Context:\n{company_context}\n\nUser Request: {user_request}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        content = response.choices[0].message.content or "{}"
        return json.loads(content)
    except Exception as e:
        print(f"[Planner Warning] LLM planning failed ({e}); falling back to deterministic policy planner.")
        return _rule_based_fallback_plan(user_request)
