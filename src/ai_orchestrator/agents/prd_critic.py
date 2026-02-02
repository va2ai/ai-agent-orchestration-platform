from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from ..models.prd_models import PRD, PRDReview
from ..prompts.system_prompts import PRD_CRITIC_SYSTEM, get_review_prompt
from typing import Optional, Tuple
import os

class PRDCritic:
    """Product quality critic agent"""

    def __init__(self, model: str = "gpt-4-turbo", temperature: float = 0.2):
        self.llm = ChatOpenAI(
            model=model,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.parser = JsonOutputParser(pydantic_object=PRDReview)
        self.name = "prd_critic"

    def review(self, prd: PRD, logger: Optional[object] = None) -> Tuple[PRDReview, dict]:
        """Review PRD and return structured issues with metadata"""
        messages = [
            SystemMessage(content=PRD_CRITIC_SYSTEM),
            HumanMessage(content=get_review_prompt(prd))
        ]

        if logger:
            logger.log_llm_request(self.name, get_review_prompt(prd))

        response = self.llm.invoke(messages)

        # Extract token usage
        token_usage = {}
        if hasattr(response, 'response_metadata'):
            token_usage = response.response_metadata.get('token_usage', {})

        if logger:
            logger.log_llm_response(self.name, response.content, token_usage)

        review_data = self.parser.parse(response.content)
        review = PRDReview(**review_data)

        if logger:
            high_count = sum(1 for i in review.issues if i.severity == "High")
            logger.log_review_summary(self.name, len(review.issues), high_count, review.overall_assessment)
            logger.log_issues(self.name, [i.model_dump() for i in review.issues])

        return review, token_usage
