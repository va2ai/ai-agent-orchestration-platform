#!/usr/bin/env python3
"""
Dynamic Orchestrator: Uses AI-generated roundtable participants for any topic
"""
import asyncio
from typing import Tuple, Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from ..agents.meta_orchestrator import MetaOrchestrator, RoundtableConfig
from ..agents.dynamic_critic import DynamicCritic, DynamicModerator
from ..models.document_models import Document, DocumentReview
from ..storage.prd_storage import PRDStorage
from ..utils.convergence import ConvergenceChecker
from ..utils.logger import PRDLogger as RefinementLogger


class DynamicOrchestrator:
    """
    Orchestrator that uses AI to generate appropriate critics for any discussion topic.

    Flow:
    1. User provides topic and content
    2. Meta-orchestrator analyzes and generates roundtable participants
    3. Dynamic critics are created with AI-generated prompts
    4. Iterative refinement proceeds as normal
    5. Convergence when criteria met
    """

    def __init__(
        self,
        max_iterations: int = 3,
        verbose: bool = False,
        num_participants: int = 3,
        use_preset: Optional[str] = None
    ):
        """
        Initialize dynamic orchestrator.

        Args:
            max_iterations: Maximum refinement iterations
            verbose: Enable verbose logging
            num_participants: Number of roundtable participants (default: 3)
            use_preset: Optional preset ("prd", "code-review", "architecture", etc.)
        """
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.num_participants = num_participants
        self.use_preset = use_preset

        self.meta = MetaOrchestrator()
        self.storage = PRDStorage()
        self.convergence_checker = ConvergenceChecker()

        # Will be set after participant generation
        self.critics: List[DynamicCritic] = []
        self.moderator: Optional[DynamicModerator] = None
        self.roundtable_config: Optional[RoundtableConfig] = None

    def generate_roundtable(self, title: str, initial_content: str) -> RoundtableConfig:
        """
        Generate roundtable participants for the given topic.

        Args:
            title: Document title
            initial_content: Initial document content

        Returns:
            RoundtableConfig with generated participants
        """
        if self.use_preset:
            # Use preset configuration
            config = self.meta.generate_from_preset(self.use_preset)
        else:
            # AI generates participants based on content
            config = self.meta.generate_roundtable(
                topic=title,
                content=initial_content,
                num_participants=self.num_participants
            )

        # Create dynamic critics
        self.critics = [
            DynamicCritic(
                name=p.name,
                role=p.role,
                system_prompt=p.system_prompt
            )
            for p in config.participants
        ]

        # Create dynamic moderator
        self.moderator = DynamicModerator(
            moderator_focus=config.moderator_focus
        )

        self.roundtable_config = config

        return config

    async def run(
        self,
        title: str,
        initial_content: str,
        document_type: str = "document",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[Document, Dict[str, Any]]:
        """
        Run the dynamic refinement process.

        Args:
            title: Document title
            initial_content: Initial content
            document_type: Type of document (e.g., "prd", "architecture", "code-review")
            metadata: Optional metadata

        Returns:
            Tuple of (final_document, convergence_report)
        """

        # Create session
        session_id = self.storage.create_session(title)
        logger = RefinementLogger(session_id, verbose=self.verbose)

        logger.info("=" * 60)
        logger.info(f"Dynamic Roundtable Refinement")
        logger.info(f"   Topic: {title}")
        logger.info(f"   Document Type: {document_type}")
        logger.info(f"   Max Iterations: {self.max_iterations}")
        logger.info("=" * 60)
        logger.info("")

        # STEP 1: Generate roundtable participants
        logger.info("Generating roundtable participants...")
        config = self.generate_roundtable(title, initial_content)

        logger.info(f"Generated {len(self.critics)} participants:")
        for critic in self.critics:
            logger.info(f"  - {critic.name}: {critic.role}")
        logger.info(f"Moderator focus: {config.moderator_focus}")
        logger.info(f"Convergence criteria: {config.convergence_criteria}")
        logger.info("")

        # Create initial document
        doc = Document(
            version=1,
            title=title,
            content=initial_content,
            document_type=document_type,
            metadata=metadata or {},
            created_at=datetime.now().isoformat()
        )

        # Save initial version
        self.storage.save_prd(session_id, doc)
        logger.info(f"Saved {document_type} v{doc.version}")
        logger.info("")

        # Track metrics
        iteration = 1
        token_tracker = {critic.name: 0 for critic in self.critics}
        token_tracker["moderator"] = 0

        # Main refinement loop
        while iteration <= self.max_iterations:
            logger.info(f"Iteration {iteration}/{self.max_iterations}")

            # STEP 2: Critics review in parallel
            logger.info("  Participants reviewing...")
            review_tasks = [
                self._review_async(critic, doc, logger)
                for critic in self.critics
            ]
            results = await asyncio.gather(*review_tasks)

            reviews = []
            for review, tokens in results:
                reviews.append(review)
                doc.add_review(review)
                token_tracker[review.reviewer_name] += tokens["total_tokens"]

                # Log review summary
                high_count = sum(1 for i in review.issues if i.severity == "High")
                logger.info(f"    - {review.reviewer_name}: {len(review.issues)} issues ({high_count} high)")

            # STEP 3: Check convergence
            issue_counts = doc.get_issue_counts()
            converged, reason = self.convergence_checker.get_convergence_reason(
                doc,
                issue_counts,
                iteration,
                self.max_iterations
            )

            logger.info(f"  Status: {reason}")

            # Save reviews
            self.storage.save_reviews(session_id, doc.version, reviews)

            if converged:
                logger.info(f"{document_type.upper()} converged!")
                break

            # STEP 4: Moderator refines
            logger.info("  Moderator refining document...")
            refined_content, tokens = await self._refine_async(doc, reviews, logger)
            token_tracker["moderator"] += tokens["total_tokens"]

            # Create new version
            doc = Document(
                version=doc.version + 1,
                title=title,
                content=refined_content,
                document_type=document_type,
                metadata=metadata or {},
                created_at=datetime.now().isoformat()
            )

            self.storage.save_prd(session_id, doc)
            logger.info(f"Saved {document_type} v{doc.version}")
            logger.info("")

            iteration += 1

        # Generate convergence report
        final_issue_counts = doc.get_issue_counts()

        report = {
            "session_id": session_id,
            "title": title,
            "document_type": document_type,
            "initial_version": 1,
            "final_version": doc.version,
            "iterations": iteration - 1,
            "converged": converged,
            "convergence_reason": reason,
            "convergence_criteria": config.convergence_criteria,
            "roundtable_participants": [
                {
                    "name": p.name,
                    "role": p.role,
                    "expertise": p.expertise,
                    "perspective": p.perspective
                }
                for p in config.participants
            ],
            "moderator_focus": config.moderator_focus,
            "final_issue_count": final_issue_counts,
            "token_usage": token_tracker,
            "timestamps": {
                "start": datetime.now().isoformat(),
                "end": datetime.now().isoformat()
            }
        }

        self.storage.save_convergence_report(session_id, report)

        # Print summary
        logger.info("")
        logger.info("=" * 60)
        logger.info("REFINEMENT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Final Version: {doc.version}")
        logger.info(f"Converged: {converged}")
        logger.info(f"Reason: {reason}")
        logger.info(f"Final Issues: {final_issue_counts['high']} high, {final_issue_counts['medium']} medium, {final_issue_counts['low']} low")
        logger.info("")
        logger.info("Roundtable Participants:")
        for p in config.participants:
            logger.info(f"  - {p.name} ({p.role})")
        logger.info("")
        logger.info(f"Session: {session_id}")
        logger.info("")

        # Token usage summary
        total_tokens = sum(token_tracker.values())
        logger.info("Token Usage:")
        for agent, tokens in token_tracker.items():
            logger.info(f"  {agent}: {tokens:,}")
        logger.info(f"  TOTAL: {total_tokens:,}")

        return doc, report

    async def _review_async(self, critic: DynamicCritic, doc: Document, logger) -> Tuple[DocumentReview, Dict]:
        """Run critic review in executor (non-blocking)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, critic.review, doc, logger)

    async def _refine_async(self, doc: Document, reviews: List[DocumentReview], logger) -> Tuple[str, Dict]:
        """Run moderator refinement in executor (non-blocking)"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.moderator.refine, doc, reviews, logger)


if __name__ == "__main__":
    import sys

    # Test the dynamic orchestrator
    async def test():
        orchestrator = DynamicOrchestrator(
            max_iterations=2,
            verbose=True,
            num_participants=3
        )

        # Test with custom topic
        title = "Microservices Architecture for E-commerce"
        content = """# Architecture Proposal

Build a scalable microservices architecture for an e-commerce platform.

## Services
- User service
- Product catalog
- Order management
- Payment processing

## Goals
- Handle 10k requests/second
- 99.9% uptime
- Horizontal scalability
"""

        final_doc, report = await orchestrator.run(
            title=title,
            initial_content=content,
            document_type="architecture"
        )

        print("\n" + "=" * 60)
        print("FINAL DOCUMENT")
        print("=" * 60)
        print(final_doc.content)

    # Run test
    asyncio.run(test())
