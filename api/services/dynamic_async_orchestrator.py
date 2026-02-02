#!/usr/bin/env python3
"""
Dynamic Async Orchestrator with WebSocket broadcasting for API
"""
import asyncio
from typing import Tuple, Dict, Any, Optional, List
from datetime import datetime

from ai_orchestrator.agents.meta_orchestrator import MetaOrchestrator, RoundtableConfig
from ai_orchestrator.agents.dynamic_critic import DynamicCritic, DynamicModerator
from ai_orchestrator.models.document_models import Document, DocumentReview
from ai_orchestrator.storage.prd_storage import PRDStorage
from ai_orchestrator.utils.convergence import ConvergenceChecker
from ai_orchestrator.utils.logger import PRDLogger as RefinementLogger
from ai_orchestrator.utils.llm_factory import get_model_name


class DynamicAsyncOrchestrator:
    """
    Async orchestrator that uses AI-generated roundtable participants with WebSocket updates.
    """

    def __init__(
        self,
        max_iterations: int = 3,
        verbose: bool = False,
        num_participants: int = 3,
        use_preset: Optional[str] = None,
        model: str = "gemini-3-pro-preview",
        model_strategy: str = "uniform",
        force_max_iterations: bool = False
    ):
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.num_participants = num_participants
        self.use_preset = use_preset
        self.model = model
        self.model_strategy = model_strategy
        self.force_max_iterations = force_max_iterations

        self.meta = MetaOrchestrator(model=model)
        self.storage = PRDStorage()
        self.convergence_checker = ConvergenceChecker()

        self.critics: List[DynamicCritic] = []
        self.moderator: Optional[DynamicModerator] = None
        self.roundtable_config: Optional[RoundtableConfig] = None

    async def broadcast_event(self, session_id: str, event_type: str, data: dict):
        """Broadcast event to WebSocket clients"""
        try:
            from api.routes.websocket import manager
            await manager.broadcast(session_id, {
                "type": event_type,
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"Failed to broadcast event: {e}")

    async def broadcast_log(self, session_id: str, level: str, message: str, critic: str = None):
        """Broadcast log message to Chrome console via WebSocket"""
        await self.broadcast_event(session_id, "log", {
            "level": level,  # debug, info, warn, error
            "message": message,
            "critic": critic
        })

    def generate_roundtable(self, title: str, initial_content: str, goal: str = None, participant_style: str = None) -> RoundtableConfig:
        """Generate roundtable participants"""
        if self.use_preset:
            config = self.meta.generate_from_preset(self.use_preset)
        else:
            config = self.meta.generate_roundtable(
                topic=title,
                content=initial_content,
                num_participants=self.num_participants,
                goal=goal,
                participant_style=participant_style
            )

        # Model Selection Logic
        diverse_models = [
            "gpt-5.2",
            "gemini-3-pro-preview",
            "gpt-5.2-pro",
            "gemini-3-flash-preview",
            "claude-3-5-sonnet-20240620",
            "gpt-5",
            "gemini-2.5-flash",
            "gpt-4o",
            "gemini-1.5-pro",
            "gpt-4.1"
        ]
        
        self.critics = []
        for i, p in enumerate(config.participants):
            assigned_model = self.model
            if self.model_strategy == "diverse":
                # Assign round-robin from high-quality models
                assigned_model = diverse_models[i % len(diverse_models)]
            
            # Store the model info in the participant object for UI display
            # (Note: This monkey-patches the Pydantic model instance if mutable, or we just rely on the critic having it)
            # Better: We'll modify the critic creation.
            
            critic = DynamicCritic(
                name=p.name,
                role=p.role,
                system_prompt=p.system_prompt,
                model=assigned_model
            )
            self.critics.append(critic)

        self.moderator = DynamicModerator(
            moderator_focus=config.moderator_focus,
            model=self.model # Moderator typically stays consistent with primary choice or best reasoning model
        )

        self.roundtable_config = config
        return config

    async def run(
        self,
        title: str,
        initial_content: str,
        document_type: str = "document",
        metadata: Optional[Dict[str, Any]] = None,
        goal: Optional[str] = None,
        participant_style: Optional[str] = None
    ) -> Tuple[Document, Dict[str, Any]]:
        """
        Run dynamic refinement with WebSocket updates.
        """

        # Create session
        session_id = self.storage.create_session(title)
        logger = RefinementLogger(session_id, verbose=self.verbose)

        await self.broadcast_event(session_id, "session_created", {
            "session_id": session_id,
            "title": title,
            "document_type": document_type,
            "goal": goal,
            "participant_style": participant_style,
            "model": self.model,
            "model_strategy": self.model_strategy
        })

        # Generate roundtable participants
        logger.info("Generating roundtable participants...")
        if goal:
            logger.info(f"Goal: {goal}")
        if participant_style:
            logger.info(f"Participant Style: {participant_style}")
            
        config = self.generate_roundtable(title, initial_content, goal, participant_style)

        await self.broadcast_event(session_id, "roundtable_generated", {
            "participants": [
                {
                    "name": p.name,
                    "role": p.role,
                    "expertise": p.expertise,
                    "perspective": p.perspective,
                    "model": get_model_name(self.critics[i].llm) # Send assigned model to UI
                }
                for i, p in enumerate(config.participants)
            ],
            "moderator_focus": config.moderator_focus,
            "convergence_criteria": config.convergence_criteria
        })

        # Save roundtable config to storage for resumption/monitoring
        self.storage.save_roundtable_config(session_id, config.dict())

        logger.info(f"Generated {len(self.critics)} participants:")
        for critic in self.critics:
            logger.info(f"  - {critic.name}: {critic.role}")

        # Create initial document
        doc = Document(
            version=1,
            title=title,
            content=initial_content,
            document_type=document_type,
            metadata=metadata or {},
            created_at=datetime.now().isoformat()
        )

        self.storage.save_prd(session_id, doc)
        logger.info(f"Saved {document_type} v{doc.version}")

        # Track tokens
        token_tracker = {critic.name: 0 for critic in self.critics}
        token_tracker["moderator"] = 0

        # Main refinement loop
        iteration = 1

        while iteration <= self.max_iterations:
            await self.broadcast_event(session_id, "iteration_start", {
                "iteration": iteration,
                "max_iterations": self.max_iterations
            })

            logger.info(f"Iteration {iteration}/{self.max_iterations}")

            # Parallel critic reviews
            logger.info("  Participants reviewing...")
            logger.debug(f"  Starting {len(self.critics)} parallel reviews...")
            await self.broadcast_log(session_id, "info", f"Starting {len(self.critics)} parallel reviews")

            review_tasks = [
                self._review_async(critic, doc, session_id, logger)
                for critic in self.critics
            ]

            try:
                results = await asyncio.gather(*review_tasks)
                logger.debug(f"  All {len(results)} reviews completed")
                await self.broadcast_log(session_id, "info", f"All {len(results)} reviews completed")
            except Exception as e:
                logger.error(f"  Review gathering failed: {str(e)}")
                await self.broadcast_log(session_id, "error", f"Review gathering failed: {str(e)}")
                raise

            reviews = []
            for idx, (review, tokens) in enumerate(results):
                logger.debug(f"  Processing review {idx+1}/{len(results)} from {review.reviewer_name}")
                reviews.append(review)
                doc.add_review(review)
                token_tracker[review.reviewer_name] += tokens["total_tokens"]

                high_count = sum(1 for i in review.issues if i.severity == "High")
                logger.info(f"    - {review.reviewer_name}: {len(review.issues)} issues ({high_count} high, {tokens['total_tokens']} tokens)")

            # Check convergence
            issue_counts = doc.get_issue_counts()
            converged, reason = self.convergence_checker.get_convergence_reason(
                reviews,
                iteration,
                self.max_iterations
            )

            await self.broadcast_event(session_id, "convergence_check", {
                "converged": converged,
                "reason": reason,
                "issue_counts": issue_counts
            })

            logger.info(f"  Status: {reason}")

            # Save reviews
            self.storage.save_reviews(session_id, doc.version, reviews)

            if converged:
                if self.force_max_iterations and iteration < self.max_iterations:
                    logger.info(f"{document_type.upper()} converged, but forcing next iteration as requested.")
                    await self.broadcast_log(session_id, "info", f"Converged, but forcing next iteration ({iteration}/{self.max_iterations})")
                else:
                    logger.info(f"{document_type.upper()} converged!")
                    break

            # Moderator refines
            await self.broadcast_event(session_id, "moderator_start", {})
            logger.info("  Moderator refining document...")

            refined_content, tokens = await self._refine_async(doc, reviews, logger)
            token_tracker["moderator"] += tokens["total_tokens"]

            await self.broadcast_event(session_id, "moderator_complete", {
                "new_version": doc.version + 1,
                "tokens": tokens
            })

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

            iteration += 1

        # Generate report
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

        await self.broadcast_event(session_id, "refinement_complete", {
            "final_version": doc.version,
            "converged": converged,
            "reason": reason,
            "final_issue_count": final_issue_counts
        })

        # Summary
        total_tokens = sum(token_tracker.values())
        logger.info("")
        logger.info("=" * 60)
        logger.info("REFINEMENT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Final Version: {doc.version}")
        logger.info(f"Converged: {converged}")
        logger.info(f"Reason: {reason}")
        logger.info(f"Final Issues: {final_issue_counts['high']} high, {final_issue_counts['medium']} medium, {final_issue_counts['low']} low")
        logger.info(f"Total Tokens: {total_tokens:,}")

        return doc, report

    async def _review_async(
        self,
        critic: DynamicCritic,
        doc: Document,
        session_id: str,
        logger
    ) -> Tuple[DocumentReview, Dict]:
        """Run critic review asynchronously"""
        logger.debug(f"[{critic.name}] Starting async review task")
        await self.broadcast_log(session_id, "debug", f"Starting review", critic.name)
        await self.broadcast_event(session_id, "critic_review_start", {
            "critic": critic.name,
            "role": critic.role
        })

        try:
            loop = asyncio.get_event_loop()
            logger.debug(f"[{critic.name}] Executing review in thread pool")
            await self.broadcast_log(session_id, "debug", f"Calling LLM for review", critic.name)
            review, tokens = await loop.run_in_executor(None, critic.review, doc, logger)
            logger.debug(f"[{critic.name}] Review execution completed")
            await self.broadcast_log(session_id, "info", f"Review completed: {len(review.issues)} issues found", critic.name)
        except Exception as e:
            logger.error(f"[{critic.name}] Review failed: {str(e)}")
            await self.broadcast_log(session_id, "error", f"Review failed: {str(e)}", critic.name)
            import traceback
            logger.error(f"[{critic.name}] Traceback: {traceback.format_exc()}")
            raise

        high_count = sum(1 for i in review.issues if i.severity == "High")
        logger.debug(f"[{critic.name}] Broadcasting completion event")

        await self.broadcast_event(session_id, "critic_review_complete", {
            "critic": critic.name,
            "issues_count": len(review.issues),
            "high_count": high_count,
            "tokens": tokens,
            "top_issues": [i.model_dump() for i in review.issues[:2]],
            "assessment": review.overall_assessment
        })

        return review, tokens

    async def _refine_async(
        self,
        doc: Document,
        reviews: List[DocumentReview],
        logger
    ) -> Tuple[str, Dict]:
        """Run moderator refinement asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.moderator.refine, doc, reviews, logger)

    async def continue_from(
        self,
        session_id: str,
        current_doc: Document,
        start_iteration: int,
        document_type: str = "document",
        metadata: Optional[Dict[str, Any]] = None,
        goal: Optional[str] = None,
        participant_style: Optional[str] = None
    ) -> Tuple[Document, Dict[str, Any]]:
        """
        Continue refinement from an existing document and iteration.
        """
        logger = RefinementLogger(session_id, verbose=self.verbose)

        await self.broadcast_event(session_id, "session_resumed", {
            "session_id": session_id,
            "start_iteration": start_iteration,
            "max_iterations": self.max_iterations,
            "start_version": current_doc.version
        })

        logger.info(f"Resuming refinement from iteration {start_iteration}")

        # Load existing roundtable config
        config_dict = self.storage.load_roundtable_config(session_id)
        if not config_dict:
            raise ValueError("Roundtable config not found for session")

        # Reconstruct roundtable from saved config
        self.roundtable_config = RoundtableConfig(**config_dict)

        # Recreate critics and moderator
        diverse_models = [
            "gpt-5.2",
            "gemini-3-pro-preview",
            "gpt-5.2-pro",
            "gemini-3-flash-preview",
            "claude-3-5-sonnet-20240620",
            "gpt-5",
            "gemini-2.5-flash",
            "gpt-4o",
            "gemini-1.5-pro",
            "gpt-4.1"
        ]

        self.critics = []
        for i, p in enumerate(self.roundtable_config.participants):
            assigned_model = self.model
            if self.model_strategy == "diverse":
                assigned_model = diverse_models[i % len(diverse_models)]

            critic = DynamicCritic(
                name=p.name,
                role=p.role,
                system_prompt=p.system_prompt,
                model=assigned_model
            )
            self.critics.append(critic)

        self.moderator = DynamicModerator(
            moderator_focus=self.roundtable_config.moderator_focus,
            model=self.model
        )

        logger.info(f"Reconstructed {len(self.critics)} participants from saved config")

        # Track tokens
        token_tracker = {critic.name: 0 for critic in self.critics}
        token_tracker["moderator"] = 0

        # Continue refinement loop
        doc = current_doc
        iteration = start_iteration + 1
        converged = False
        reason = ""

        while iteration <= self.max_iterations:
            await self.broadcast_event(session_id, "iteration_start", {
                "iteration": iteration,
                "max_iterations": self.max_iterations
            })

            logger.info(f"Iteration {iteration}/{self.max_iterations}")

            # Parallel critic reviews
            logger.info("  Participants reviewing...")
            await self.broadcast_log(session_id, "info", f"Starting {len(self.critics)} parallel reviews")

            review_tasks = [
                self._review_async(critic, doc, session_id, logger)
                for critic in self.critics
            ]

            try:
                results = await asyncio.gather(*review_tasks)
                await self.broadcast_log(session_id, "info", f"All {len(results)} reviews completed")
            except Exception as e:
                logger.error(f"  Review gathering failed: {str(e)}")
                await self.broadcast_log(session_id, "error", f"Review gathering failed: {str(e)}")
                raise

            reviews = []
            for idx, (review, tokens) in enumerate(results):
                reviews.append(review)
                doc.add_review(review)
                token_tracker[review.reviewer_name] += tokens["total_tokens"]

                high_count = sum(1 for i in review.issues if i.severity == "High")
                logger.info(f"    - {review.reviewer_name}: {len(review.issues)} issues ({high_count} high, {tokens['total_tokens']} tokens)")

            # Check convergence
            issue_counts = doc.get_issue_counts()
            converged, reason = self.convergence_checker.get_convergence_reason(
                reviews,
                iteration,
                self.max_iterations
            )

            await self.broadcast_event(session_id, "convergence_check", {
                "converged": converged,
                "reason": reason,
                "issue_counts": issue_counts
            })

            logger.info(f"  Status: {reason}")

            # Save reviews
            self.storage.save_reviews(session_id, doc.version, reviews)

            if converged:
                if self.force_max_iterations and iteration < self.max_iterations:
                    logger.info(f"Document converged, but forcing next iteration as requested.")
                    await self.broadcast_log(session_id, "info", f"Converged, but forcing next iteration ({iteration}/{self.max_iterations})")
                else:
                    logger.info(f"Document converged!")
                    break

            # Moderator refines
            await self.broadcast_event(session_id, "moderator_start", {})
            logger.info("  Moderator refining document...")

            refined_content, tokens = await self._refine_async(doc, reviews, logger)
            token_tracker["moderator"] += tokens["total_tokens"]

            await self.broadcast_event(session_id, "moderator_complete", {
                "new_version": doc.version + 1,
                "tokens": tokens
            })

            # Create new version
            doc = Document(
                version=doc.version + 1,
                title=current_doc.title,
                content=refined_content,
                document_type=document_type,
                metadata=metadata or {},
                created_at=datetime.now().isoformat()
            )

            self.storage.save_prd(session_id, doc)
            logger.info(f"Saved {document_type} v{doc.version}")

            iteration += 1

        # Generate updated report
        final_issue_counts = doc.get_issue_counts()

        report = {
            "session_id": session_id,
            "title": current_doc.title,
            "document_type": document_type,
            "initial_version": 1,
            "final_version": doc.version,
            "iterations": iteration - 1,
            "converged": converged,
            "convergence_reason": reason,
            "convergence_criteria": self.roundtable_config.convergence_criteria,
            "roundtable_participants": [
                {
                    "name": p.name,
                    "role": p.role,
                    "expertise": p.expertise,
                    "perspective": p.perspective
                }
                for p in self.roundtable_config.participants
            ],
            "moderator_focus": self.roundtable_config.moderator_focus,
            "final_issue_count": final_issue_counts,
            "token_usage": token_tracker,
            "timestamps": {
                "start": datetime.now().isoformat(),
                "end": datetime.now().isoformat()
            },
            "continued_from_iteration": start_iteration
        }

        self.storage.save_convergence_report(session_id, report)

        await self.broadcast_event(session_id, "refinement_complete", {
            "final_version": doc.version,
            "converged": converged,
            "reason": reason,
            "final_issue_count": final_issue_counts
        })

        # Summary
        total_tokens = sum(token_tracker.values())
        logger.info("")
        logger.info("=" * 60)
        logger.info("CONTINUATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Final Version: {doc.version}")
        logger.info(f"Converged: {converged}")
        logger.info(f"Reason: {reason}")
        logger.info(f"Final Issues: {final_issue_counts['high']} high, {final_issue_counts['medium']} medium, {final_issue_counts['low']} low")
        logger.info(f"Additional Tokens: {total_tokens:,}")

        return doc, report
