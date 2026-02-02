"""
Logging utilities for the AI Orchestrator library.

Provides structured logging for orchestration sessions with:
- Console output (with optional verbosity control)
- File-based logging
- Token usage tracking
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class OrchestratorLogger:
    """Logger for orchestration sessions."""

    def __init__(
        self,
        session_id: str,
        log_dir: Optional[str] = None,
        verbose: bool = False,
        console_output: bool = True,
    ):
        self.session_id = session_id
        self.verbose = verbose
        self.console_output = console_output
        self.token_usage: Dict[str, int] = {}

        # Set up log directory
        if log_dir:
            self.log_dir = Path(log_dir) / session_id
        else:
            self.log_dir = Path("data") / "logs" / session_id

        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up file logger
        self._setup_file_logger()

    def _setup_file_logger(self):
        """Set up file-based logging."""
        self.logger = logging.getLogger(f"orchestrator.{self.session_id}")
        self.logger.setLevel(logging.DEBUG)

        # Clear existing handlers
        self.logger.handlers = []

        # File handler
        log_file = self.log_dir / "refinement.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

    def info(self, message: str):
        """Log info message."""
        self.logger.info(message)
        if self.console_output and self.verbose:
            print(f"  {message}")

    def debug(self, message: str):
        """Log debug message."""
        self.logger.debug(message)
        if self.console_output and self.verbose:
            print(f"    [DEBUG] {message}")

    def warning(self, message: str):
        """Log warning message."""
        self.logger.warning(message)
        if self.console_output:
            print(f"  [WARNING] {message}")

    def error(self, message: str):
        """Log error message."""
        self.logger.error(message)
        if self.console_output:
            print(f"  [ERROR] {message}", file=sys.stderr)

    def section(self, title: str):
        """Log a section header."""
        separator = "=" * 60
        self.logger.info(separator)
        self.logger.info(title)
        self.logger.info(separator)
        if self.console_output:
            print(f"\n{separator}")
            print(f"  {title}")
            print(separator)

    def log_iteration_start(self, iteration: int, max_iterations: int):
        """Log the start of an iteration."""
        self.logger.info(f"Starting iteration {iteration}/{max_iterations}")
        if self.console_output:
            print(f"\nIteration {iteration}/{max_iterations}")

    def log_agent_review(
        self,
        agent_name: str,
        issues_count: int,
        high_count: int,
        tokens: Optional[Dict[str, int]] = None,
    ):
        """Log an agent review completion."""
        msg = f"Agent '{agent_name}': {issues_count} issues ({high_count} high)"
        if tokens:
            msg += f" - {tokens.get('total_tokens', 0)} tokens"
        self.logger.info(msg)
        if self.console_output:
            print(f"    - {agent_name}: {issues_count} issues ({high_count} high)")

    def log_convergence_check(self, converged: bool, reason: str, iteration: int):
        """Log convergence check result."""
        status = "CONVERGED" if converged else "CONTINUING"
        self.logger.info(f"Convergence check (iteration {iteration}): {status} - {reason}")
        if self.console_output:
            print(f"  Status: {reason}")

    def log_refinement(self, new_version: int, prev_length: int, new_length: int):
        """Log document refinement."""
        delta_pct = ((new_length - prev_length) / prev_length * 100) if prev_length > 0 else 0
        msg = f"Refined to v{new_version}: {prev_length} -> {new_length} chars ({delta_pct:+.1f}%)"
        self.logger.info(msg)
        if self.console_output and self.verbose:
            print(f"    {msg}")

    def track_tokens(self, agent_name: str, tokens: Dict[str, int]):
        """Track token usage for an agent."""
        total = tokens.get("total_tokens", 0)
        if agent_name not in self.token_usage:
            self.token_usage[agent_name] = 0
        self.token_usage[agent_name] += total
        self.logger.debug(f"Token usage for {agent_name}: {total} (total: {self.token_usage[agent_name]})")

    def get_token_summary(self) -> Dict[str, int]:
        """Get summary of token usage."""
        summary = dict(self.token_usage)
        summary["total"] = sum(self.token_usage.values())
        return summary

    def log_token_summary(self):
        """Log token usage summary."""
        summary = self.get_token_summary()
        self.section("Token Usage Summary")
        for agent, tokens in sorted(summary.items()):
            if agent != "total":
                self.logger.info(f"  {agent}: {tokens:,} tokens")
                if self.console_output:
                    print(f"  {agent}: {tokens:,} tokens")
        self.logger.info(f"  TOTAL: {summary['total']:,} tokens")
        if self.console_output:
            print(f"  TOTAL: {summary['total']:,} tokens")

    def log_final_result(self, converged: bool, final_version: int, reason: str):
        """Log the final result."""
        self.section("Refinement Complete")
        self.logger.info(f"Final version: {final_version}")
        self.logger.info(f"Converged: {converged}")
        self.logger.info(f"Reason: {reason}")
        if self.console_output:
            print(f"  Final version: v{final_version}")
            print(f"  Converged: {converged}")
            print(f"  Reason: {reason}")


def create_logger(
    session_id: str,
    log_dir: Optional[str] = None,
    verbose: bool = False,
) -> OrchestratorLogger:
    """Create a logger for an orchestration session."""
    return OrchestratorLogger(
        session_id=session_id,
        log_dir=log_dir,
        verbose=verbose,
    )
