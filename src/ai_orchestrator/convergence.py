"""
Convergence logic for the AI Orchestrator library.

This module provides reusable stop conditions for iterative refinement loops:
- No high-severity issues remaining
- Maximum iterations reached
- Document delta below threshold
- Custom stop conditions

The convergence logic is decoupled from specific document types and can be
used across different workflows (PRD refinement, code review, etc.).
"""
import difflib
from typing import List, Optional

from .types import (
    Issue,
    Review,
    RoundtableConfig,
    RoundtableIteration,
    Severity,
    StopDecision,
)


def count_issues_by_severity(reviews: List[Review]) -> dict:
    """Count issues by severity across all reviews."""
    counts = {"high": 0, "medium": 0, "low": 0}
    for review in reviews:
        for issue in review.issues:
            if issue.severity == Severity.HIGH:
                counts["high"] += 1
            elif issue.severity == Severity.MEDIUM:
                counts["medium"] += 1
            else:
                counts["low"] += 1
    return counts


def has_high_severity_issues(reviews: List[Review]) -> bool:
    """Check if any high severity issues exist in reviews."""
    for review in reviews:
        for issue in review.issues:
            if issue.severity == Severity.HIGH:
                return True
    return False


def calculate_document_delta(prev_content: str, current_content: str) -> float:
    """
    Calculate the change between two document versions.

    Returns:
        Float between 0.0 (identical) and 1.0 (completely different)
    """
    if not prev_content or not current_content:
        return 1.0

    matcher = difflib.SequenceMatcher(None, prev_content, current_content)
    similarity = matcher.ratio()  # 0.0 to 1.0
    return 1.0 - similarity  # Convert to delta


def decide_stop(
    config: RoundtableConfig,
    iterations: List[RoundtableIteration],
) -> StopDecision:
    """
    Decide whether the roundtable should stop.

    Evaluates stop conditions in priority order:
    1. Custom stop condition (if provided)
    2. No high severity issues remaining
    3. Maximum iterations reached
    4. Document delta below threshold

    Args:
        config: Roundtable configuration with thresholds
        iterations: List of completed iterations

    Returns:
        StopDecision indicating whether to stop and why
    """
    if not iterations:
        return StopDecision(
            should_stop=False,
            reason="No iterations completed yet",
            stopped_by="none",
        )

    current_iteration = iterations[-1]
    iteration_count = len(iterations)

    # Check 1: Custom stop condition
    if config.custom_stop_condition is not None:
        custom_decision = config.custom_stop_condition(iterations)
        if custom_decision.should_stop:
            return custom_decision

    # Check 2: No high severity issues
    if config.stop_on_no_high_issues:
        if not has_high_severity_issues(current_iteration.reviews):
            return StopDecision(
                should_stop=True,
                reason="No high severity issues remaining (0 remaining)",
                stopped_by="no_high_issues",
            )

    # Check 3: Max iterations reached
    if iteration_count >= config.max_iterations:
        high_count = sum(
            1
            for review in current_iteration.reviews
            for issue in review.issues
            if issue.severity == Severity.HIGH
        )
        return StopDecision(
            should_stop=True,
            reason=f"Max iterations reached ({config.max_iterations}). {high_count} high severity issues remain.",
            stopped_by="max_iterations",
        )

    # Check 4: Document delta below threshold
    if len(iterations) >= 2:
        prev_iteration = iterations[-2]
        delta = calculate_document_delta(
            prev_iteration.output_document,
            current_iteration.output_document,
        )
        if delta < config.delta_threshold:
            return StopDecision(
                should_stop=True,
                reason=f"Document stable (delta: {delta:.2%})",
                stopped_by="delta_threshold",
            )

    # Not converged
    high_count = sum(
        1
        for review in current_iteration.reviews
        for issue in review.issues
        if issue.severity == Severity.HIGH
    )
    return StopDecision(
        should_stop=False,
        reason=f"{high_count} high severity issues remain",
        stopped_by="none",
    )


class ConvergenceChecker:
    """
    Stateful convergence checker for backwards compatibility.

    This class wraps the functional convergence logic for compatibility
    with existing code that expects a class-based interface.
    """

    @staticmethod
    def has_converged(reviews: List[Review]) -> bool:
        """Check if no High severity issues remain."""
        return not has_high_severity_issues(reviews)

    @staticmethod
    def calculate_delta(prev_content: str, current_content: str) -> float:
        """Calculate similarity between document versions."""
        return calculate_document_delta(prev_content, current_content)

    @staticmethod
    def get_convergence_reason(
        reviews: List[Review],
        iteration: int,
        max_iterations: int,
        prev_content: Optional[str] = None,
        current_content: Optional[str] = None,
    ) -> tuple:
        """
        Determine if converged and why.

        Returns:
            Tuple of (converged: bool, reason: str)
        """
        # Build a minimal config and iterations list for decide_stop
        config = RoundtableConfig(
            max_iterations=max_iterations,
            stop_on_no_high_issues=True,
        )

        # Create minimal iterations for the check
        iterations = []
        if prev_content is not None:
            prev_iter = RoundtableIteration(
                iteration_index=iteration - 1,
                input_document="",
                output_document=prev_content,
                reviews=[],
            )
            iterations.append(prev_iter)

        current_iter = RoundtableIteration(
            iteration_index=iteration,
            input_document=prev_content or "",
            output_document=current_content or "",
            reviews=reviews,
        )
        iterations.append(current_iter)

        decision = decide_stop(config, iterations)
        return decision.should_stop, decision.reason
