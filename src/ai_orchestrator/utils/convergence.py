from typing import List, Tuple, Union
import difflib

# Support both old and new models
try:
    from ..models.prd_models import PRD, PRDReview
except ImportError:
    PRD = None
    PRDReview = None

try:
    from ..models.document_models import Document, DocumentReview
except ImportError:
    Document = None
    DocumentReview = None


class ConvergenceChecker:
    """Check if PRD/Document refinement has converged"""

    @staticmethod
    def has_converged(reviews: List[Union['PRDReview', 'DocumentReview']]) -> bool:
        """Check if no High severity issues remain"""
        for review in reviews:
            for issue in review.issues:
                if issue.severity == "High":
                    return False
        return True

    @staticmethod
    def calculate_delta(prev_doc: Union['PRD', 'Document'], current_doc: Union['PRD', 'Document']) -> float:
        """Calculate similarity between document versions (0.0 = identical, 1.0 = completely different)"""
        prev_content = prev_doc.content
        current_content = current_doc.content

        matcher = difflib.SequenceMatcher(None, prev_content, current_content)
        similarity = matcher.ratio()  # 0.0 to 1.0
        return 1.0 - similarity  # Convert to delta

    @staticmethod
    def get_convergence_reason(
        reviews: List[Union['PRDReview', 'DocumentReview']],
        iteration: int,
        max_iterations: int,
        prev_doc: Union['PRD', 'Document'] = None,
        current_doc: Union['PRD', 'Document'] = None
    ) -> Tuple[bool, str]:
        """Determine if converged and why"""

        # Check 1: No high severity issues
        if ConvergenceChecker.has_converged(reviews):
            high_count = sum(
                1 for r in reviews for i in r.issues if i.severity == "High"
            )
            return True, f"No high severity issues (0 remaining)"

        # Check 2: Max iterations
        if iteration >= max_iterations:
            high_count = sum(
                1 for r in reviews for i in r.issues if i.severity == "High"
            )
            return True, f"Max iterations reached ({max_iterations}). {high_count} high severity issues remain."

        # Check 3: Stable document (delta < 5%)
        if prev_doc and current_doc:
            delta = ConvergenceChecker.calculate_delta(prev_doc, current_doc)
            if delta < 0.05:
                return True, f"Document stable (delta: {delta:.2%})"

        # Not converged
        high_count = sum(
            1 for r in reviews for i in r.issues if i.severity == "High"
        )
        return False, f"{high_count} high severity issues remain"
