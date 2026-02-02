"""
Smoke tests for run_roundtable runner.

Tests basic functionality with mock agents and moderators.
"""
import pytest
from typing import Any, Dict, Optional, Sequence

from ai_orchestrator import (
    run_roundtable,
    RoundtableConfig,
    RoundtableResult,
    Issue,
    Review,
    Severity,
)


class FakeAgent:
    """A fake agent for testing that returns configurable reviews."""

    def __init__(self, name: str, issues: list[tuple[str, Severity]] = None):
        self._name = name
        self._issues = issues or []

    @property
    def name(self) -> str:
        return self._name

    def review(
        self, document: str, context: Optional[Dict[str, Any]] = None
    ) -> Review:
        """Return a fake review with configured issues."""
        return Review(
            reviewer_name=self._name,
            issues=[
                Issue(
                    category="test",
                    description=desc,
                    severity=severity,
                    reviewer=self._name,
                )
                for desc, severity in self._issues
            ],
            overall_assessment=f"Review by {self._name}",
        )


class FakeModerator:
    """A fake moderator that appends a version number to the document."""

    def __init__(self, suffix: str = "[REFINED]"):
        self.suffix = suffix
        self.call_count = 0

    def refine(
        self,
        document: str,
        reviews: Sequence[Review],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Return document with a refinement marker."""
        self.call_count += 1
        return f"{document}\n{self.suffix} v{self.call_count}"


class TestRunRoundtable:
    """Tests for the run_roundtable function."""

    def test_basic_execution(self):
        """Test that run_roundtable executes and returns a result."""
        agents = [FakeAgent("TestAgent", [("issue1", Severity.LOW)])]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=1)

        result = run_roundtable(
            document="Test document",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Test Run",
        )

        assert isinstance(result, RoundtableResult)
        assert result.title == "Test Run"
        assert result.converged is True
        assert len(result.iterations) == 1

    def test_converges_on_no_high_issues(self):
        """Test convergence when no high severity issues."""
        agents = [
            FakeAgent("Agent1", [("minor issue", Severity.LOW)]),
            FakeAgent("Agent2", [("medium issue", Severity.MEDIUM)]),
        ]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=5, stop_on_no_high_issues=True)

        result = run_roundtable(
            document="Test document",
            agents=agents,
            moderator=moderator,
            config=config,
            title="No High Issues",
        )

        assert result.converged is True
        assert result.stopped_by == "no_high_issues"
        assert result.final_issue_count["high"] == 0

    def test_stops_at_max_iterations_with_high_issues(self):
        """Test that runner stops at max iterations even with high issues."""
        agents = [
            FakeAgent("Critic", [("critical issue", Severity.HIGH)]),
        ]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=3)

        result = run_roundtable(
            document="Test document",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Max Iterations",
        )

        assert result.converged is True  # Converged due to max iterations
        assert result.stopped_by == "max_iterations"
        assert len(result.iterations) == 3
        assert result.final_issue_count["high"] > 0

    def test_document_refinement(self):
        """Test that document is refined through iterations."""
        agents = [FakeAgent("Agent", [("issue", Severity.HIGH)])]
        moderator = FakeModerator(suffix="[MODIFIED]")
        config = RoundtableConfig(max_iterations=2)

        result = run_roundtable(
            document="Original content",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Refinement Test",
        )

        # Document should have been modified
        assert "[MODIFIED]" in result.final_document
        assert "Original content" in result.final_document

    def test_multiple_agents(self):
        """Test with multiple agents providing reviews."""
        agents = [
            FakeAgent("ProductCritic", [("ux issue", Severity.MEDIUM)]),
            FakeAgent("TechCritic", [("perf issue", Severity.LOW)]),
            FakeAgent("SecurityCritic", [("security issue", Severity.HIGH)]),
        ]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=2)

        result = run_roundtable(
            document="Multi-agent test",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Multi-Agent",
        )

        # Should have reviews from all agents in each iteration
        for iteration in result.iterations:
            assert len(iteration.reviews) == 3
            reviewer_names = {r.reviewer_name for r in iteration.reviews}
            assert "ProductCritic" in reviewer_names
            assert "TechCritic" in reviewer_names
            assert "SecurityCritic" in reviewer_names

    def test_result_structure(self):
        """Test that result contains all expected fields."""
        agents = [FakeAgent("Agent")]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=1)

        result = run_roundtable(
            document="Test",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Structure Test",
        )

        # Check all expected fields
        assert result.session_id is not None
        assert result.title == "Structure Test"
        assert result.initial_document == "Test"
        assert result.final_document is not None
        assert result.initial_version == 1
        assert result.final_version >= 1
        assert isinstance(result.iterations, list)
        assert isinstance(result.converged, bool)
        assert result.convergence_reason is not None
        assert result.stopped_by in ["no_high_issues", "max_iterations", "delta_threshold", "custom", "none"]
        assert isinstance(result.total_issues_identified, int)
        assert "high" in result.final_issue_count
        assert "medium" in result.final_issue_count
        assert "low" in result.final_issue_count

    def test_to_dict(self):
        """Test that result can be converted to dictionary."""
        agents = [FakeAgent("Agent")]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=1)

        result = run_roundtable(
            document="Test",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Dict Test",
        )

        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert "session_id" in result_dict
        assert "converged" in result_dict
        assert "history" in result_dict

    def test_session_id_provided(self):
        """Test that custom session_id is used when provided."""
        agents = [FakeAgent("Agent")]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=1)

        result = run_roundtable(
            document="Test",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Test",
            session_id="custom_session_123",
        )

        assert result.session_id == "custom_session_123"

    def test_context_passed_to_agents(self):
        """Test that context is passed to agents and moderator."""

        class ContextAwareAgent:
            def __init__(self):
                self._name = "ContextAgent"
                self.received_context = None

            @property
            def name(self):
                return self._name

            def review(self, document: str, context: Optional[Dict[str, Any]] = None) -> Review:
                self.received_context = context
                return Review(
                    reviewer_name=self._name,
                    issues=[],
                    overall_assessment="OK",
                )

        class ContextAwareModerator:
            def __init__(self):
                self.received_context = None

            def refine(
                self,
                document: str,
                reviews: Sequence[Review],
                context: Optional[Dict[str, Any]] = None,
            ) -> str:
                self.received_context = context
                return document

        agent = ContextAwareAgent()
        moderator = ContextAwareModerator()
        config = RoundtableConfig(max_iterations=1)
        context = {"key": "value", "user_id": 123}

        run_roundtable(
            document="Test",
            agents=[agent],
            moderator=moderator,
            config=config,
            context=context,
            title="Context Test",
        )

        assert agent.received_context == context


class TestIssueTracking:
    """Tests for issue tracking in results."""

    def test_total_issues_identified(self):
        """Test that total issues are correctly counted across iterations."""
        # Each review has 2 issues, 2 iterations means 4 total
        agents = [
            FakeAgent("Agent1", [("issue1", Severity.LOW)]),
            FakeAgent("Agent2", [("issue2", Severity.MEDIUM)]),
        ]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=2, stop_on_no_high_issues=False)

        # Force max iterations by having agent3 always have high issues
        agents_with_high = agents + [FakeAgent("Agent3", [("critical", Severity.HIGH)])]

        result = run_roundtable(
            document="Test",
            agents=agents_with_high,
            moderator=moderator,
            config=config,
            title="Issue Tracking",
        )

        # 3 agents * 2 iterations = 6 issues total (1 issue per agent per iteration)
        assert result.total_issues_identified == 6

    def test_final_issue_count(self):
        """Test that final issue count reflects last iteration."""
        agents = [
            FakeAgent("Agent1", [("high1", Severity.HIGH)]),
            FakeAgent("Agent2", [("medium1", Severity.MEDIUM), ("low1", Severity.LOW)]),
        ]
        moderator = FakeModerator()
        config = RoundtableConfig(max_iterations=1)

        result = run_roundtable(
            document="Test",
            agents=agents,
            moderator=moderator,
            config=config,
            title="Final Count",
        )

        assert result.final_issue_count["high"] == 1
        assert result.final_issue_count["medium"] == 1
        assert result.final_issue_count["low"] == 1
