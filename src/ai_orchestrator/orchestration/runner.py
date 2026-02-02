"""
Main runner for the AI Orchestrator roundtable loop.

This module provides the primary public API: run_roundtable()
"""
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

from ..convergence import count_issues_by_severity, decide_stop
from ..exceptions import EngineError, OrchestratorError
from ..logging import OrchestratorLogger, create_logger
from ..types import (
    Agent,
    Moderator,
    OrchestratorEngine,
    Review,
    RoundtableConfig,
    RoundtableIteration,
    RoundtableResult,
    Severity,
)


class DefaultEngine:
    """
    Default engine implementation that runs agents sequentially.

    This engine:
    1. Runs each agent's review() method to get reviews
    2. Aggregates all reviews
    3. Passes reviews to the moderator for refinement

    For parallel execution, use AsyncEngine or implement OrchestratorEngine.
    """

    def step(
        self,
        document: str,
        agents: Sequence[Agent],
        moderator: Moderator,
        context: Optional[Dict[str, Any]] = None,
        iteration_index: int = 0,
        logger: Optional[OrchestratorLogger] = None,
    ) -> RoundtableIteration:
        """Execute a single roundtable iteration."""
        context = context or {}
        reviews: List[Review] = []
        token_usage: Dict[str, int] = {}

        # Step 1: Get reviews from all agents
        for agent in agents:
            try:
                review = agent.review(document, context)
                reviews.append(review)

                # Log if logger provided
                if logger:
                    high_count = sum(1 for i in review.issues if i.severity == Severity.HIGH)
                    logger.log_agent_review(
                        agent.name,
                        len(review.issues),
                        high_count,
                    )
            except Exception as e:
                raise EngineError(f"Agent '{agent.name}' failed: {e}") from e

        # Step 2: Moderator refines the document
        try:
            refined_document = moderator.refine(document, reviews, context)
        except Exception as e:
            raise EngineError(f"Moderator failed: {e}") from e

        return RoundtableIteration(
            iteration_index=iteration_index,
            input_document=document,
            output_document=refined_document,
            reviews=reviews,
            notes="",
            metadata={"token_usage": token_usage},
        )


def run_roundtable(
    document: str,
    agents: Sequence[Agent],
    moderator: Moderator,
    engine: Optional[OrchestratorEngine] = None,
    config: Optional[RoundtableConfig] = None,
    context: Optional[Dict[str, Any]] = None,
    title: str = "Untitled",
    session_id: Optional[str] = None,
    logger: Optional[OrchestratorLogger] = None,
) -> RoundtableResult:
    """
    Run a roundtable refinement session.

    This is the primary public API for the AI Orchestrator library.

    Args:
        document: The initial document to refine (markdown content)
        agents: Sequence of agents that will review the document
        moderator: Moderator that refines the document based on reviews
        engine: Optional engine for executing iterations (default: DefaultEngine)
        config: Optional configuration (default: RoundtableConfig())
        context: Optional context dict passed to agents and moderator
        title: Title for the session
        session_id: Optional session ID (auto-generated if not provided)
        logger: Optional logger instance

    Returns:
        RoundtableResult containing the final document and all iteration data

    Example:
        from ai_orchestrator import run_roundtable, RoundtableConfig

        result = run_roundtable(
            document="# My PRD\\n\\nBuild a chatbot...",
            agents=[product_critic, engineering_critic, ai_risk_critic],
            moderator=prd_moderator,
            config=RoundtableConfig(max_iterations=3),
            title="AI Chatbot PRD",
        )

        print(f"Final document:\\n{result.final_document}")
        print(f"Converged: {result.converged}")
    """
    # Apply defaults
    config = config or RoundtableConfig()
    engine = engine or DefaultEngine()
    context = context or {}

    # Generate session ID if not provided
    if not session_id:
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Create logger if not provided
    if not logger:
        logger = create_logger(session_id, verbose=config.verbose)

    logger.section(f"Roundtable Session: {title}")
    logger.info(f"Session ID: {session_id}")
    logger.info(f"Max iterations: {config.max_iterations}")
    logger.info(f"Agents: {[a.name for a in agents]}")

    # Track state
    iterations: List[RoundtableIteration] = []
    current_document = document
    initial_document = document
    start_time = datetime.now().isoformat()
    total_issues = 0

    # Main loop
    for iteration_index in range(1, config.max_iterations + 1):
        logger.log_iteration_start(iteration_index, config.max_iterations)

        # Execute iteration
        iteration = engine.step(
            document=current_document,
            agents=agents,
            moderator=moderator,
            context=context,
            iteration_index=iteration_index,
            logger=logger,
        )
        iterations.append(iteration)
        total_issues += len(iteration.all_issues)

        # Check convergence
        decision = decide_stop(config, iterations)
        logger.log_convergence_check(decision.should_stop, decision.reason, iteration_index)

        if decision.should_stop:
            logger.info(f"Stopping: {decision.reason}")
            break

        # Update document for next iteration
        current_document = iteration.output_document
        logger.log_refinement(
            iteration_index + 1,
            len(iteration.input_document),
            len(iteration.output_document),
        )

    # Build final result
    final_iteration = iterations[-1] if iterations else None
    final_document = final_iteration.output_document if final_iteration else document
    final_reviews = final_iteration.reviews if final_iteration else []

    # Get final decision
    final_decision = decide_stop(config, iterations)

    result = RoundtableResult(
        session_id=session_id,
        title=title,
        initial_document=initial_document,
        final_document=final_document,
        initial_version=1,
        final_version=len(iterations) + 1,
        iterations=iterations,
        converged=final_decision.should_stop,
        convergence_reason=final_decision.reason,
        stopped_by=final_decision.stopped_by,
        total_issues_identified=total_issues,
        final_issue_count=count_issues_by_severity(final_reviews),
        token_usage=logger.get_token_summary(),
        timestamps={
            "start": start_time,
            "end": datetime.now().isoformat(),
        },
        metadata=config.metadata,
    )

    # Log final result
    logger.log_final_result(result.converged, result.final_version, result.convergence_reason)
    logger.log_token_summary()

    return result
