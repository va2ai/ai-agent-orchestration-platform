"""
Optional LangExtract-based structured extraction agent.

Why LangExtract?
- It produces structured extractions with precise source grounding (character offsets).
- Great for "grounded issues" story in interviews / portfolio.
- Enables provenance tracking for every extracted fact.

Install:
    pip install langextract

Or in your pyproject optional extras:
    pip install -e ".[langextract]"

(As of Feb 2026, LangExtract is published by Google as the `langextract` package.)

Example usage:
    from ai_orchestrator.agents.extractor_langextract import (
        LangExtractExtractorAgent,
        LangExtractSpec,
    )

    spec = LangExtractSpec(
        prompt_description="Extract all claims and their evidence from the document",
        examples=[
            {"claim": "The product launched in Q1", "evidence": "paragraph 2"},
        ],
        model_id="gpt-4o",
    )

    agent = LangExtractExtractorAgent(name="claim_extractor", spec=spec)
    result = agent.extract(document_text)
    issues = agent.to_issues(result)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence


@dataclass
class ExtractedIssue:
    """An issue extracted from a document with provenance.

    This is a simplified representation that can be mapped to the
    ai_orchestrator.types.Issue class.
    """

    severity: str
    message: str
    evidence: Optional[Mapping[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "message": self.message,
            "evidence": dict(self.evidence) if self.evidence else None,
        }


@dataclass
class LangExtractSpec:
    """Defines what to extract using LangExtract.

    Attributes:
        prompt_description: What you want extracted (natural language).
        examples: Few-shot examples LangExtract uses to learn the schema.
        model_id: Model identifier (e.g., 'gemini-2.0-flash', 'gpt-4o', 'claude-3-5-sonnet').
        fence_output: Whether to fence output in markdown code blocks.
        use_schema_constraints: Whether to use JSON schema constraints.
    """

    prompt_description: str
    examples: Sequence[Mapping[str, Any]] = field(default_factory=list)
    model_id: str = "gpt-4o"
    fence_output: bool = True
    use_schema_constraints: bool = False


@dataclass
class LangExtractExtractorAgent:
    """Structured extraction agent using LangExtract.

    This agent extracts structured information from documents with
    precise source grounding (character offsets for provenance).

    Example:
        spec = LangExtractSpec(
            prompt_description="Extract contradictions and inconsistencies",
            examples=[{"contradiction": "...", "location": "..."}],
        )
        agent = LangExtractExtractorAgent(name="contradiction_extractor", spec=spec)
        result = agent.extract(document)
        issues = agent.to_issues(result)
    """

    name: str = "langextract_extractor"
    spec: Optional[LangExtractSpec] = None
    api_key_env: str = "OPENAI_API_KEY"  # Used by OpenAI provider example

    def extract(
        self,
        text: str,
        *,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Extract structured information from text.

        Args:
            text: The document text to extract from.
            api_key: Optional API key (falls back to environment variable).

        Returns:
            Dictionary containing the raw extraction result.

        Raises:
            ValueError: If spec is not set.
            ImportError: If langextract is not installed.
        """
        if self.spec is None:
            raise ValueError("LangExtractExtractorAgent.spec must be set")

        try:
            import langextract as lx  # type: ignore
        except ImportError as e:
            raise ImportError(
                "LangExtract is not installed. "
                "Run `pip install langextract` (or `pip install -e .[langextract]`)."
            ) from e

        # LangExtract's top-level API supports multi-provider model_id routing.
        # Using OpenAI requires api_key, fence_output=True, use_schema_constraints=False
        # per project README.
        # You can swap model_id to Gemini/Ollama/local as you prefer.
        result = lx.extract(  # type: ignore
            text_or_documents=text,
            prompt_description=self.spec.prompt_description,
            examples=list(self.spec.examples),
            model_id=self.spec.model_id,
            api_key=api_key,
            fence_output=self.spec.fence_output,
            use_schema_constraints=self.spec.use_schema_constraints,
        )

        # `result` shape can vary by provider/version; we keep it generic.
        return {"raw": result}

    def to_issues(
        self,
        extraction_payload: Dict[str, Any],
    ) -> List[ExtractedIssue]:
        """Map extracted structures into Issue objects.

        This is intentionally generic. For specific use cases, you'd typically map:
            - contradictions -> high severity
            - missing evidence -> high/medium severity
            - unclear timeline -> medium severity
            - minor formatting -> low severity

        Args:
            extraction_payload: The result from extract().

        Returns:
            List of ExtractedIssue objects.
        """
        raw = extraction_payload.get("raw")
        issues: List[ExtractedIssue] = []

        # Best-effort parsing (LangExtract returns objects that are usually dict-like / iterable).
        # You will likely customize this once you see real outputs.
        if raw is None:
            return issues

        # If raw contains "extractions" list, map them.
        extractions = None
        if isinstance(raw, dict):
            extractions = raw.get("extractions") or raw.get("items") or raw.get("results")

        if isinstance(extractions, list):
            for ex in extractions:
                if isinstance(ex, dict):
                    severity = str(
                        ex.get("severity") or ex.get("priority") or "low"
                    ).lower()
                    message = str(
                        ex.get("message")
                        or ex.get("issue")
                        or ex.get("fact")
                        or ex.get("description")
                        or "extracted item"
                    )
                    evidence = ex.get("provenance") or ex.get("source") or ex.get("evidence") or ex
                    issues.append(
                        ExtractedIssue(
                            severity=severity,
                            message=message,
                            evidence=evidence,
                        )
                    )
        else:
            # Fallback single issue: you got output but didn't map it yet.
            issues.append(
                ExtractedIssue(
                    severity="low",
                    message="LangExtract output captured; mapping not configured",
                    evidence={"raw": raw},
                )
            )

        return issues

    def extract_and_convert(
        self,
        text: str,
        *,
        api_key: Optional[str] = None,
    ) -> List[ExtractedIssue]:
        """Convenience method: extract and convert to issues in one call.

        Args:
            text: The document text to extract from.
            api_key: Optional API key.

        Returns:
            List of ExtractedIssue objects.
        """
        result = self.extract(text, api_key=api_key)
        return self.to_issues(result)


