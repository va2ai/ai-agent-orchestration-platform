#!/usr/bin/env python3
"""
Generic document models for any type of content refinement.

These models replace the PRD-specific models and work for any document type:
- Product requirements
- Technical designs
- Code reviews
- Business strategies
- Documentation
- etc.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class DocumentIssue(BaseModel):
    """An issue identified in a document during review"""
    category: str = Field(description="Issue category (e.g., 'Clarity', 'Technical Feasibility', 'Security')")
    description: str = Field(description="Detailed description of the issue")
    severity: str = Field(description="Severity level: High, Medium, or Low")
    suggested_fix: Optional[str] = Field(default=None, description="Suggested fix or improvement")
    reviewer: str = Field(description="Name of the reviewer who identified this issue")


class DocumentReview(BaseModel):
    """A review of a document by a single reviewer"""
    reviewer_name: str = Field(description="Name of the reviewer")
    issues: List[DocumentIssue] = Field(default_factory=list, description="List of issues found")
    overall_assessment: str = Field(description="Overall assessment and summary")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Document(BaseModel):
    """
    A generic document that can be iteratively refined.

    Can represent:
    - Product requirements documents (PRDs)
    - Technical design documents
    - Architecture proposals
    - Business strategy documents
    - Code review summaries
    - Documentation drafts
    - etc.
    """
    version: int = Field(description="Document version number")
    title: str = Field(description="Document title")
    content: str = Field(description="Document content (markdown format)")
    document_type: str = Field(default="document", description="Type of document (e.g., 'prd', 'architecture', 'code-review')")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    reviews: List[DocumentReview] = Field(default_factory=list, description="Reviews for this version")

    def add_review(self, review: DocumentReview):
        """Add a review to this document version"""
        self.reviews.append(review)

    def get_issue_counts(self) -> dict:
        """Get count of issues by severity across all reviews"""
        counts = {"high": 0, "medium": 0, "low": 0}

        for review in self.reviews:
            for issue in review.issues:
                severity_key = issue.severity.lower()
                if severity_key in counts:
                    counts[severity_key] += 1

        return counts

    def get_all_issues(self) -> List[DocumentIssue]:
        """Get all issues from all reviews"""
        all_issues = []
        for review in self.reviews:
            all_issues.extend(review.issues)
        return all_issues

    def has_high_severity_issues(self) -> bool:
        """Check if any High severity issues exist"""
        for review in self.reviews:
            for issue in review.issues:
                if issue.severity == "High":
                    return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "version": self.version,
            "title": self.title,
            "content": self.content,
            "document_type": self.document_type,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "reviews": [
                {
                    "reviewer_name": r.reviewer_name,
                    "issues": [
                        {
                            "category": i.category,
                            "description": i.description,
                            "severity": i.severity,
                            "suggested_fix": i.suggested_fix,
                            "reviewer": i.reviewer
                        }
                        for i in r.issues
                    ],
                    "overall_assessment": r.overall_assessment,
                    "timestamp": r.timestamp
                }
                for r in self.reviews
            ]
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """Create Document from dictionary"""
        # Convert reviews
        reviews = []
        for r_data in data.get("reviews", []):
            issues = [DocumentIssue(**i) for i in r_data.get("issues", [])]
            review = DocumentReview(
                reviewer_name=r_data["reviewer_name"],
                issues=issues,
                overall_assessment=r_data["overall_assessment"],
                timestamp=r_data.get("timestamp", datetime.now().isoformat())
            )
            reviews.append(review)

        return cls(
            version=data["version"],
            title=data["title"],
            content=data["content"],
            document_type=data.get("document_type", "document"),
            metadata=data.get("metadata", {}),
            created_at=data.get("created_at", datetime.now().isoformat()),
            reviews=reviews
        )


# Backwards compatibility aliases
PRD = Document
PRDIssue = DocumentIssue
PRDReview = DocumentReview
