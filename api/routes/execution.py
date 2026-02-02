"""
API routes for execution trace visualization.

These endpoints provide data for the React Flow execution visualizer.
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from api.models.execution_models import (
    ExecutionTrace,
    IterationExecution,
    AgentExecution,
    ExecutionIssue,
    IssueSeverity,
    StartOrchestrationRequest,
    OrchestrationStartResponse,
)
from api.services.dynamic_async_orchestrator import DynamicAsyncOrchestrator
from api.state import active_refinements
from ai_orchestrator.storage.prd_storage import PRDStorage
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio

router = APIRouter()

# In-memory storage for execution traces (for real-time updates)
execution_traces: Dict[str, ExecutionTrace] = {}


def build_execution_trace_from_session(session_id: str) -> Optional[ExecutionTrace]:
    """
    Build an ExecutionTrace from stored session data.

    This reconstructs the execution trace from the convergence report and reviews.
    """
    storage = PRDStorage()

    if not storage.session_exists(session_id):
        return None

    # Load convergence report
    report = storage.load_convergence_report(session_id)
    if not report:
        return None

    # Get session metadata
    metadata = storage.get_session_metadata(session_id)

    # Build iterations from stored reviews
    iterations: List[IterationExecution] = []

    for version in range(1, report.get("final_version", 1) + 1):
        reviews = storage.load_reviews(session_id, version)
        prd = storage.load_prd(session_id, version)

        if reviews:
            agents = []
            all_issues = []

            for review in reviews:
                reviewer_name = review.get("reviewer_name", "Unknown")
                review_issues = review.get("issues", [])

                high_count = sum(
                    1 for i in review_issues if i.get("severity", "").lower() == "high"
                )

                agents.append(
                    AgentExecution(
                        name=reviewer_name,
                        role=review.get("role"),
                        issues=len(review_issues),
                        high_issues=high_count,
                        assessment=review.get("overall_assessment"),
                    )
                )

                for issue in review_issues:
                    severity_str = issue.get("severity", "medium").lower()
                    try:
                        severity = IssueSeverity(severity_str)
                    except ValueError:
                        severity = IssueSeverity.MEDIUM

                    all_issues.append(
                        ExecutionIssue(
                            severity=severity,
                            message=issue.get("description", ""),
                            category=issue.get("category"),
                            suggested_fix=issue.get("suggested_fix"),
                        )
                    )

            issue_counts = {
                "high": sum(1 for i in all_issues if i.severity == IssueSeverity.HIGH),
                "medium": sum(1 for i in all_issues if i.severity == IssueSeverity.MEDIUM),
                "low": sum(1 for i in all_issues if i.severity == IssueSeverity.LOW),
            }

            iterations.append(
                IterationExecution(
                    iteration_index=version,
                    delta=0.0,  # Could be calculated from document changes
                    issues=all_issues,
                    issue_counts=issue_counts,
                    agents=agents,
                    document_version=version,
                    document_length=len(prd.content) if prd else 0,
                )
            )

    # Build participants info
    participants = report.get("roundtable_participants", [])

    # Determine stopped_by from convergence_reason
    stopped_by = None
    convergence_reason = report.get("convergence_reason", "")
    if "no high" in convergence_reason.lower():
        stopped_by = "no_high_issues"
    elif "max iterations" in convergence_reason.lower():
        stopped_by = "max_iterations"
    elif "delta" in convergence_reason.lower() or "stable" in convergence_reason.lower():
        stopped_by = "delta_threshold"

    # Load initial and final document lengths
    initial_prd = storage.load_prd(session_id, 1)
    final_prd = storage.load_prd(session_id, report.get("final_version", 1))

    trace = ExecutionTrace(
        run_id=session_id,
        title=report.get("title", metadata.get("title", "Untitled")),
        status="completed" if report.get("converged") else "completed",
        stopped_by=stopped_by,
        convergence_reason=convergence_reason,
        initial_document_length=len(initial_prd.content) if initial_prd else 0,
        final_document_length=len(final_prd.content) if final_prd else 0,
        iterations=iterations,
        total_iterations=report.get("iterations", 0),
        max_iterations=report.get("max_iterations", 3),
        participants=participants,
        moderator_focus=report.get("moderator_focus"),
        total_issues_identified=sum(it.issue_counts["high"] + it.issue_counts["medium"] + it.issue_counts["low"] for it in iterations),
        final_issue_counts=report.get("final_issue_count", {"high": 0, "medium": 0, "low": 0}),
        started_at=report.get("timestamps", {}).get("start"),
        completed_at=report.get("timestamps", {}).get("end"),
    )

    return trace


@router.get("/runs")
async def list_runs():
    """List all available execution runs."""
    storage = PRDStorage()
    sessions = storage.list_sessions()

    runs = []
    for session in sessions:
        session_id = session.get("session_id", "")
        report = storage.load_convergence_report(session_id)

        runs.append({
            "run_id": session_id,
            "title": session.get("title", "Untitled"),
            "created_at": session.get("created_at"),
            "status": "completed" if report else "unknown",
            "iterations": report.get("iterations", 0) if report else 0,
            "converged": report.get("converged", False) if report else False,
        })

    return {"runs": runs, "total": len(runs)}


@router.get("/trace/{run_id}", response_model=ExecutionTrace)
async def get_execution_trace(run_id: str):
    """
    Get the execution trace for a completed run.

    Returns the full computed execution trace for visualization.
    The frontend should only render this data - no computation needed.
    """
    # Check in-memory first (for active runs)
    if run_id in execution_traces:
        return execution_traces[run_id]

    # Load from storage
    trace = build_execution_trace_from_session(run_id)

    if not trace:
        raise HTTPException(status_code=404, detail="Run not found")

    return trace


@router.post("/start", response_model=OrchestrationStartResponse)
async def start_orchestration(
    request: StartOrchestrationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Start a new orchestration run.

    Returns immediately with the run_id and websocket URL.
    The actual orchestration runs in the background.
    """
    # Generate session ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"session_{timestamp}"

    # Initialize execution trace
    execution_traces[run_id] = ExecutionTrace(
        run_id=run_id,
        title=request.title,
        status="running",
        initial_document_length=len(request.document),
        max_iterations=request.max_iterations,
    )

    # Start orchestration in background
    background_tasks.add_task(
        run_orchestration_with_trace,
        run_id,
        request.title,
        request.document,
        request.max_iterations,
        request.document_type,
        request.num_participants,
        request.model,
        request.goal,
        request.participant_style,
    )

    # Return immediately
    return OrchestrationStartResponse(
        run_id=run_id,
        status="started",
        websocket_url=f"/ws/execution/{run_id}",
    )


