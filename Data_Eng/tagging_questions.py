import os
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv
from google import genai

load_dotenv()

ROOT = os.getenv("PROJECT_ROOT")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not ROOT:
    raise ValueError("PROJECT_ROOT not set")

if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not set")

INPUT_FILE = Path(ROOT) / "output" / "cleaned_questions" / "clean_questions.json"

OUTPUT_DIR = Path(ROOT) / "output" / "tagged_questions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TAGGED_JSON = OUTPUT_DIR / "tagged_questions.json"
REPORT_JSON = OUTPUT_DIR / "tagging_report.json"
FAILED_JSON = OUTPUT_DIR / "tagging_failed.json"

client = genai.Client(api_key=GEMINI_API_KEY)

MODEL = "gemini-2.5-flash"


def extract_json(text):
    text = re.sub(r"```json|```", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group(0))

    raise ValueError("No valid JSON found")


def safe_generate(prompt, retries=5, delay=5):
    for attempt in range(retries):
        try:
            time.sleep(1.5)

            response = client.models.generate_content(
                model=MODEL,
                contents=prompt
            )

            if not response.text:
                raise ValueError("Empty Gemini response")

            return response.text

        except Exception as e:
            msg = str(e)

            if any(x in msg for x in ["503", "429", "UNAVAILABLE"]):
                wait = delay * (attempt + 1)
                print(f"⏳ Retry {attempt + 1}/{retries} after {wait}s")
                time.sleep(wait)
            else:
                raise e

    raise RuntimeError("Gemini failed after retries")


def build_prompt(q):
    return f"""
You are an expert JEE/NEET/KCET exam content classifier.

Classify the following question.

Return ONLY valid JSON in this exact schema:

{{
  "subject": "Physics/Chemistry/Mathematics/Biology",
  "unit": "...",
  "topics": ["..."],
  "sub_topics": ["..."],
  "concepts": ["..."],
  "difficulty": "Easy/Medium/Hard",
  "difficulty_score": 0.0,
  "question_type": "MCQ/MultiCorrect/Numeric/MatrixMatch/Unknown",
  "exam_relevance": "JEE/NEET/KCET/General"
}}

Rules:
- topics must be an array
- concepts must be specific
- difficulty_score must be between 0 and 1
- do not explain

Question:
{q.get("question_raw", "")}

Options:
A: {q.get("options", {}).get("A", "")}
B: {q.get("options", {}).get("B", "")}
C: {q.get("options", {}).get("C", "")}
D: {q.get("options", {}).get("D", "")}

Correct Answer:
{q.get("correct_answer", "")}
"""


def tag_question(q):
    prompt = build_prompt(q)
    response = safe_generate(prompt)
    tags = extract_json(response)

    q["metadata"]["subject"] = tags.get("subject", "")
    q["metadata"]["unit"] = tags.get("unit", "")
    q["metadata"]["topic"] = tags.get("topics", [])
    q["metadata"]["sub_topic"] = tags.get("sub_topics", [])
    q["metadata"]["concepts"] = tags.get("concepts", [])
    q["metadata"]["difficulty"] = tags.get("difficulty", "")
    q["metadata"]["difficulty_score"] = tags.get("difficulty_score", None)
    q["metadata"]["question_type"] = tags.get("question_type", "")
    q["metadata"]["exam_relevance"] = tags.get("exam_relevance", "")

    q["processing"]["tagged"] = True

    return q


def run():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    tagged = []
    failed = []

    for i, q in enumerate(questions, start=1):
        print(f"🔍 Tagging {i}/{len(questions)}")

        try:
            tagged_q = tag_question(q)
            tagged.append(tagged_q)

        except Exception as e:
            print(f"❌ Failed: {e}")
            q["tagging_error"] = str(e)
            failed.append(q)

    with open(TAGGED_JSON, "w", encoding="utf-8") as f:
        json.dump(tagged, f, indent=2)

    with open(FAILED_JSON, "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2)

    report = {
        "input_questions": len(questions),
        "tagged_questions": len(tagged),
        "failed_questions": len(failed),
        "tagged_output": str(TAGGED_JSON),
        "failed_output": str(FAILED_JSON)
    }

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("TAGGING COMPLETE")
    print("=" * 60)
    print(f"Input  : {len(questions)}")
    print(f"Tagged : {len(tagged)}")
    print(f"Failed : {len(failed)}")
    print(f"Output : {TAGGED_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    run()