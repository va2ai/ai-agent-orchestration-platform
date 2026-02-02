"""
Pydantic models for execution trace visualization.

These models define the data contract between the backend and the React Flow GUI.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class IssueSeverity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ExecutionIssue(BaseModel):
    """An issue identified during document review."""
    severity: IssueSeverity
    message: str
    category: Optional[str] = None
    suggested_fix: Optional[str] = None


class AgentExecution(BaseModel):
    """Execution details for a single agent in an iteration."""
    name: str
    role: Optional[str] = None
    issues: int = 0
    high_issues: int = 0
    notes: Optional[str] = None
    assessment: Optional[str] = None


class IterationExecution(BaseModel):
    """Execution details for a single iteration."""
    iteration_index: int
    delta: float = 0.0
    issues: List[ExecutionIssue] = Field(default_factory=list)
    issue_counts: Dict[str, int] = Field(default_factory=lambda: {"high": 0, "medium": 0, "low": 0})
    agents: List[AgentExecution] = Field(default_factory=list)
    document_version: int = 1
    document_length: int = 0


class ExecutionTrace(BaseModel):
    """
    Complete execution trace for visualization.

    This is the data contract returned to the React Flow GUI.
    The frontend should only render what it is given - no computation.
    """
    run_id: str
    title: str = ""
    status: str = "pending"  # "pending" | "running" | "completed" | "failed"
    stopped_by: Optional[str] = None  # "no_high_issues" | "max_iterations" | "delta_threshold" | "custom"
    convergence_reason: Optional[str] = None

    # Document info
    initial_document_length: int = 0
    final_document_length: int = 0

    # Execution data
    iterations: List[IterationExecution] = Field(default_factory=list)
    total_iterations: int = 0
    max_iterations: int = 3

    # Participant info
    participants: List[Dict[str, Any]] = Field(default_factory=list)
    moderator_focus: Optional[str] = None

    # Summary
    total_issues_identified: int = 0
    final_issue_counts: Dict[str, int] = Field(default_factory=lambda: {"high": 0, "medium": 0, "low": 0})

    # Timestamps
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class StartOrchestrationRequest(BaseModel):
    """Request to start a new orchestration run."""
    document: str = Field(..., description="The document to refine")
    title: str = Field(default="Untitled", description="Title for the run")
    max_iterations: int = Field(default=3, ge=1, le=10)
    document_type: str = Field(default="document")
    num_participants: int = Field(default=3, ge=2, le=6)
    model: str = Field(default="gpt-4-turbo")
    goal: Optional[str] = None
    participant_style: Optional[str] = None


class OrchestrationStartResponse(BaseModel):
    """Response after starting an orchestration run."""
    run_id: str
    status: str = "started"
    websocket_url: str