async def run_orchestration_with_trace(
    run_id: str,
    title: str,
    content: str,
    max_iterations: int,
    document_type: str,
    num_participants: int,
    model: str,
    goal: Optional[str],
    participant_style: Optional[str],
):
    """
    Run orchestration and update execution trace in real-time.
    """
    try:
        orchestrator = DynamicAsyncOrchestrator(
            max_iterations=max_iterations,
            verbose=False,
            num_participants=num_participants,
            model=model,
        )

        final_doc, report = await orchestrator.run(
            title=title,
            initial_content=content,
            document_type=document_type,
            goal=goal,
            participant_style=participant_style,
        )

        # Update execution trace with final results
        trace = build_execution_trace_from_session(run_id)
        if trace:
            execution_traces[run_id] = trace
        else:
            # Update with basic info if storage load fails
            if run_id in execution_traces:
                execution_traces[run_id].status = "completed"
                execution_traces[run_id].final_document_length = len(final_doc.content)
                execution_traces[run_id].convergence_reason = report.get("convergence_reason")

    except Exception as e:
        if run_id in execution_traces:
            execution_traces[run_id].status = "failed"
            execution_traces[run_id].convergence_reason = f"Error: {str(e)}"
        print(f"Orchestration failed for {run_id}: {e}")
        import traceback
        traceback.print_exc()


@router.get("/status/{run_id}")
async def get_run_status(run_id: str):
    """Get the current status of an orchestration run."""
    if run_id in execution_traces:
        trace = execution_traces[run_id]
        return {
            "run_id": run_id,
            "status": trace.status,
            "current_iteration": len(trace.iterations),
            "max_iterations": trace.max_iterations,
        }

    # Check storage
    storage = PRDStorage()
    if storage.session_exists(run_id):
        report = storage.load_convergence_report(run_id)
        if report:
            return {
                "run_id": run_id,
                "status": "completed",
                "current_iteration": report.get("iterations", 0),
                "max_iterations": report.get("max_iterations", 3),
            }

    raise HTTPException(status_code=404, detail="Run not found")
