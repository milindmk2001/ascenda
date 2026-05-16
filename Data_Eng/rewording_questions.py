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

INPUT_FILE = Path(ROOT) / "output" / "tagged_questions" / "tagged_questions.json"

OUTPUT_DIR = Path(ROOT) / "output" / "reworded_questions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_JSON = OUTPUT_DIR / "reworded_questions.json"
FAILED_JSON = OUTPUT_DIR / "rewording_failed.json"
REPORT_JSON = OUTPUT_DIR / "rewording_report.json"

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"


def extract_json(text):
    text = re.sub(r"```json|```", "", text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("No JSON found")
    return json.loads(match.group(0))


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
You are creating original learning content for an exam-prep platform.

Given a source question, produce:
1. A reworded version of the question
2. A concise step-by-step explanation
3. The final answer

Important rules:
- Do NOT copy the question verbatim
- Preserve the same concept, difficulty, and correct answer
- Keep options aligned with the original correct answer
- Do NOT hallucinate missing facts
- Explanation should be educational and concise
- Return ONLY valid JSON

Schema:
{{
  "question_reworded": "...",
  "options_reworded": {{
    "A": "...",
    "B": "...",
    "C": "...",
    "D": "..."
  }},
  "correct_answer": "...",
  "explanation": "...",
  "solution_steps": ["...", "..."],
  "formulae": ["..."]
}}

Original Question:
{q.get("question_raw", "")}

Options:
A: {q.get("options", {}).get("A", "")}
B: {q.get("options", {}).get("B", "")}
C: {q.get("options", {}).get("C", "")}
D: {q.get("options", {}).get("D", "")}

Correct Answer:
{q.get("correct_answer", "")}

Metadata:
Subject: {q.get("metadata", {}).get("subject", "")}
Unit: {q.get("metadata", {}).get("unit", "")}
Topic: {q.get("metadata", {}).get("topic", "")}
Sub-topic: {q.get("metadata", {}).get("sub_topic", "")}
Difficulty: {q.get("metadata", {}).get("difficulty", "")}
"""


def reword_question(q):
    prompt = build_prompt(q)
    response = safe_generate(prompt)
    result = extract_json(response)

    q["question_reworded"] = result.get("question_reworded", "")
    q["options_reworded"] = result.get("options_reworded", q.get("options", {}))
    q["correct_answer"] = result.get("correct_answer", q.get("correct_answer", ""))
    q["explanation"] = result.get("explanation", "")
    q["solution_steps"] = result.get("solution_steps", [])
    q["formulae"] = result.get("formulae", [])

    q["processing"]["reworded"] = True

    return q


def run():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    reworded = []
    failed = []

    for i, q in enumerate(questions, start=1):
        print(f"🔍 Rewording {i}/{len(questions)}")

        try:
            reworded_q = reword_question(q)
            reworded.append(reworded_q)

        except Exception as e:
            print(f"❌ Failed: {e}")
            q["rewording_error"] = str(e)
            failed.append(q)

        # checkpoint every 25
        if i % 25 == 0:
            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(reworded, f, indent=2)

            with open(FAILED_JSON, "w", encoding="utf-8") as f:
                json.dump(failed, f, indent=2)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(reworded, f, indent=2)

    with open(FAILED_JSON, "w", encoding="utf-8") as f:
        json.dump(failed, f, indent=2)

    report = {
        "input_questions": len(questions),
        "reworded_questions": len(reworded),
        "failed_questions": len(failed),
        "output": str(OUTPUT_JSON),
        "failed_output": str(FAILED_JSON)
    }

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("REWORDING COMPLETE")
    print("=" * 60)
    print(f"Input    : {len(questions)}")
    print(f"Reworded : {len(reworded)}")
    print(f"Failed   : {len(failed)}")
    print(f"Output   : {OUTPUT_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    run()