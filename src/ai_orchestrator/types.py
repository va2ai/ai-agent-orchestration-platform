"""
Core types for the AI Orchestrator library.

These types define the public API contract for the library.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence


class Severity(str, Enum):
    """Issue severity levels."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Issue:
    """An issue identified during document review."""
    category: str
    description: str
    severity: Severity
    suggested_fix: Optional[str] = None
    reviewer: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "severity": self.severity.value,
            "suggested_fix": self.suggested_fix,
            "reviewer": self.reviewer,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Issue":
        severity = data.get("severity", "Medium")
        if isinstance(severity, str):
            severity = Severity(severity)
        return cls(
            category=data.get("category", ""),
            description=data.get("description", ""),
            severity=severity,
            suggested_fix=data.get("suggested_fix"),
            reviewer=data.get("reviewer", ""),
        )


@dataclass
class Review:
    """A review from a single agent."""
    reviewer_name: str
    issues: List[Issue]
    overall_assessment: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reviewer_name": self.reviewer_name,
            "issues": [i.to_dict() for i in self.issues],
            "overall_assessment": self.overall_assessment,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Review":
        issues = [Issue.from_dict(i) for i in data.get("issues", [])]
        return cls(
            reviewer_name=data.get("reviewer_name", ""),
            issues=issues,
            overall_assessment=data.get("overall_assessment", ""),
            timestamp=data.get("timestamp", datetime.now().isoformat()),
        )


@dataclass
class RoundtableIteration:
    """Result from a single iteration of the roundtable."""
    iteration_index: int
    input_document: str
    output_document: str
    reviews: List[Review]
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def all_issues(self) -> List[Issue]:
        """Get all issues from all reviews."""
        issues = []
        for review in self.reviews:
            issues.extend(review.issues)
        return issues

    @property
    def high_severity_count(self) -> int:
        """Count of high severity issues."""
        return sum(1 for i in self.all_issues if i.severity == Severity.HIGH)


@dataclass
class StopDecision:
    """Decision about whether to stop the roundtable loop."""
    should_stop: bool
    reason: str
    stopped_by: str  # "no_high_issues", "max_iterations", "delta_threshold", "custom"


@dataclass
class RoundtableConfig:
    """Configuration for running a roundtable session."""
    max_iterations: int = 3
    delta_threshold: float = 0.05  # Stop if document change < 5%
    stop_on_no_high_issues: bool = True
    verbose: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Optional custom stop condition
    custom_stop_condition: Optional[Callable[[List[RoundtableIteration]], StopDecision]] = None


@dataclass
class RoundtableResult:
    """Final result from a roundtable session."""
    session_id: str
    title: str
    initial_document: str
    final_document: str
    initial_version: int
    final_version: int
    iterations: List[RoundtableIteration]
    converged: bool
    convergence_reason: str
    stopped_by: str
    total_issues_identified: int
    final_issue_count: Dict[str, int]  # {"high": 0, "medium": 3, "low": 5}
    token_usage: Dict[str, int] = field(default_factory=dict)
    timestamps: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "title": self.title,
            "initial_version": self.initial_version,
            "final_version": self.final_version,
            "iterations": len(self.iterations),
            "converged": self.converged,
            "convergence_reason": self.convergence_reason,
            "stopped_by": self.stopped_by,
            "total_issues_identified": self.total_issues_identified,
            "final_issue_count": self.final_issue_count,
            "token_usage": self.token_usage,
            "timestamps": self.timestamps,
            "metadata": self.metadata,
            "history": [
                {
                    "iteration": it.iteration_index,
                    "issues_count": len(it.all_issues),
                    "high_count": it.high_severity_count,
                    "notes": it.notes,
                }
                for it in self.iterations
            ],
        }


class Agent(Protocol):
    """Protocol for agents that participate in a roundtable."""

    @property
    def name(self) -> str:
        """Agent name/identifier."""
        ...

    def review(self, document: str, context: Optional[Dict[str, Any]] = None) -> Review:
        """Review a document and return issues found."""
        ...


class Moderator(Protocol):
    """Protocol for moderators that refine documents based on reviews."""

    def refine(
        self,
        document: str,
        reviews: Sequence[Review],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Refine a document based on reviews."""
        ...


class OrchestratorEngine(Protocol):
    """Protocol for the engine that executes a single roundtable step."""

    def step(
        self,
        document: str,
        agents: Sequence[Agent],
        moderator: Moderator,
        context: Optional[Dict[str, Any]] = None,
        iteration_index: int = 0,
    ) -> RoundtableIteration:
        """Execute a single roundtable iteration."""
        ...
