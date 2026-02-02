#!/usr/bin/env python3
"""
Dynamic Critic: A critic agent that can take on any role based on generated configuration
"""
from typing import Tuple, Optional
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from ..models.document_models import Document, DocumentReview, DocumentIssue
from ..utils.llm_factory import create_llm, extract_token_usage
import os


class DynamicCritic:
    """
    A flexible critic agent that can review documents from any perspective.

    Unlike hardcoded critics (PRDCritic, EngineeringCritic), this critic accepts:
    - name: Display name (e.g., "Senior Backend Engineer")
    - role: What they review (e.g., "Scalability and performance")
    - system_prompt: Complete instructions for this critic

    This allows the system to generate critics on-the-fly based on the discussion topic.
    """

    def __init__(
        self,
        name: str,
        role: str,
        system_prompt: str,
        model: str = "gpt-4-turbo",
        temperature: float = 0.2
    ):
        """
        Initialize a dynamic critic.

        Args:
            name: Critic's name/title (e.g., "Security Expert")
            role: What they focus on (e.g., "Review for security vulnerabilities")
            system_prompt: Complete system prompt defining their review criteria
            model: LLM model to use
            temperature: LLM temperature
        """
        self.name = name
        self.role = role
        self.system_prompt = system_prompt
        self.llm = create_llm(model=model, temperature=temperature)
        self.parser = JsonOutputParser(pydantic_object=DocumentReview)

    def review(
        self,
        document: Document,
        logger: Optional[any] = None
    ) -> Tuple[DocumentReview, dict]:
        """
        Review the document from this critic's perspective.

        Args:
            document: The document to review
            logger: Optional logger for tracking

        Returns:
            Tuple of (DocumentReview, token_usage)
        """

        human_prompt = f"""Review the following document:

Title: {document.title}
Version: {document.version}

Content:
{document.content}

Provide your expert review following the instructions in your system prompt.
Focus on your specific area of expertise and flag any issues you identify.
"""

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=human_prompt)
        ]

        if logger:
            logger.debug(f"[{self.name}] Starting review...")
            logger.debug(f"System prompt length: {len(self.system_prompt)} chars")
            logger.debug(f"Document content length: {len(document.content)} chars")

        response = self.llm.invoke(messages)

        if logger:
            logger.debug(f"[{self.name}] Received response ({len(response.content)} chars)")
            logger.debug(f"[{self.name}] Response preview: {response.content[:200]}...")

        # Parse response
        try:
            if logger:
                logger.debug(f"[{self.name}] Parsing JSON response...")
            review_data = self.parser.parse(response.content)
            if logger:
                logger.debug(f"[{self.name}] Successfully parsed JSON")
        except Exception as e:
            if logger:
                logger.error(f"[{self.name}] JSON parsing failed: {str(e)}")
                logger.error(f"[{self.name}] Full response: {response.content}")
            raise

        # Transform issues to match expected schema (defensive coding)
        if "issues" in review_data:
            transformed_issues = []
            for issue in review_data["issues"]:
                # Handle different field names that LLM might use
                transformed_issue = {
                    "category": issue.get("category") or issue.get("section") or "General",
                    "description": issue.get("description") or issue.get("issue") or "",
                    "severity": issue.get("severity", "Low"),
                    "suggested_fix": issue.get("suggested_fix") or issue.get("fix"),
                    "reviewer": issue.get("reviewer") or self.name
                }
                transformed_issues.append(transformed_issue)
            review_data["issues"] = transformed_issues

        # Create review object
        review = DocumentReview(
            reviewer_name=self.name,
            **review_data
        )

        # Extract token usage (handles both OpenAI and Gemini formats)
        token_usage = extract_token_usage(response)

        if logger:
            high_count = sum(1 for issue in review.issues if issue.severity == "High")
            medium_count = sum(1 for issue in review.issues if issue.severity == "Medium")
            low_count = sum(1 for issue in review.issues if issue.severity == "Low")
            logger.info(f"[{self.name}] Found {len(review.issues)} issues: {high_count} high, {medium_count} medium, {low_count} low")
            logger.info(f"[{self.name}] Tokens: {token_usage['total_tokens']}")

        return review, token_usage

    def __repr__(self):
        return f"DynamicCritic(name='{self.name}', role='{self.role}')"


class DynamicModerator:
    """
    A flexible moderator that can refine documents based on any set of reviews.

    Takes a moderator_focus instruction that tells it how to incorporate feedback.
    """

    def __init__(
        self,
        moderator_focus: str,
        model: str = "gpt-4-turbo",
        temperature: float = 0.3
    ):
        """
        Initialize a dynamic moderator.

        Args:
            moderator_focus: Instructions on how to refine (e.g., "Fix all High issues, improve clarity")
            model: LLM model to use
            temperature: LLM temperature
        """
        self.moderator_focus = moderator_focus
        # Moderator outputs markdown, not JSON, so disable json_mode
        self.llm = create_llm(model=model, temperature=temperature, json_mode=False)

    def refine(
        self,
        document: Document,
        reviews: list[DocumentReview],
        logger: Optional[any] = None
    ) -> Tuple[str, dict]:
        """
        Refine the document based on reviews.

        Args:
            document: Current document version
            reviews: Reviews from all critics
            logger: Optional logger

        Returns:
            Tuple of (refined_content, token_usage)
        """

        # Build review summary
        review_summary = []
        for review in reviews:
            review_summary.append(f"\n=== {review.reviewer_name} ===")
            review_summary.append(f"Overall: {review.overall_assessment}\n")

            for issue in review.issues:
                review_summary.append(f"[{issue.severity}] {issue.category}: {issue.description}")
                if issue.suggested_fix:
                    review_summary.append(f"  → Suggested fix: {issue.suggested_fix}")

        reviews_text = "\n".join(review_summary)

        system_prompt = f"""You are a skilled moderator facilitating a document refinement discussion.

Your job is to take feedback from multiple expert reviewers and create an improved version
of the document that addresses their concerns.

Focus: {self.moderator_focus}

Guidelines:
- Address ALL High severity issues
- Address Medium issues if they significantly improve quality
- Keep the document focused and concise
- Maintain the original intent while improving clarity
- Preserve the document structure and formatting
- Don't add unnecessary content

Output ONLY the refined document content (markdown format).
"""

        human_prompt = f"""Current Document:

Title: {document.title}
Version: {document.version}

Content:
{document.content}

Expert Reviews:
{reviews_text}

Please create an improved version that addresses the feedback.
Output the complete refined document.
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        if logger:
            logger.debug("[Moderator] Refining document...")
            logger.debug(f"Document length: {len(document.content)} chars")
            logger.debug(f"Total issues to address: {sum(len(r.issues) for r in reviews)}")

        response = self.llm.invoke(messages)

        if logger:
            logger.debug(f"[Moderator] Generated refined content ({len(response.content)} chars)")

        refined_content = response.content.strip()

        # Extract token usage (handles both OpenAI and Gemini formats)
        token_usage = extract_token_usage(response)

        if logger:
            logger.info(f"[Moderator] Refined content: {len(refined_content)} chars")
            logger.info(f"[Moderator] Tokens: {token_usage['total_tokens']}")

        return refined_content, token_usage
