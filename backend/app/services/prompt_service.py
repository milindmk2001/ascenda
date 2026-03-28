import json

class PromptService:
    @staticmethod
    def get_coulombs_law_prompt(scenario: str):
        r_val = 120 if scenario == "attraction" else 350
        q2_val = -1 if scenario == "attraction" else 1

        return f"""
        Act as a Gen-Z Physics Tutor for Ascenda. Explain {scenario.upper()} in Coulomb's Law.
        Return ONLY JSON:
        {{
          "explanation": "Your punchy teenage-friendly script here",
          "animation_params": {{ "q1": 1, "q2": {q2_val}, "r": {r_val} }},
          "topic_title": "{scenario.capitalize()} Vibes",
          "mode": "{scenario}"
        }}
        """

    @staticmethod
    def clean_ai_response(text: str):
        return json.loads(text.replace("```json", "").replace("```", "").strip())