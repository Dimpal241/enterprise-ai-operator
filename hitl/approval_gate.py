# hitl/approval_gate.py
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from tools.base import BaseTool, ToolResult

HITL_DIR = Path("hitl_workspace")
HITL_DIR.mkdir(exist_ok=True)
REQUEST_FILE = HITL_DIR / "pending_request.json"
RESPONSE_FILE = HITL_DIR / "response.json"


@dataclass
class HITLRequest:
    reason: str              # Why is human approval needed?
    data: Dict[str, Any]     # Data the human needs to review (e.g. invoice details)
    risk_level: str = "medium"  # low / medium / high
    recommended_action: str = ""  # What the agent recommends


def request_approval(request: HITLRequest, timeout_seconds: int = 180) -> Tuple[bool, str]:
    """Pause agent execution and request human approval via file-based IPC.

    Returns: (approved: bool, comment: str)
    """
    HITL_DIR.mkdir(exist_ok=True)

    # Write request for dashboard to display
    payload = {
        "reason": request.reason,
        "data": request.data,
        "risk_level": request.risk_level,
        "recommended_action": request.recommended_action,
        "timestamp": time.time(),
    }
    REQUEST_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Clear old response
    if RESPONSE_FILE.exists():
        try:
            RESPONSE_FILE.unlink()
        except Exception:
            pass

    # Wait for response (poll every 1 second)
    start = time.time()
    while time.time() - start < timeout_seconds:
        if RESPONSE_FILE.exists():
            try:
                response = json.loads(RESPONSE_FILE.read_text(encoding="utf-8"))
                REQUEST_FILE.unlink(missing_ok=True)
                RESPONSE_FILE.unlink(missing_ok=True)
                return bool(response.get("approved", False)), response.get("comment", "")
            except Exception:
                pass
        time.sleep(1)

    # Safe default upon timeout: reject
    REQUEST_FILE.unlink(missing_ok=True)
    return False, "Timed out - agent defaulted to rejection for enterprise safety"


def provide_approval(approved: bool, comment: str = "") -> None:
    """Helper used by Dashboard/CLI to answer a pending HITL request."""
    HITL_DIR.mkdir(exist_ok=True)
    RESPONSE_FILE.write_text(
        json.dumps({"approved": approved, "comment": comment, "timestamp": time.time()}),
        encoding="utf-8",
    )


def get_pending_request() -> Optional[Dict[str, Any]]:
    """Return current pending approval request if one exists on disk."""
    if REQUEST_FILE.exists():
        try:
            return json.loads(REQUEST_FILE.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


class HITLTool(BaseTool):
    """Tool allowing AI Operator to pause execution and request human review."""

    name = "request_human_approval"
    description = (
        "Request human manager approval before taking irreversible or high-risk actions, "
        "such as submitting invoices that exceed spending thresholds."
    )

    def execute(self, reason: str, data: Optional[Dict[str, Any]] = None, risk_level: str = "medium", **kwargs) -> ToolResult:
        try:
            req = HITLRequest(
                reason=reason,
                data=data or {},
                risk_level=risk_level,
                recommended_action=kwargs.get("recommended_action", "Approve pending transaction"),
            )
            # In headless automated test mode or environment flag, auto-approve with note
            if "AUTO_APPROVE_TEST" in time.time().__str__() and False:
                pass

            approved, comment = request_approval(req, timeout_seconds=kwargs.get("timeout_seconds", 30))
            if approved:
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=f"Human Approved: {comment or 'Transaction authorized by manager'}",
                )
            else:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=f"Human Denied: {comment}",
                    error=f"Action rejected by human reviewer: {comment}",
                )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"HITL request error: {str(e)}",
            )

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Explanation of why human approval is required (e.g. 'Invoice amount $4500 exceeds $2000 auto-approval limit')",
                        },
                        "data": {
                            "type": "object",
                            "description": "Structured details for the human reviewer",
                        },
                        "risk_level": {
                            "type": "string",
                            "enum": ["low", "medium", "high"],
                            "default": "medium",
                        },
                    },
                    "required": ["reason"],
                },
            },
        }
