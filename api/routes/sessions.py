from fastapi import APIRouter, HTTPException
from storage.prd_storage import PRDStorage
from api.models.api_models import SessionListResponse, SessionInfo, PRDResponse
from api.state import active_refinements
from typing import Dict, Any

router = APIRouter()
storage = PRDStorage()

@router.get("/", response_model=SessionListResponse)
async def list_sessions():
    """List all refinement sessions"""
    try:
        sessions = storage.list_sessions()
        session_infos = []

        for session in sessions:
            # Try to load convergence report for final version info
            report = storage.load_convergence_report(session["session_id"])
            session_info = SessionInfo(
                session_id=session["session_id"],
                title=session["title"],
                created_at=session["created_at"],
                final_version=report.get("final_version") if report else None,
                converged=report.get("converged") if report else None
            )
            session_infos.append(session_info)

        return SessionListResponse(
            sessions=session_infos,
            total=len(session_infos)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get session details"""
    try:
        session = storage.get_session_metadata(session_id)
        report = storage.load_convergence_report(session_id)

        return SessionInfo(
            session_id=session["session_id"],
            title=session["title"],
            created_at=session["created_at"],
            final_version=report.get("final_version") if report else None,
            converged=report.get("converged") if report else None
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/prd/{version}", response_model=PRDResponse)
async def get_prd_version(session_id: str, version: int):
    """Get specific PRD version"""
    try:
        prd = storage.load_prd(session_id, version)
        return PRDResponse(
            version=prd.version,
            title=prd.title,
            content=prd.content,
            created_at=prd.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"PRD version not found: {str(e)}")

@router.get("/{session_id}/reviews/{version}")
async def get_reviews(session_id: str, version: int):
    """Get reviews for specific version"""
    try:
        reviews = storage.load_reviews(session_id, version)
        return {"version": version, "reviews": reviews}
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Reviews not found: {str(e)}")

@router.get("/{session_id}/report")
async def get_convergence_report(session_id: str):
    """Get final convergence report"""
    try:
        report = storage.load_convergence_report(session_id)
        if report is None:
            raise HTTPException(status_code=444, detail="Convergence report not found")
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{session_id}/state")
async def get_session_state(session_id: str):
    """Get full state for monitoring a running session"""
    try:
        # 1. Get Status & Progress
        status_info = active_refinements.get(session_id)

        status = "unknown"
        current_iteration = 0
        max_iterations = 0

        if status_info:
            status = status_info.status
            current_iteration = status_info.current_iteration
            max_iterations = status_info.max_iterations
        else:
            # Fallback: check if completed
            report = storage.load_convergence_report(session_id)
            if report:
                status = "completed"
                current_iteration = report.get("iterations", 0)
                # max_iterations might not be easily available if not running, but config helps
            else:
                status = "inactive" # Exists but not in memory and not finished (failed/restarted?)

        # 2. Get Roundtable Config
        config = storage.load_roundtable_config(session_id)

        return {
            "session_id": session_id,
            "status": status,
            "current_iteration": current_iteration,
            "max_iterations": max_iterations,
            "roundtable_config": config
        }

    except Exception as e:
        print(f"Error getting session state: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to get session state: {str(e)}")

@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session and all its data"""
    try:
        # Check if session is currently running
        if session_id in active_refinements:
            raise HTTPException(status_code=400, detail="Cannot delete a running session")

        # Delete the session
        success = storage.delete_session(session_id)

        if success:
            return {"message": "Session deleted successfully", "session_id": session_id}
        else:
            raise HTTPException(status_code=404, detail="Session not found")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")
