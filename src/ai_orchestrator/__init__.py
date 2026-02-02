"""
AI Orchestrator - Reusable AI agent orchestration library for iterative document refinement.

This library provides a framework for running AI agent "roundtables" where multiple
critic agents review a document and a moderator refines it based on their feedback.

Public API:
-----------
- run_roundtable(): The main entry point for running a refinement session
- RoundtableConfig: Configuration for the roundtable session
- RoundtableResult: The result of a roundtable session

Types:
------
- Agent: Protocol for review agents
- Moderator: Protocol for document refinement
- Issue: An issue found during review
- Review: A collection of issues from one agent
- Severity: Issue severity levels (HIGH, MEDIUM, LOW)

Convergence:
------------
- decide_stop(): Core convergence decision function
- ConvergenceChecker: Class-based interface for backwards compatibility

Example:
--------
    from ai_orchestrator import run_roundtable, RoundtableConfig

    result = run_roundtable(
        document="# My PRD\\n\\nBuild a chatbot...",
        agents=[product_critic, engineering_critic],
        moderator=prd_moderator,
        config=RoundtableConfig(max_iterations=3),
        title="AI Chatbot PRD",
    )

    print(f"Final document: {result.final_document}")
    print(f"Converged: {result.converged}")
"""

__version__ = "0.1.0"

# Public API - Main function
from .orchestration.runner import run_roundtable, DefaultEngine

# Public API - Configuration and Result types
from .types import (
    RoundtableConfig,
    RoundtableResult,
    RoundtableIteration,
    StopDecision,
    Agent,
    Moderator,
    OrchestratorEngine,
    Issue,
    Review,
    Severity,
)

# Public API - Convergence
from .convergence import (
    decide_stop,
    has_high_severity_issues,
    calculate_document_delta,
    count_issues_by_severity,
    ConvergenceChecker,
)

# Public API - Exceptions
from .exceptions import (
    OrchestratorError,
    ConfigurationError,
    AgentError,
    ConvergenceError,
    StorageError,
    EngineError,
)

# Public API - Logging
from .logging import OrchestratorLogger, create_logger

__all__ = [
    # Version
    "__version__",
    # Main function
    "run_roundtable",
    "DefaultEngine",
    # Types
    "RoundtableConfig",
    "RoundtableResult",
    "RoundtableIteration",
    "StopDecision",
    "Agent",
    "Moderator",
    "OrchestratorEngine",
    "Issue",
    "Review",
    "Severity",
    # Convergence
    "decide_stop",
    "has_high_severity_issues",
    "calculate_document_delta",
    "count_issues_by_severity",
    "ConvergenceChecker",
    # Exceptions
    "OrchestratorError",
    "ConfigurationError",
    "AgentError",
    "ConvergenceError",
    "StorageError",
    "EngineError",
    # Logging
    "OrchestratorLogger",
    "create_logger",
]
