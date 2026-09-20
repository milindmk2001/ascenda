"""
debug_gemini.py
Tests Gemini JSON generation for one node and saves the raw response.
Run this to see exactly what Gemini returns.
"""
import os
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

GEMINI_KEY = os.environ["GEMINI_API_KEY"]
GEN_MODEL  = "gemini-2.5-flash"
client     = genai.Client(api_key=GEMINI_KEY)

PROMPT_STRUCTURE = """You generate educational JSON for Grade 6 Maths in India.

CRITICAL RULES:
1. Return ONLY a valid JSON object
2. No apostrophes anywhere - use "do not" not "don't"
3. No single quotes anywhere
4. No trailing commas
5. No comments
6. All strings must be short - max 100 characters each
7. narration fields: max 80 characters, no apostrophes

Return exactly this JSON (fill in the REPLACE fields):
{"schemaVersion":"1.0","lessonId":"REPLACE","initialScene":"s1","metadata":{"subject":"Mathematics","grade":6,"book":"Ganita Prakash","chapter":"REPLACE","topic":"REPLACE","concept":"REPLACE"},"learningObjectives":["REPLACE","REPLACE","REPLACE"],"prerequisites":{"curriculumNodes":[],"conceptsRequired":["REPLACE","REPLACE"],"enforcementMode":"warn"},"assessmentPolicy":{"mode":"formative","passMark":0.7,"scoreMethod":"correct_answers_ratio","requireAllSlides":true,"allowRetry":true,"maxRetries":3},"masteryCriteria":{"minimumScore":0.7,"minimumSlidesViewed":3,"requiredInteractions":["answered_question"],"awardBadge":false,"unlocks":[]},"interactionPolicy":{"onCorrect":"reveal_answer","onWrong":"show_hint","onStudentQuestion":"call_tutor_router","onSlideComplete":"follow_transition","onLessonComplete":"show_summary","allowSkip":false,"allowReplay":true,"maxHintsPerSlide":2},"slides":[{"slideId":"s1","slideIndex":0,"sceneType":"animated_explanation","title":"REPLACE","learningObjective":"REPLACE","narration":"REPLACE max 80 chars no apostrophes","visualSpec":{"visualType":"number_sequence","sequence":[1,2,3,4,5],"rule":"REPLACE","ruleType":"additive","showQuestionMark":false},"animationTimeline":[{"action":"fadeIn","target":"term_0","duration":400},{"action":"drawArrow","target":"arrow_0","duration":300},{"action":"reveal","target":"term_1","duration":400},{"action":"highlight","target":"rule_label","duration":600}],"transitions":{"animation_complete":"s1_question","student_question":"tutor_router","replay_requested":"s1"}},{"slideId":"s1_question","slideIndex":1,"sceneType":"student_response","question":"REPLACE","answer":"REPLACE","hint":"REPLACE","misconception":"REPLACE","visualSpec":{"visualType":"number_sequence","sequence":[1,2,3,4,5],"rule":"REPLACE","ruleType":"additive","showQuestionMark":true},"transitions":{"student_correct":"lesson_end","student_wrong":"s1_hint","student_question":"tutor_router","max_attempts":"lesson_end"}},{"slideId":"s1_hint","slideIndex":2,"sceneType":"hint_delivery","narration":"REPLACE max 80 chars","transitions":{"animation_complete":"s1_question","student_question":"tutor_router"}},{"slideId":"lesson_end","slideIndex":3,"sceneType":"lesson_summary","narration":"REPLACE max 80 chars","transitions":{}}]}

No text before or after the JSON.
"""

user_prompt = """Generate lesson for:
Chapter 1: Patterns in Mathematics
Content type: common_mistakes
Topic: common errors students make with number patterns
Keep all string values short. No apostrophes."""

print("Calling Gemini...")
response = client.models.generate_content(
    model    = GEN_MODEL,
    contents = user_prompt,
    config   = types.GenerateContentConfig(
        system_instruction = PROMPT_STRUCTURE,
        response_mime_type = "application/json",
        temperature        = 0.1,
        max_output_tokens  = 4000,
    )
)

raw = response.text
print(f"\nTotal length: {len(raw)} chars")
print(f"\n--- FULL RAW RESPONSE ---")
print(raw)
print(f"--- END RAW RESPONSE ---")

# Save to file
with open("debug_raw_full.txt", "w", encoding="utf-8") as f:
    f.write(raw)
print(f"\nSaved to debug_raw_full.txt")

# Try parse
raw_clean = raw.strip()
if raw_clean.startswith("```"):
    lines = raw_clean.split("\n")
    lines = [l for l in lines if not l.startswith("```")]
    raw_clean = "\n".join(lines).strip()

start = raw_clean.find("{")
end   = raw_clean.rfind("}") + 1
if start >= 0 and end > start:
    raw_clean = raw_clean[start:end]

raw_clean = raw_clean.replace("\u2019", "").replace("\u2018", "")
raw_clean = re.sub(r",\s*([}\]])", r"\1", raw_clean)

try:
    result = json.loads(raw_clean)
    print(f"\n✅ JSON parsed OK - {len(result.get('slides', []))} slides")
except json.JSONDecodeError as e:
    print(f"\n❌ JSON parse failed: {e}")
    print(f"Error at char {e.pos}: {repr(raw_clean[max(0,e.pos-50):e.pos+50])}")
