import logging
import sys
from typing import Optional
from datetime import datetime
from pathlib import Path

class PRDLogger:
    """Enhanced logging for PRD refinement process"""

    def __init__(self, session_id: str, log_dir: str = "data/prds", verbose: bool = False):
        self.session_id = session_id
        self.verbose = verbose
        self.log_dir = Path(log_dir) / session_id
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Set up file logger
        self.file_logger = self._setup_file_logger()

    def _setup_file_logger(self) -> logging.Logger:
        """Set up file logger for detailed logs"""
        logger = logging.getLogger(f"prd_refinement_{self.session_id}")
        logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        logger.handlers = []

        # File handler for detailed logs
        log_file = self.log_dir / "refinement.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def info(self, message: str, console: bool = True):
        """Log info message"""
        self.file_logger.info(message)
        if console:
            print(message)

    def debug(self, message: str, console: bool = False):
        """Log debug message"""
        self.file_logger.debug(message)
        if console and self.verbose:
            print(f"[DEBUG] {message}")

    def warning(self, message: str, console: bool = True):
        """Log warning message"""
        self.file_logger.warning(message)
        if console:
            print(f"[WARNING] {message}")

    def error(self, message: str, console: bool = True):
        """Log error message"""
        self.file_logger.error(message)
        if console:
            print(f"[ERROR] {message}")

    def section(self, title: str, console: bool = True):
        """Log section header"""
        separator = "=" * 60
        self.file_logger.info(separator)
        self.file_logger.info(title)
        self.file_logger.info(separator)
        if console:
            print(f"\n{separator}")
            print(title)
            print(separator)

    def log_llm_request(self, agent: str, prompt_preview: str, max_length: int = 200):
        """Log LLM request"""
        preview = prompt_preview[:max_length] + "..." if len(prompt_preview) > max_length else prompt_preview
        self.file_logger.debug(f"[{agent}] Request prompt preview: {preview}")
        self.debug(f"[{agent}] Sending request to LLM...", console=True)

    def log_llm_response(self, agent: str, response: str, token_usage: Optional[dict] = None):
        """Log LLM response"""
        self.file_logger.debug(f"[{agent}] Response: {response}")

        if token_usage:
            prompt_tokens = token_usage.get('prompt_tokens', 0)
            completion_tokens = token_usage.get('completion_tokens', 0)
            total_tokens = token_usage.get('total_tokens', 0)

            self.file_logger.info(
                f"[{agent}] Token usage: {prompt_tokens} prompt + {completion_tokens} completion = {total_tokens} total"
            )

            if self.verbose:
                print(f"  [{agent}] Tokens: {total_tokens} ({prompt_tokens} in / {completion_tokens} out)")

    def log_review_summary(self, reviewer: str, issues_count: int, high_count: int, response_preview: str):
        """Log review summary with preview"""
        self.file_logger.info(f"[{reviewer}] Found {issues_count} issues ({high_count} high)")

        # Save full response to separate file
        response_file = self.log_dir / f"{reviewer}_responses.log"
        with open(response_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"{'='*60}\n")
            f.write(response_preview)
            f.write(f"\n\n")

        if self.verbose:
            preview = response_preview[:300] + "..." if len(response_preview) > 300 else response_preview
            print(f"\n  [{reviewer}] Overall Assessment Preview:")
            print(f"  {preview}\n")

    def log_issues(self, reviewer: str, issues: list):
        """Log detailed issues"""
        if not issues:
            return

        self.file_logger.info(f"[{reviewer}] Issues breakdown:")
        for i, issue in enumerate(issues, 1):
            severity = issue.get('severity', 'Unknown')
            description = issue.get('description', 'No description')
            fix = issue.get('suggested_fix', 'No fix suggested')

            self.file_logger.info(f"  Issue {i} [{severity}]: {description}")
            self.file_logger.info(f"    Fix: {fix}")

            if self.verbose:
                print(f"  Issue {i} [{severity}]: {description[:100]}...")

    def log_refinement(self, version: int, prev_length: int, new_length: int):
        """Log refinement details"""
        change_pct = ((new_length - prev_length) / prev_length * 100) if prev_length > 0 else 0

        self.file_logger.info(f"Refinement v{version-1} -> v{version}:")
        self.file_logger.info(f"  Content length: {prev_length} -> {new_length} chars ({change_pct:+.1f}%)")

        if self.verbose:
            print(f"  Refinement: {prev_length} -> {new_length} chars ({change_pct:+.1f}%)")

    def log_moderator_output(self, refined_content: str):
        """Log moderator's refined output"""
        self.file_logger.debug(f"Moderator refined content:\n{refined_content}")

        # Save to separate file
        moderator_file = self.log_dir / "moderator_outputs.log"
        with open(moderator_file, 'a', encoding='utf-8') as f:
            timestamp = datetime.now().isoformat()
            f.write(f"\n{'='*80}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"{'='*80}\n")
            f.write(refined_content)
            f.write(f"\n\n")

        if self.verbose:
            preview = refined_content[:500] + "..." if len(refined_content) > 500 else refined_content
            print(f"\n  [Moderator] Refined PRD Preview:")
            print(f"  {preview}\n")

    def log_convergence(self, converged: bool, reason: str, iteration: int):
        """Log convergence status"""
        status = "CONVERGED" if converged else "CONTINUING"
        self.file_logger.info(f"[Iteration {iteration}] {status}: {reason}")

        if self.verbose or converged:
            print(f"  Status: {reason}")

    def log_token_summary(self, total_tokens: dict):
        """Log final token usage summary"""
        self.section("Token Usage Summary", console=False)

        for agent, tokens in total_tokens.items():
            self.file_logger.info(f"{agent}: {tokens} tokens")

        total = sum(total_tokens.values())
        self.file_logger.info(f"TOTAL: {total} tokens")

        if self.verbose:
            print("\nToken Usage Summary:")
            for agent, tokens in total_tokens.items():
                print(f"  {agent}: {tokens:,} tokens")
            print(f"  TOTAL: {total:,} tokens")
