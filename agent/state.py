# agent/state.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentStatus(str, Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    AWAITING_HUMAN = "awaiting_human"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentState:
    """Complete snapshot of agent state at any point in time.

    Maintaining full state enables:
    - Resumability after failure
    - Full auditability
    - Human inspection at any step
    - Dashboard rendering
    """
    goal: str
    status: AgentStatus = AgentStatus.IDLE
    step_count: int = 0
    max_steps: int = 25

    plan: List[Dict[str, Any]] = field(default_factory=list)      # Decomposed goal steps
    completed_steps: List[int] = field(default_factory=list)

    messages: List[Dict[str, Any]] = field(default_factory=list)  # LLM conversation history
    action_log: List[Dict[str, Any]] = field(default_factory=list)  # Full audit trail

    retrieved_data: Dict[str, Any] = field(default_factory=dict)  # Data extracted during execution
    evidence: List[str] = field(default_factory=list)             # Screenshot / artifact paths

    error_count: int = 0
    last_error: Optional[str] = None

    verified: bool = False
    verification_details: Optional[Dict[str, Any]] = None
    final_summary: Optional[str] = None

    def record_action(
        self,
        tool_name: str,
        params: Dict[str, Any],
        output: Any,
        success: bool,
        error: Optional[str] = None,
        evidence: Optional[str] = None,
        thought: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Add an entry to the complete audit trail."""
        import datetime

        entry = {
            "step": self.step_count,
            "tool": tool_name,
            "params": params,
            "output": output,
            "success": success,
            "error": error,
            "evidence": evidence,
            "thought": thought,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.action_log.append(entry)
        if evidence and evidence not in self.evidence:
            self.evidence.append(evidence)
        return entry
