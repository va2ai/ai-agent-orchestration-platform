import asyncio
from datetime import datetime
from typing import List, Tuple, Dict, Any
from ai_orchestrator.agents.prd_critic import PRDCritic
from ai_orchestrator.agents.engineering_critic import EngineeringCritic
from ai_orchestrator.agents.ai_risk_critic import AIRiskCritic
from ai_orchestrator.agents.moderator import Moderator
from ai_orchestrator.models.prd_models import PRD, PRDReview
from ai_orchestrator.storage.prd_storage import PRDStorage
from ai_orchestrator.utils.convergence import ConvergenceChecker
from ai_orchestrator.utils.logger import PRDLogger

class AsyncLoopingOrchestrator:
    """Async orchestrator with WebSocket broadcasting"""

    def __init__(self, max_iterations: int = 3, verbose: bool = False):
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.storage = PRDStorage()

        # Initialize agents
        self.critics = [
            PRDCritic(),
            EngineeringCritic(),
            AIRiskCritic()
        ]
        self.moderator = Moderator()
        self.convergence_checker = ConvergenceChecker()

        # Token tracking
        self.token_usage = {
            'prd_critic': 0,
            'engineering_critic': 0,
            'ai_risk_critic': 0,
            'moderator': 0
        }

    async def broadcast_event(self, session_id: str, event_type: str, data: dict):
        """Broadcast event to WebSocket clients"""
        from api.routes.websocket import manager
        await manager.broadcast(session_id, {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        })

    async def run(self, title: str, initial_content: str) -> Tuple[PRD, Dict[str, Any]]:
        """Run looping refinement and return final PRD + report"""

        # Create session
        session_id = self.storage.create_session(title)
        await self.broadcast_event(session_id, "session_created", {"session_id": session_id})

        # Initialize logger
        logger = PRDLogger(session_id, verbose=self.verbose)
        logger.section(f"PRD Refinement Session: {title}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Max iterations: {self.max_iterations}")

        # Initialize PRD
        prd = PRD(version=1, title=title, content=initial_content)
        self.storage.save_prd(session_id, prd)
        logger.info(f"Initial PRD length: {len(initial_content)} chars")

        # Track history
        history = []
        iteration = 1
        prev_prd = None

        # Main loop
        while iteration <= self.max_iterations:
            logger.section(f"Iteration {iteration}/{self.max_iterations}")

            await self.broadcast_event(session_id, "iteration_start", {
                "iteration": iteration,
                "max_iterations": self.max_iterations
            })

            # Step 1: Parallel critic reviews
            logger.info("Starting critic reviews...")
            review_tasks = [
                self._review_async(critic, prd, session_id, logger)
                for critic in self.critics
            ]
            reviews = await asyncio.gather(*review_tasks)

            # Save reviews
            self.storage.save_reviews(session_id, prd.version, reviews)

            # Step 2: Check convergence
            converged, reason = self.convergence_checker.get_convergence_reason(
                reviews, iteration, self.max_iterations, prev_prd, prd
            )

            logger.log_convergence(converged, reason, iteration)

            await self.broadcast_event(session_id, "convergence_check", {
                "converged": converged,
                "reason": reason,
                "iteration": iteration
            })

            # Count issues
            high_count = sum(1 for r in reviews for i in r.issues if i.severity == "High")
            medium_count = sum(1 for r in reviews for i in r.issues if i.severity == "Medium")
            low_count = sum(1 for r in reviews for i in r.issues if i.severity == "Low")

            history.append({
                "iteration": iteration,
                "version": prd.version,
                "reviews": [r.model_dump() for r in reviews],
                "converged": converged,
                "reason": reason,
                "tokens": dict(self.token_usage),
                "issue_count": {
                    "high": high_count,
                    "medium": medium_count,
                    "low": low_count
                }
            })

            if converged:
                break

            # Step 3: Moderator refinement
            await self.broadcast_event(session_id, "moderator_start", {})

            logger.info("Moderator refining PRD...")
            refined_content, tokens = await self._refine_async(prd, reviews, logger)

            # Track tokens
            self.token_usage['moderator'] += tokens.get('total_tokens', 0)

            # Create new PRD version
            prev_prd = prd
            prd = PRD(
                version=prd.version + 1,
                title=title,
                content=refined_content,
                metadata={"refined_from": prd.version}
            )
            self.storage.save_prd(session_id, prd)
            logger.info(f"Created PRD v{prd.version}")

            await self.broadcast_event(session_id, "moderator_complete", {
                "new_version": prd.version,
                "tokens": tokens
            })

            iteration += 1

        # Generate final report
        report = self._generate_report(
            session_id, title, prd, reviews, history, converged, reason
        )
        self.storage.save_convergence_report(session_id, report)

        await self.broadcast_event(session_id, "refinement_complete", {
            "final_version": prd.version,
            "report": report
        })

        return prd, report

    async def _review_async(self, critic, prd, session_id, logger):
        """Async wrapper for critic review with broadcasting"""
        await self.broadcast_event(session_id, "critic_review_start", {
            "critic": critic.name
        })

        # Run synchronous critic.review in executor
        loop = asyncio.get_event_loop()
        review, tokens = await loop.run_in_executor(None, critic.review, prd, logger)

        # Track tokens
        self.token_usage[critic.name] += tokens.get('total_tokens', 0)

        high_count = sum(1 for i in review.issues if i.severity == "High")

        await self.broadcast_event(session_id, "critic_review_complete", {
            "critic": critic.name,
            "issues_count": len(review.issues),
            "high_count": high_count,
            "tokens": tokens
        })

        return review

    async def _refine_async(self, prd, reviews, logger):
        """Async wrapper for moderator refinement"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.moderator.refine, prd, reviews, logger)

    def _generate_report(self, session_id, title, prd, reviews, history, converged, reason):
        """Generate convergence report"""
        high_count = sum(1 for r in reviews for i in r.issues if i.severity == "High")
        medium_count = sum(1 for r in reviews for i in r.issues if i.severity == "Medium")
        low_count = sum(1 for r in reviews for i in r.issues if i.severity == "Low")

        total_issues = sum(len(h["reviews"][0].get("issues", [])) +
                          len(h["reviews"][1].get("issues", [])) +
                          len(h["reviews"][2].get("issues", []))
                          for h in history)

        return {
            "session_id": session_id,
            "title": title,
            "initial_version": 1,
            "final_version": prd.version,
            "iterations": len(history),
            "converged": converged,
            "convergence_reason": reason,
            "total_issues_identified": total_issues,
            "final_issue_count": {
                "high": high_count,
                "medium": medium_count,
                "low": low_count
            },
            "timestamps": {
                "start": history[0]["reviews"][0]["timestamp"] if history else None,
                "end": datetime.now().isoformat()
            },
            "token_usage": self.token_usage,
            "history": history
        }
