# src/jira_to_code/models.py
from typing import Literal, Optional, List, Dict, Any
from pydantic import Field
from openenv.core.env_server import Action, Observation

class JiraCodeAction(Action):
    action_type: Literal[
        "read_file",
        "write_file",
        "list_files",
        "run_tests",
        "submit",
        "human_approved_final",  # matches env.py line 518
        "human_rejected_final",  # matches env.py line 561
    ]
    file_path: Optional[str] = Field(default=None, description="Path to the file to read or write")
    content: Optional[str] = Field(default=None, description="Code content to write to the file")

class JiraCodeObservation(Observation):
    jira_ticket: str = Field(..., description="The objective the agent needs to complete")
    file_tree: List[str] = Field(default_factory=list, description="List of files in the repo")
    current_file_content: Optional[str] = Field(default=None, description="Content of the recently read/written file")
    test_output: Optional[str] = Field(default=None, description="Output from running tests")
    error: Optional[str] = Field(default=None, description="Any system errors (e.g., file not found)")