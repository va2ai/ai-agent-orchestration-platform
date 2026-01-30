from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class StartRefinementRequest(BaseModel):
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Initial document markdown content")
    goal: Optional[str] = Field(default=None, description="What the roundtable should accomplish (e.g., 'write an appeal', 'improve clarity', 'add security measures')")
    max_iterations: int = Field(default=3, ge=1, le=10)
    document_type: str = Field(default="document", description="Document type (prd, architecture, code-review, etc.)")
    num_participants: int = Field(default=3, ge=2, le=6, description="Number of roundtable participants")
    use_preset: Optional[str] = Field(default=None, description="Use preset configuration (prd, code-review, architecture, business-strategy)")
    participant_style: Optional[str] = Field(default=None, description="Style/Tone of participants (critical, creative, conservative, academic)")
    model: Optional[str] = Field(default="gpt-4-turbo", description="LLM model to use (gpt-4-turbo, gpt-4o, claude-3-opus-20240229, etc.)")
    model_strategy: Optional[str] = Field(default="uniform", description="Strategy for model assignment: 'uniform' (use selected model for all) or 'diverse' (assign different models)")
    force_max_iterations: bool = Field(default=False, description="Whether to ignore early convergence and run for the full number of max iterations")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class RefinementStatus(BaseModel):
    session_id: str
    status: str  # "running" | "completed" | "failed"
    current_iteration: int
    max_iterations: int
    current_version: int
    converged: bool
    convergence_reason: Optional[str] = None

class SessionInfo(BaseModel):
    session_id: str
    title: str
    created_at: str
    final_version: Optional[int] = None
    converged: Optional[bool] = None

class SessionListResponse(BaseModel):
    sessions: List[SessionInfo]
    total: int

class PRDResponse(BaseModel):
    version: int
    title: str
    content: str
    created_at: str

class ReviewsResponse(BaseModel):
    version: int
    reviews: List[Dict[str, Any]]

class ParticipantInfo(BaseModel):
    name: str
    role: str
    expertise: str
    perspective: str

class RoundtableConfigResponse(BaseModel):
    participants: List[ParticipantInfo]
    moderator_focus: str
    convergence_criteria: str

class DocumentResponse(BaseModel):
    version: int
    title: str
    content: str
    document_type: str
    created_at: str
