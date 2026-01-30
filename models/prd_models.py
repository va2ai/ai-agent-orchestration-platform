from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class PRDIssue(BaseModel):
    """Single issue identified by a critic"""
    category: str = Field(..., description="Issue category: product, engineering, ai_risk")
    description: str = Field(..., description="Detailed issue description")
    severity: Literal["High", "Medium", "Low"] = Field(..., description="Issue severity")
    suggested_fix: str = Field(..., description="Actionable recommendation")
    reviewer: str = Field(..., description="Critic agent that found this issue")

class PRDReview(BaseModel):
    """Review from a single critic agent"""
    reviewer: str = Field(..., description="Critic agent name")
    issues: List[PRDIssue] = Field(default_factory=list)
    overall_assessment: str = Field(..., description="Summary assessment")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class PRD(BaseModel):
    """Product Requirements Document"""
    version: int = Field(default=1, description="PRD version number")
    title: str = Field(..., description="PRD title")
    content: str = Field(..., description="Full PRD markdown content")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    reviews: List[PRDReview] = Field(default_factory=list)
