from agents.prd_critic import PRDCritic
from agents.engineering_critic import EngineeringCritic
from agents.ai_risk_critic import AIRiskCritic
from agents.moderator import Moderator
from models.prd_models import PRD, PRDReview
from storage.prd_storage import PRDStorage
from utils.convergence import ConvergenceChecker
from utils.logger import PRDLogger
from typing import List, Tuple, Dict, Any
from datetime import datetime

class LoopingOrchestrator:
    """Orchestrate looping PRD refinement"""

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

    def run(self, title: str, initial_content: str) -> Tuple[PRD, Dict[str, Any]]:
        """Run looping refinement and return final PRD + report"""

        # Create session
        session_id = self.storage.create_session(title)
        print(f"Created session: {session_id}")

        # Initialize logger
        logger = PRDLogger(session_id, verbose=self.verbose)
        logger.section(f"PRD Refinement Session: {title}")
        logger.info(f"Session ID: {session_id}")
        logger.info(f"Max iterations: {self.max_iterations}")
        logger.info(f"Verbose mode: {self.verbose}")

        # Initialize PRD
        prd = PRD(version=1, title=title, content=initial_content)
        self.storage.save_prd(session_id, prd)
        print(f"Saved PRD v{prd.version}")
        logger.info(f"Initial PRD length: {len(initial_content)} chars")

        # Track history
        history = []
        iteration = 1
        prev_prd = None

        # Main loop
        while iteration <= self.max_iterations:
            print(f"\nIteration {iteration}/{self.max_iterations}")
            logger.section(f"Iteration {iteration}/{self.max_iterations}")

            # Step 1: Critics review
            print("  Critics reviewing...")
            logger.info("Starting critic reviews...")
            reviews: List[PRDReview] = []

            for critic in self.critics:
                review, tokens = critic.review(prd, logger)
                reviews.append(review)

                # Track tokens
                self.token_usage[critic.name] += tokens.get('total_tokens', 0)

                high_count = sum(1 for i in review.issues if i.severity == "High")
                print(f"    - {review.reviewer}: {len(review.issues)} issues ({high_count} high)")

            # Save reviews
            self.storage.save_reviews(session_id, prd.version, reviews)

            # Step 2: Check convergence
            converged, reason = self.convergence_checker.get_convergence_reason(
                reviews, iteration, self.max_iterations, prev_prd, prd
            )

            print(f"  Status: {reason}")
            logger.log_convergence(converged, reason, iteration)

            history.append({
                "iteration": iteration,
                "version": prd.version,
                "reviews": [r.model_dump() for r in reviews],
                "converged": converged,
                "reason": reason,
                "tokens": dict(self.token_usage)
            })

            if converged:
                print("PRD converged!")
                logger.info("PRD converged!")
                break

            # Step 3: Moderator refines
            print("  Moderator refining PRD...")
            logger.info("Starting moderator refinement...")
            prev_prd = prd
            prev_length = len(prev_prd.content)

            refined_content, tokens = self.moderator.refine(prd, reviews, logger)

            # Track tokens
            self.token_usage['moderator'] += tokens.get('total_tokens', 0)

            prd = PRD(
                version=prd.version + 1,
                title=prd.title,
                content=refined_content,
                metadata={"refined_from": prev_prd.version}
            )

            self.storage.save_prd(session_id, prd)
            print(f"Saved PRD v{prd.version}")

            logger.log_refinement(prd.version, prev_length, len(refined_content))

            iteration += 1

        # Generate final report
        logger.section("Generating Final Report")
        report = self._generate_report(session_id, prd, history)
        report['token_usage'] = dict(self.token_usage)
        self.storage.save_convergence_report(session_id, report)

        print(f"\nReport saved to: {session_id}/convergence_report.json")
        logger.info(f"Report saved to: convergence_report.json")

        # Log token summary
        logger.log_token_summary(self.token_usage)

        # Final summary
        logger.section("Refinement Complete")
        logger.info(f"Final version: {prd.version}")
        logger.info(f"Converged: {report['converged']}")
        logger.info(f"Total tokens used: {sum(self.token_usage.values())}")
        logger.info(f"Log file: data/prds/{session_id}/refinement.log")

        return prd, report

    def _generate_report(self, session_id: str, final_prd: PRD, history: List[dict]) -> dict:
        """Generate convergence report"""
        total_issues = sum(
            len(r.get("issues", []))
            for h in history
            for r in h.get("reviews", [])
        )

        final_reviews = history[-1]["reviews"] if history else []
        final_issue_count = {
            "high": sum(1 for r in final_reviews for i in r.get("issues", []) if i["severity"] == "High"),
            "medium": sum(1 for r in final_reviews for i in r.get("issues", []) if i["severity"] == "Medium"),
            "low": sum(1 for r in final_reviews for i in r.get("issues", []) if i["severity"] == "Low")
        }

        return {
            "session_id": session_id,
            "title": final_prd.title,
            "initial_version": 1,
            "final_version": final_prd.version,
            "iterations": len(history),
            "converged": history[-1]["converged"] if history else False,
            "convergence_reason": history[-1]["reason"] if history else "No iterations",
            "total_issues_identified": total_issues,
            "final_issue_count": final_issue_count,
            "timestamps": {
                "start": history[0]["reviews"][0]["timestamp"] if history and history[0].get("reviews") else None,
                "end": datetime.now().isoformat()
            },
            "history": history
        }
