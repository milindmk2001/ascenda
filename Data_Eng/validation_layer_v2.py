import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

STRUCTURED_PATH = Path(ROOT) / "output" / "structured"
VALIDATED_PATH = Path(ROOT) / "output" / "validated"
REPORT_PATH = Path(ROOT) / "output" / "quality_reports"

VALIDATED_PATH.mkdir(parents=True, exist_ok=True)
REPORT_PATH.mkdir(parents=True, exist_ok=True)


def question_score(q):
    score = 1.0

    question = q.get("question", "")
    options = q.get("options", {})

    if not isinstance(options, dict):
        score -= 0.4
        options = {}

    # Question length
    if len(question.strip()) < 30:
        score -= 0.3

    # Header / instruction pollution
    bad_markers = [
        "===== PAGE",
        "SECTION",
        "TOTAL MARKS",
        "PART",
        "SINGLE CORRECT",
        "MULTIPLE CORRECT",
        "INTEGER ANSWER",
        "MATRIX-MATCH"
    ]

    if any(marker.lower() in question.lower() for marker in bad_markers):
        score -= 0.35

    # Answer pollution inside question
    if "answer" in question.lower():
        score -= 0.25

    # Missing options
    required = ["A", "B", "C", "D"]
    missing = sum(1 for k in required if not options.get(k, "").strip())
    score -= missing * 0.15

    # Very short options
    short_opts = sum(
        1 for k in required
        if options.get(k, "").strip() and len(options.get(k, "").strip()) < 3
    )
    score -= short_opts * 0.08

    # OCR noise
    noise = sum(
        1 for c in question
        if not c.isalnum() and c not in " .?(),:-+=/%[]{}<>^_"
    )
    if noise > 20:
        score -= 0.2

    return max(0.0, min(1.0, score))


def file_score(questions):
    if not isinstance(questions, list) or not questions:
        return 0.0

    scores = [question_score(q) for q in questions if isinstance(q, dict)]

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def calculate_score(data):
    return file_score(data)


def process_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scored_questions = []

    for q in data:
        score = question_score(q)

        q["validation"] = {
            "confidence": score,
            "is_valid": score >= 0.65
        }

        scored_questions.append(q)

    f_score = file_score(scored_questions)

    return scored_questions, f_score


def run():
    files = list(STRUCTURED_PATH.glob("*structured.json"))

    report = []

    for file in files:
        print(f"🔍 Processing: {file.name}")

        questions, f_score = process_file(file)

        out_file = VALIDATED_PATH / file.name.replace("structured", "validated")

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=2)

        if f_score >= 0.85:
            status = "GOOD"
        elif f_score >= 0.65:
            status = "WARNING"
        else:
            status = "BAD"

        report.append({
            "file": file.name,
            "score": round(f_score, 3),
            "status": status
        })

        print(f"📊 File score: {f_score:.2f} → {status}")

    report_file = REPORT_PATH / "quality_report.json"

    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n📁 Quality report saved: {report_file}")


if __name__ == "__main__":
    run()