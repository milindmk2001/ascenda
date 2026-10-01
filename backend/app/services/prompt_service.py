import json
import re
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field


class Persona(str, Enum):
    GEN_Z = "gen_z"
    SOCRATIC = "socratic"
    PROFESSOR_PRIYA = "professor_priya"


class PhysicsTopic(str, Enum):
    COULOMBS_LAW = "coulombs_law"
    SNELLS_LAW = "snells_law"
    LIGHT_REFRACTION = "light_refraction"


class VisualLessonOutputSchema(BaseModel):
    explanation: str
    animation_params: dict[str, Any]
    topic_title: str
    mode: str


class PromptService:
    PERSONA_PROMPTS = {
        Persona.GEN_Z: "Act as a Gen-Z Physics Tutor for Ascenda. Use punchy, engaging, teenager-friendly language with modern analogies.",
        Persona.SOCRATIC: "Act as a Socratic Physics Tutor for Ascenda. Guide the student by asking thought-provoking questions and encouraging step-by-step reasoning.",
        Persona.PROFESSOR_PRIYA: "Act as Professor Priya Sharma, a warm, encouraging, and highly articulate expert physics tutor for Ascenda.",
    }

    @classmethod
    def get_coulombs_law_prompt(
        cls, 
        scenario: str, 
        persona: Persona = Persona.GEN_Z
    ) -> str:
        r_val = 120 if scenario == "attraction" else 350
        q2_val = -1 if scenario == "attraction" else 1
        persona_instruction = cls.PERSONA_PROMPTS.get(persona, cls.PERSONA_PROMPTS[Persona.GEN_Z])

        return f"""
        {persona_instruction}
        
        Topic: Coulomb's Law - Scenario: {scenario.upper()}
        
        Return ONLY valid JSON matching this exact structure:
        {{
          "explanation": "Your explanation or script goes here",
          "animation_params": {{ "q1": 1, "q2": {q2_val}, "r": {r_val} }},
          "topic_title": "{scenario.capitalize()} Mode",
          "mode": "{scenario}"
        }}
        """

    @classmethod
    def get_snells_law_prompt(
        cls, 
        n1: float = 1.0, 
        n2: float = 1.5, 
        persona: Persona = Persona.PROFESSOR_PRIYA
    ) -> str:
        persona_instruction = cls.PERSONA_PROMPTS.get(persona, cls.PERSONA_PROMPTS[Persona.PROFESSOR_PRIYA])

        return f"""
        {persona_instruction}
        
        Topic: Refraction & Snell's Law (n1 = {n1}, n2 = {n2})
        
        Return ONLY valid JSON matching this exact structure:
        {{
          "explanation": "Detailed explanation of light bending across medium interface",
          "animation_params": {{ "n1": {n1}, "n2": {n2}, "theta1": 45.0 }},
          "topic_title": "Snell's Law & Refraction",
          "mode": "refraction"
        }}
        """

    @staticmethod
    def clean_ai_response(text: str) -> dict[str, Any]:
        """
        Strips markdown code fences, leading/trailing whitespace, and validates output against JSON parsing.
        """
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
        return json.loads(cleaned)

    @classmethod
    def parse_and_validate_response(cls, text: str) -> VisualLessonOutputSchema:
        """
        Cleans raw LLM response and validates it using Pydantic.
        """
        data = cls.clean_ai_response(text)
        return VisualLessonOutputSchema(**data)