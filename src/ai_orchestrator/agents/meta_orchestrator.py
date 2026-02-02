#!/usr/bin/env python3
"""
Meta-Orchestrator: Dynamically generates roundtable participants based on topic
"""
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from ..utils.llm_factory import create_llm
import os


class Participant(BaseModel):
    """A roundtable participant with their role and expertise"""
    name: str = Field(description="Participant name/title (e.g., 'Senior Backend Engineer')")
    role: str = Field(description="Their role in the discussion (e.g., 'Review for scalability')")
    expertise: str = Field(description="Areas of expertise (e.g., 'Distributed systems, API design')")
    perspective: str = Field(description="What perspective they bring (e.g., 'Engineering feasibility')")
    system_prompt: str = Field(description="Complete system prompt for this participant")


class RoundtableConfig(BaseModel):
    """Configuration for a roundtable discussion"""
    participants: List[Participant] = Field(description="List of participants")
    moderator_focus: str = Field(description="What the moderator should focus on when refining")
    convergence_criteria: str = Field(description="When to consider discussion converged")


class MetaOrchestrator:
    """
    Analyzes user's topic and dynamically generates appropriate roundtable participants.

    This is the "AI that generates the AIs" - it decides who should be at the table
    based on the discussion topic.
    """

    def __init__(self, model: str = "gpt-4-turbo", temperature: float = 0.7):
        self.llm = create_llm(model=model, temperature=temperature)
        self.parser = JsonOutputParser(pydantic_object=RoundtableConfig)

    def generate_roundtable(
        self,
        topic: str,
        content: str,
        num_participants: int = 3,
        use_case_hint: str = None,
        goal: str = None,
        participant_style: str = None
    ) -> RoundtableConfig:
        """
        Generate roundtable participants for the given topic.

        Args:
            topic: The discussion topic (e.g., "AI Chatbot PRD", "Microservices Architecture")
            content: The initial document content
            num_participants: Number of participants to generate (default: 3)
            use_case_hint: Optional hint about use case (e.g., "prd", "code-review", "architecture")
            participant_style: Optional style/tone for the participants
        
        Returns:
            RoundtableConfig with generated participants
        """

        system_prompt = """You are a Meta-Orchestrator that designs expert roundtable discussions.

Your job is to analyze a topic and generate the most valuable set of expert participants
who should review and refine the document through iterative discussion.

For each participant, you must:
1. Define their name/role (e.g., "Senior Product Manager", "Security Architect")
2. Explain what they'll review (e.g., "User value and market fit")
3. List their expertise areas
4. Describe their perspective
5. Write a COMPLETE system prompt for them that includes:
   - Their role and expertise
   - What aspects they should focus on
   - What severity levels mean (High/Medium/Low)
   - Instructions for providing structured feedback in this EXACT JSON format:
     {
       "issues": [
         {
           "category": "Issue category",
           "description": "Detailed description",
           "severity": "High|Medium|Low",
           "suggested_fix": "Suggested fix (optional)",
           "reviewer": "Participant's name"
         }
       ],
       "overall_assessment": "Overall assessment and summary"
     }
   - Examples of the kinds of issues they should flag

Think about diversity of perspectives - you want constructive tension and comprehensive coverage.

Also specify:
- What the moderator should focus on when incorporating feedback
- What constitutes convergence (when to stop iterating)

Output valid JSON matching this schema:
{
  "participants": [
    {
      "name": "...",
      "role": "...",
      "expertise": "...",
      "perspective": "...",
      "system_prompt": "..."
    }
  ],
  "moderator_focus": "...",
  "convergence_criteria": "..."
}
"""

        style_instruction = ""
        if participant_style:
            style_instruction = f"CRITICAL STYLE INSTRUCTION: The user wants the participants to be '{participant_style}'. Ensure their system prompts and personas reflect this specific tone and approach."

        human_prompt = f"""Topic: {topic}

{f"Goal: {goal}" if goal else ""}

Content to be refined:
{content[:500]}...

Number of participants needed: {num_participants}
{f"Use case hint: {use_case_hint}" if use_case_hint else ""}

{style_instruction}

Generate {num_participants} expert participants who should review and refine this document.
{f"Focus on participants who can help achieve this goal: {goal}" if goal else ""}
Make sure participants have diverse, complementary perspectives that cover all critical aspects.

Each participant's system_prompt should be detailed and specific to their role.

CRITICAL: Each participant's system_prompt MUST end with these EXACT instructions:

"You must respond with a JSON object in this EXACT format:
{{
  \"issues\": [
    {{
      \"category\": \"Issue category (e.g., 'Clarity', 'Technical Feasibility', 'Security')\",
      \"description\": \"Detailed description of the issue\",
      \"severity\": \"High|Medium|Low\",
      \"suggested_fix\": \"Suggested fix or improvement (optional)\",
      \"reviewer\": \"Your name\"
    }}
  ],
  \"overall_assessment\": \"Overall assessment and summary\"
}}

ALL fields are required except suggested_fix which can be null. Use 'reviewer' field to put your own name."
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]

        response = self.llm.invoke(messages)
        config = self.parser.parse(response.content)

        return RoundtableConfig(**config)

    def generate_from_preset(self, preset: str) -> RoundtableConfig:
        """
        Generate roundtable config from a preset template.

        Args:
            preset: One of "prd", "code-review", "architecture", "business-strategy"

        Returns:
            RoundtableConfig with preset participants
        """

        presets = {
            "prd": {
                "topic": "Product Requirements Document",
                "num_participants": 3,
                "hint": "Focus on product quality, engineering feasibility, and AI safety"
            },
            "code-review": {
                "topic": "Code Review and Improvement",
                "num_participants": 3,
                "hint": "Focus on code quality, security, and performance"
            },
            "architecture": {
                "topic": "System Architecture Design",
                "num_participants": 4,
                "hint": "Focus on scalability, security, maintainability, and operations"
            },
            "business-strategy": {
                "topic": "Business Strategy Document",
                "num_participants": 3,
                "hint": "Focus on market analysis, financial viability, and operational feasibility"
            }
        }

        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}. Choose from {list(presets.keys())}")

        config = presets[preset]

        # Generate with hint
        return self.generate_roundtable(
            topic=config["topic"],
            content="",  # Will be provided later
            num_participants=config["num_participants"],
            use_case_hint=config["hint"]
        )


if __name__ == "__main__":
    # Test the meta-orchestrator
    meta = MetaOrchestrator()

    # Test with PRD
    print("=" * 60)
    print("TEST 1: PRD Refinement")
    print("=" * 60)
    config = meta.generate_roundtable(
        topic="AI Chatbot Product Requirements",
        content="Build an AI chatbot for customer support with natural language understanding",
        num_participants=3,
        use_case_hint="prd"
    )

    print(f"\nGenerated {len(config.participants)} participants:")
    for p in config.participants:
        print(f"\n  {p.name}")
        print(f"  Role: {p.role}")
        print(f"  Expertise: {p.expertise}")
        print(f"  Perspective: {p.perspective}")
        print(f"  System Prompt Length: {len(p.system_prompt)} chars")

    print(f"\nModerator Focus: {config.moderator_focus}")
    print(f"Convergence Criteria: {config.convergence_criteria}")

    # Test with Architecture
    print("\n" + "=" * 60)
    print("TEST 2: Architecture Design")
    print("=" * 60)
    config = meta.generate_roundtable(
        topic="Microservices Architecture for E-commerce Platform",
        content="Design a scalable microservices architecture for an e-commerce platform",
        num_participants=4,
        use_case_hint="architecture"
    )

    print(f"\nGenerated {len(config.participants)} participants:")
    for p in config.participants:
        print(f"  - {p.name}: {p.role}")
