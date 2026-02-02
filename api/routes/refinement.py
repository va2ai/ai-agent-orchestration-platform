from fastapi import APIRouter, BackgroundTasks, HTTPException
from api.models.api_models import StartRefinementRequest, RefinementStatus, RoundtableConfigResponse
from api.services.dynamic_async_orchestrator import DynamicAsyncOrchestrator
from api.services.async_orchestrator import AsyncLoopingOrchestrator
from api.state import active_refinements
from datetime import datetime
from typing import Dict
import asyncio

router = APIRouter()

@router.post("/start")
async def start_refinement(request: StartRefinementRequest, background_tasks: BackgroundTasks):
    """Start a new document refinement with dynamic roundtable"""

    # Generate session ID
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_id = f"session_{timestamp}"

    # Initialize status
    active_refinements[session_id] = RefinementStatus(
        session_id=session_id,
        status="running",
        current_iteration=0,
        max_iterations=request.max_iterations,
        current_version=1,
        converged=False
    )

    # Start refinement in background
    background_tasks.add_task(
        run_refinement,
        session_id,
        request.title,
        request.content,
        request.max_iterations,
        request.document_type,
        request.num_participants,
        request.use_preset,
        request.metadata,
        request.goal,
        request.participant_style,
        request.model,
        request.force_max_iterations
    )

    return {"session_id": session_id, "status": "started"}

@router.get("/status/{session_id}", response_model=RefinementStatus)
async def get_status(session_id: str):
    """Get current refinement status"""
    if session_id not in active_refinements:
        raise HTTPException(status_code=404, detail="Session not found")
    return active_refinements[session_id]

@router.post("/continue/{session_id}")
async def continue_refinement(session_id: str, additional_iterations: int, background_tasks: BackgroundTasks):
    """Continue refinement for a converged session with additional iterations"""
    from ai_orchestrator.storage.prd_storage import PRDStorage

    storage = PRDStorage()

    # Check if session exists
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    # Load session metadata
    session_metadata = storage.get_session_metadata(session_id)

    # Load convergence report to get final version
    report = storage.load_convergence_report(session_id)
    if not report:
        raise HTTPException(status_code=404, detail="Convergence report not found")

    # Load the final document version
    final_version = report.get("final_version", 1)
    final_doc = storage.load_prd(session_id, final_version)

    # Load roundtable config
    roundtable_config = storage.load_roundtable_config(session_id)
    if not roundtable_config:
        raise HTTPException(status_code=404, detail="Roundtable config not found")

    # Calculate new max iterations
    current_iterations = report.get("iterations", 0)
    new_max_iterations = current_iterations + additional_iterations

    # Initialize status for continuation
    active_refinements[session_id] = RefinementStatus(
        session_id=session_id,
        status="running",
        current_iteration=current_iterations,
        max_iterations=new_max_iterations,
        current_version=final_version,
        converged=False
    )

    # Start continuation in background
    background_tasks.add_task(
        run_continuation,
        session_id,
        final_doc,
        current_iterations,
        new_max_iterations,
        roundtable_config
    )

    return {
        "session_id": session_id,
        "status": "continued",
        "previous_iterations": current_iterations,
        "new_max_iterations": new_max_iterations,
        "additional_iterations": additional_iterations
    }

async def run_refinement(
    session_id: str,
    title: str,
    content: str,
    max_iterations: int,
    document_type: str = "document",
    num_participants: int = 3,
    use_preset: str = None,
    metadata: dict = None,
    goal: str = None,
    participant_style: str = None,
    model: str = "gpt-4-turbo",
    force_max_iterations: bool = False
):
    """Background task to run refinement with dynamic roundtable"""
    try:
        orchestrator = DynamicAsyncOrchestrator(
            max_iterations=max_iterations,
            verbose=False,
            num_participants=num_participants,
            use_preset=use_preset,
            model=model,
            force_max_iterations=force_max_iterations
        )

        final_doc, report = await orchestrator.run(
            title=title,
            initial_content=content,
            document_type=document_type,
            metadata=metadata,
            goal=goal,
            participant_style=participant_style
        )

        # Update status to completed
        if session_id in active_refinements:
            active_refinements[session_id].status = "completed"
            active_refinements[session_id].converged = report["converged"]
            active_refinements[session_id].convergence_reason = report["convergence_reason"]
            active_refinements[session_id].current_version = final_doc.version
            active_refinements[session_id].current_iteration = report["iterations"]

    except Exception as e:
        # Update status to failed
        if session_id in active_refinements:
            active_refinements[session_id].status = "failed"
            active_refinements[session_id].convergence_reason = f"Error: {str(e)}"
        print(f"Refinement failed for {session_id}: {e}")
        import traceback
        traceback.print_exc()

async def run_continuation(
    session_id: str,
    current_doc,
    current_iteration: int,
    new_max_iterations: int,
    roundtable_config: dict
):
    """Background task to continue refinement from existing state"""
    try:
        orchestrator = DynamicAsyncOrchestrator(
            max_iterations=new_max_iterations,
            verbose=False,
            num_participants=roundtable_config.get("num_participants", 3),
            use_preset=roundtable_config.get("use_preset"),
            model=roundtable_config.get("model", "gpt-4-turbo"),
            force_max_iterations=roundtable_config.get("force_max_iterations", False)
        )

        # Continue from current document
        final_doc, report = await orchestrator.continue_from(
            session_id=session_id,
            current_doc=current_doc,
            start_iteration=current_iteration,
            document_type=roundtable_config.get("document_type", "document"),
            metadata=roundtable_config.get("metadata"),
            goal=roundtable_config.get("goal"),
            participant_style=roundtable_config.get("participant_style")
        )

        # Update status to completed
        if session_id in active_refinements:
            active_refinements[session_id].status = "completed"
            active_refinements[session_id].converged = report["converged"]
            active_refinements[session_id].convergence_reason = report["convergence_reason"]
            active_refinements[session_id].current_version = final_doc.version
            active_refinements[session_id].current_iteration = report["iterations"]

    except Exception as e:
        # Update status to failed
        if session_id in active_refinements:
            active_refinements[session_id].status = "failed"
            active_refinements[session_id].convergence_reason = f"Error: {str(e)}"
        print(f"Continuation failed for {session_id}: {e}")
        import traceback
        traceback.print_exc()
