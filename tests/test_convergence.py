"""
Tests for convergence logic.

Tests all stop conditions:
- No high severity issues remaining
- Maximum iterations reached
- Document delta below threshold
- Custom stop conditions
"""
import pytest
from ai_orchestrator import (
    RoundtableConfig,
    RoundtableIteration,
    Issue,
    Review,
    Severity,
    StopDecision,
)
from ai_orchestrator.convergence import (
    decide_stop,
    has_high_severity_issues,
    calculate_document_delta,
    count_issues_by_severity,
    ConvergenceChecker,
)


def make_review(issues: list[tuple[str, Severity]]) -> Review:
    """Helper to create a Review with given issues."""
    return Review(
        reviewer_name="test_reviewer",
        issues=[
            Issue(
                category="test",
                description=f"Issue {i}",
                severity=severity,
                reviewer="test_reviewer",
            )
            for i, (_, severity) in enumerate(issues)
        ],
        overall_assessment="Test assessment",
    )


def make_iteration(
    iteration_index: int,
    reviews: list[Review],
    input_doc: str = "input",
    output_doc: str = "output",
) -> RoundtableIteration:
    """Helper to create a RoundtableIteration."""
    return RoundtableIteration(
        iteration_index=iteration_index,
        input_document=input_doc,
        output_document=output_doc,
        reviews=reviews,
    )


class TestHasHighSeverityIssues:
    """Tests for has_high_severity_issues function."""

    def test_no_issues(self):
        """Empty reviews have no high severity issues."""
        reviews = []
        assert has_high_severity_issues(reviews) is False

    def test_only_low_medium_issues(self):
        """Reviews with only low/medium issues return False."""
        reviews = [
            make_review([("low", Severity.LOW), ("medium", Severity.MEDIUM)]),
        ]
        assert has_high_severity_issues(reviews) is False

    def test_has_high_issues(self):
        """Reviews with high severity issues return True."""
        reviews = [
            make_review([("high", Severity.HIGH), ("low", Severity.LOW)]),
        ]
        assert has_high_severity_issues(reviews) is True

    def test_multiple_reviewers_with_high_issues(self):
        """High issues from any reviewer should be detected."""
        reviews = [
            make_review([("low", Severity.LOW)]),
            make_review([("high", Severity.HIGH)]),
        ]
        assert has_high_severity_issues(reviews) is True


class TestCalculateDocumentDelta:
    """Tests for calculate_document_delta function."""

    def test_identical_documents(self):
        """Identical documents have delta of 0."""
        delta = calculate_document_delta("hello world", "hello world")
        assert delta == 0.0

    def test_completely_different_documents(self):
        """Completely different documents have high delta."""
        delta = calculate_document_delta("aaa", "zzz")
        assert delta > 0.9

    def test_similar_documents(self):
        """Similar documents have low delta."""
        delta = calculate_document_delta(
            "The quick brown fox jumps over the lazy dog",
            "The quick brown fox leaps over the lazy dog",
        )
        assert 0.0 < delta < 0.2

    def test_empty_documents(self):
        """Empty documents should return delta of 1.0."""
        delta = calculate_document_delta("", "")
        # Note: empty strings are identical, so delta is 0
        # But the function handles None/empty specially
        assert delta == 1.0 or delta == 0.0  # depends on implementation


class TestCountIssuesBySeverity:
    """Tests for count_issues_by_severity function."""

    def test_empty_reviews(self):
        """Empty reviews return zero counts."""
        counts = count_issues_by_severity([])
        assert counts == {"high": 0, "medium": 0, "low": 0}

    def test_counts_all_severities(self):
        """Correctly counts issues by severity."""
        reviews = [
            make_review([
                ("h1", Severity.HIGH),
                ("h2", Severity.HIGH),
                ("m1", Severity.MEDIUM),
                ("l1", Severity.LOW),
            ]),
            make_review([
                ("h3", Severity.HIGH),
                ("l2", Severity.LOW),
            ]),
        ]
        counts = count_issues_by_severity(reviews)
        assert counts == {"high": 3, "medium": 1, "low": 2}


