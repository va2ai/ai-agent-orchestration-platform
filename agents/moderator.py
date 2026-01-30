from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from models.prd_models import PRD, PRDReview
from prompts.system_prompts import MODERATOR_SYSTEM, get_refine_prompt
from typing import List, Optional, Tuple
import os

class Moderator:
    """PRD refinement agent"""

    def __init__(self, model: str = "gpt-4-turbo", temperature: float = 0.3):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.name = "moderator"

    def refine(self, prd: PRD, reviews: List[PRDReview], logger: Optional[object] = None) -> Tuple[str, dict]:
        """Refine PRD based on reviews, return refined content and metadata"""
        prompt = get_refine_prompt(prd, reviews)
        messages = [
            SystemMessage(content=MODERATOR_SYSTEM),
            HumanMessage(content=prompt)
        ]

        if logger:
            logger.log_llm_request(self.name, prompt)

        response = self.llm.invoke(messages)

        # Extract token usage
        token_usage = {}
        if hasattr(response, 'response_metadata'):
            token_usage = response.response_metadata.get('token_usage', {})

        refined_content = response.content.strip()

        if logger:
            logger.log_llm_response(self.name, refined_content, token_usage)
            logger.log_moderator_output(refined_content)

        return refined_content, token_usage
