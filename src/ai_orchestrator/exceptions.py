"""
Custom exceptions for the AI Orchestrator library.
"""


class OrchestratorError(Exception):
    """Base exception for all orchestrator errors."""
    pass


class ConfigurationError(OrchestratorError):
    """Raised when configuration is invalid."""
    pass


class AgentError(OrchestratorError):
    """Raised when an agent fails to execute."""

    def __init__(self, agent_name: str, message: str, cause: Exception = None):
        self.agent_name = agent_name
        self.cause = cause
        super().__init__(f"Agent '{agent_name}' error: {message}")


class ConvergenceError(OrchestratorError):
    """Raised when convergence logic fails."""
    pass


class StorageError(OrchestratorError):
    """Raised when storage operations fail."""
    pass


class EngineError(OrchestratorError):
    """Raised when the orchestrator engine fails."""
    pass
