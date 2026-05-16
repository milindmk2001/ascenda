import os
import json
from pathlib import Path
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

INPUT_FILE = Path(ROOT) / "output" / "reworded_questions" / "reworded_questions.json"

OUTPUT_DIR = Path(ROOT) / "output" / "final_dataset"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FINAL_JSON = OUTPUT_DIR / "final_dataset.json"
FINAL_TXT = OUTPUT_DIR / "final_dataset.txt"
REPORT_JSON = OUTPUT_DIR / "final_dataset_report.json"


def safe_get(d, *keys, default=""):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    return cur


def build_record(q):
    metadata = q.get("metadata", {})
    source = q.get("source", {})

    question_final = q.get("question_reworded") or q.get("question_raw", "")
    options_final = q.get("options_reworded") or q.get("options", {})

    return {
        "id": q.get("id", ""),

        "exam": {
            "type": metadata.get("exam", "JEE"),
            "year": source.get("year", ""),
            "paper": source.get("paper", ""),
            "source_file": source.get("file", "")
        },

        "classification": {
            "subject": metadata.get("subject", ""),
            "unit": metadata.get("unit", ""),
            "topic": metadata.get("topic", []),
            "sub_topic": metadata.get("sub_topic", []),
            "concepts": metadata.get("concepts", []),
            "difficulty": metadata.get("difficulty", ""),
            "difficulty_score": metadata.get("difficulty_score", None),
            "question_type": metadata.get("question_type", "")
        },

        "question": {
            "raw": q.get("question_raw", ""),
            "final": question_final
        },

        "options": options_final,

        "answer": {
            "correct_answer": q.get("correct_answer", "")
        },

        "solution": {
            "explanation": q.get("explanation", ""),
            "solution_steps": q.get("solution_steps", []),
            "formulae": q.get("formulae", [])
        },

        "processing": {
            "cleaned": safe_get(q, "processing", "cleaned", default=False),
            "tagged": safe_get(q, "processing", "tagged", default=False),
            "reworded": safe_get(q, "processing", "reworded", default=False)
        }
    }


def format_text_record(r):
    topic = r["classification"].get("topic", [])
    if isinstance(topic, list):
        topic = ", ".join(topic)

    options = r.get("options", {})

    return f"""
ID: {r['id']}
Exam: {r['exam']['type']} | Year: {r['exam']['year']} | Paper: {r['exam']['paper']}
Subject: {r['classification']['subject']}
Unit: {r['classification']['unit']}
Topic: {topic}
Difficulty: {r['classification']['difficulty']}

Question:
{r['question']['final']}

Options:
A) {options.get('A', '')}
B) {options.get('B', '')}
C) {options.get('C', '')}
D) {options.get('D', '')}

Correct Answer:
{r['answer']['correct_answer']}

Explanation:
{r['solution']['explanation']}

Source Question:
{r['question']['raw']}

------------------------------------------------------------
"""


def run():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    final_records = []
    subject_counter = Counter()
    year_counter = Counter()
    difficulty_counter = Counter()

    for q in questions:
        record = build_record(q)
        final_records.append(record)

        subject_counter[record["classification"]["subject"] or "UNKNOWN"] += 1
        year_counter[str(record["exam"]["year"] or "UNKNOWN")] += 1
        difficulty_counter[record["classification"]["difficulty"] or "UNKNOWN"] += 1

    with open(FINAL_JSON, "w", encoding="utf-8") as f:
        json.dump(final_records, f, indent=2)

    with open(FINAL_TXT, "w", encoding="utf-8") as f:
        for r in final_records:
            f.write(format_text_record(r))

    report = {
        "input_questions": len(questions),
        "final_questions": len(final_records),
        "by_subject": dict(subject_counter),
        "by_year": dict(year_counter),
        "by_difficulty": dict(difficulty_counter),
        "outputs": {
            "json": str(FINAL_JSON),
            "txt": str(FINAL_TXT)
        }
    }

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n" + "=" * 60)
    print("FINAL DATASET BUILD COMPLETE")
    print("=" * 60)
    print(f"Input questions : {len(questions)}")
    print(f"Final questions : {len(final_records)}")
    print(f"JSON output     : {FINAL_JSON}")
    print(f"Text output     : {FINAL_TXT}")
    print(f"Report          : {REPORT_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    run()