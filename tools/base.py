# tools/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ToolResult:
    """Standardized result from any tool execution."""
    tool_name: str
    success: bool
    output: Any                  # The actual result
    error: Optional[str] = None     # Error message if failed
    evidence: Optional[str] = None  # Path to screenshot or artifact


class BaseTool(ABC):
    """All tools implement this interface.

    This enables: tool registry, dynamic tool selection,
    consistent error handling, and evidence capture.
    """
    name: str = ""
    description: str = ""   # LLM reads this to decide when to use this tool

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """Execute the tool action with given parameters and return a ToolResult."""
        pass

    def schema(self) -> Dict[str, Any]:
        """Return JSON schema for LLM function/tool calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