# Pre-configured extractors for common use cases


def create_contradiction_extractor(
    model_id: str = "gpt-4o",
) -> LangExtractExtractorAgent:
    """Create an extractor for finding contradictions in documents.

    Args:
        model_id: Model to use for extraction.

    Returns:
        Configured LangExtractExtractorAgent.
    """
    spec = LangExtractSpec(
        prompt_description=(
            "Extract all contradictions, inconsistencies, and conflicting statements "
            "from the document. For each contradiction, identify the conflicting claims "
            "and their locations in the text."
        ),
        examples=[
            {
                "contradiction": "Timeline conflict",
                "claim1": "Project started in January 2025",
                "claim2": "Initial planning began in March 2025",
                "severity": "high",
            },
        ],
        model_id=model_id,
    )
    return LangExtractExtractorAgent(name="contradiction_extractor", spec=spec)


def create_evidence_extractor(
    model_id: str = "gpt-4o",
) -> LangExtractExtractorAgent:
    """Create an extractor for finding claims and their supporting evidence.

    Args:
        model_id: Model to use for extraction.

    Returns:
        Configured LangExtractExtractorAgent.
    """
    spec = LangExtractSpec(
        prompt_description=(
            "Extract all factual claims from the document along with their supporting "
            "evidence. Mark claims that lack evidence or have weak evidence."
        ),
        examples=[
            {
                "claim": "The system handles 10,000 requests per second",
                "evidence": "Load testing results in Appendix A",
                "evidence_strength": "strong",
            },
            {
                "claim": "Users prefer the new interface",
                "evidence": None,
                "evidence_strength": "missing",
                "severity": "high",
            },
        ],
        model_id=model_id,
    )
    return LangExtractExtractorAgent(name="evidence_extractor", spec=spec)


def create_risk_extractor(
    model_id: str = "gpt-4o",
) -> LangExtractExtractorAgent:
    """Create an extractor for finding risks and concerns in documents.

    Args:
        model_id: Model to use for extraction.

    Returns:
        Configured LangExtractExtractorAgent.
    """
    spec = LangExtractSpec(
        prompt_description=(
            "Extract all risks, concerns, and potential issues mentioned or implied "
            "in the document. Include technical risks, business risks, timeline risks, "
            "and any other concerns."
        ),
        examples=[
            {
                "risk": "Single point of failure in authentication service",
                "category": "technical",
                "severity": "high",
                "mitigation_mentioned": False,
            },
        ],
        model_id=model_id,
    )
    return LangExtractExtractorAgent(name="risk_extractor", spec=spec)
