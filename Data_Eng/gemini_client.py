from google import genai
import os
import json
import time
import re
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not set in .env")

client = genai.Client(api_key=API_KEY)

MODEL = "gemini-2.5-flash"


def safe_generate(prompt, retries=5, delay=5):
    for attempt in range(retries):
        try:
            time.sleep(2)

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            return response.text

        except Exception as e:
            msg = str(e)

            if any(x in msg for x in ["503", "429", "UNAVAILABLE"]):
                print(f"⏳ Retry {attempt + 1}/{retries} → {msg}")
                time.sleep(delay * (attempt + 1))
            else:
                raise e

    raise Exception("❌ Gemini failed after retries")


def extract_json(text):
    try:
        text = re.sub(r"```json|```", "", text)

        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            parsed = json.loads(match.group(0))
            return [parsed] if isinstance(parsed, dict) else parsed

    except Exception:
        pass

    return []


def is_valid_output(data):
    if not isinstance(data, list) or len(data) == 0:
        return False

    sample = data[0]
    return isinstance(sample, dict) and "question" in sample and "options" in sample


def repair_warning(data):
    prompt = f"""
You are an expert exam data cleaner.

Fix this structured exam question JSON.

Rules:
- Correct OCR errors
- Remove page headers and section instructions
- Ensure each question has:
  - question
  - options as A, B, C, D
  - correct_answer if available
- Do NOT invent new questions
- Do NOT add explanations
- Return ONLY valid JSON array

INPUT:
{json.dumps(data)}
"""

    response_text = safe_generate(prompt)
    cleaned = extract_json(response_text)

    if not is_valid_output(cleaned):
        print("⚠️ WARNING fallback used")
        return data

    return cleaned


def repair_bad(raw_text):
    prompt = f"""
You are an expert at extracting MCQ questions from messy OCR text.

Extract ONLY clean multiple-choice questions.

Ignore:
- Page headers
- Section instructions
- Answer-only text
- Integer-answer questions
- Matrix-match questions
- Repeated answer-key text

Return JSON only in this exact format:

[
  {{
    "question_number": "1",
    "question": "...",
    "options": {{
      "A": "...",
      "B": "...",
      "C": "...",
      "D": "..."
    }},
    "correct_answer": ""
  }}
]

Rules:
- Only include questions that have a proper question and 4 options
- If correct answer is visible, populate correct_answer
- If correct answer is not visible, keep correct_answer as empty string
- Do not return markdown
- Do not return explanations

TEXT:
{raw_text[:12000]}
"""

    response_text = safe_generate(prompt)
    rebuilt = extract_json(response_text)

    if not is_valid_output(rebuilt):
        print("⚠️ BAD repair fallback → second pass")
        return repair_bad_second_pass(raw_text)

    return rebuilt


def repair_bad_second_pass(raw_text):
    prompt = f"""
Previous extraction failed.

Relaxed extraction mode:
- Extract any usable MCQ-like questions
- Use only items with visible options A, B, C, D
- Ignore answer-only pages and garbage text
- Return JSON array only

Format:
[
  {{
    "question_number": "",
    "question": "",
    "options": {{
      "A": "",
      "B": "",
      "C": "",
      "D": ""
    }},
    "correct_answer": ""
  }}
]

TEXT:
{raw_text[:12000]}
"""

    response_text = safe_generate(prompt)
    rebuilt = extract_json(response_text)

    if not is_valid_output(rebuilt):
        return []

    return rebuilt