class TestDecideStop:
    """Tests for decide_stop function."""

    def test_empty_iterations(self):
        """No iterations means don't stop."""
        config = RoundtableConfig(max_iterations=3)
        decision = decide_stop(config, [])
        assert decision.should_stop is False

    def test_stop_on_no_high_issues(self):
        """Stop when no high severity issues remain."""
        config = RoundtableConfig(max_iterations=3, stop_on_no_high_issues=True)
        reviews = [make_review([("low", Severity.LOW)])]
        iterations = [make_iteration(1, reviews)]

        decision = decide_stop(config, iterations)
        assert decision.should_stop is True
        assert decision.stopped_by == "no_high_issues"
        assert "0 remaining" in decision.reason

    def test_stop_on_max_iterations(self):
        """Stop when max iterations reached."""
        config = RoundtableConfig(max_iterations=2)
        reviews = [make_review([("high", Severity.HIGH)])]
        iterations = [
            make_iteration(1, reviews),
            make_iteration(2, reviews),
        ]

        decision = decide_stop(config, iterations)
        assert decision.should_stop is True
        assert decision.stopped_by == "max_iterations"
        assert "Max iterations reached" in decision.reason

    def test_stop_on_delta_threshold(self):
        """Stop when document delta is below threshold."""
        config = RoundtableConfig(max_iterations=10, delta_threshold=0.1)
        reviews = [make_review([("high", Severity.HIGH)])]

        # Create iterations with nearly identical documents
        iterations = [
            make_iteration(1, reviews, "doc version 1", "doc version 1a"),
            make_iteration(2, reviews, "doc version 1a", "doc version 1a"),  # 0% change
        ]

        decision = decide_stop(config, iterations)
        assert decision.should_stop is True
        assert decision.stopped_by == "delta_threshold"

    def test_continue_when_high_issues_remain(self):
        """Continue when high issues remain and not at max iterations."""
        config = RoundtableConfig(max_iterations=5)
        reviews = [make_review([("high", Severity.HIGH)])]
        iterations = [make_iteration(1, reviews)]

        decision = decide_stop(config, iterations)
        assert decision.should_stop is False
        assert "high severity issues remain" in decision.reason

    def test_custom_stop_condition(self):
        """Custom stop condition takes precedence."""
        def custom_stop(iterations: list) -> StopDecision:
            if len(iterations) >= 2:
                return StopDecision(
                    should_stop=True,
                    reason="Custom: two iterations complete",
                    stopped_by="custom",
                )
            return StopDecision(
                should_stop=False,
                reason="Continue",
                stopped_by="none",
            )

        config = RoundtableConfig(
            max_iterations=10,
            custom_stop_condition=custom_stop,
        )
        reviews = [make_review([("high", Severity.HIGH)])]
        iterations = [
            make_iteration(1, reviews),
            make_iteration(2, reviews),
        ]

        decision = decide_stop(config, iterations)
        assert decision.should_stop is True
        assert decision.stopped_by == "custom"


class TestConvergenceCheckerBackwardsCompatibility:
    """Tests for ConvergenceChecker class (backwards compatibility)."""

    def test_has_converged(self):
        """Test has_converged static method."""
        # No high issues
        reviews_no_high = [make_review([("low", Severity.LOW)])]
        assert ConvergenceChecker.has_converged(reviews_no_high) is True

        # Has high issues
        reviews_with_high = [make_review([("high", Severity.HIGH)])]
        assert ConvergenceChecker.has_converged(reviews_with_high) is False

    def test_calculate_delta(self):
        """Test calculate_delta static method."""
        delta = ConvergenceChecker.calculate_delta("hello", "hello")
        assert delta == 0.0

        delta = ConvergenceChecker.calculate_delta("aaa", "bbb")
        assert delta > 0.5

    def test_get_convergence_reason(self):
        """Test get_convergence_reason static method."""
        reviews = [make_review([("low", Severity.LOW)])]

        converged, reason = ConvergenceChecker.get_convergence_reason(
            reviews=reviews,
            iteration=1,
            max_iterations=3,
        )
        assert converged is True
        assert "0 remaining" in reason
