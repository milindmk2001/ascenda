import os
import json
import re
import hashlib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

INPUT_FILE = Path(ROOT) / "output" / "answer_audit" / "questions_answer_audited.json"

OUTPUT_DIR = Path(ROOT) / "output" / "cleaned_questions"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLEAN_JSON = OUTPUT_DIR / "clean_questions.json"
REMOVED_JSON = OUTPUT_DIR / "removed_questions.json"
REPORT_JSON = OUTPUT_DIR / "cleaning_report.json"


def clean_text(text):
    if not text:
        return ""

    text = str(text)

    text = re.sub(r"===== PAGE \d+ =====", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bSECTION\s*[-—]?\s*[IVXLC0-9]+\b.*?", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bPART\s*[IVXLC0-9]+\b.*?", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTOTAL MARKS\s*[:\-]?\s*\d+\b", " ", text, flags=re.IGNORECASE)

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def normalize_options(options):
    if not isinstance(options, dict):
        return {"A": "", "B": "", "C": "", "D": ""}

    return {
        "A": clean_text(options.get("A", "")),
        "B": clean_text(options.get("B", "")),
        "C": clean_text(options.get("C", "")),
        "D": clean_text(options.get("D", "")),
    }


def fingerprint(question, options):
    base = question.lower()
    base += " ".join(options.values()).lower()
    base = re.sub(r"[^a-z0-9]+", "", base)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def is_junk_question(q):
    question = q.get("question_raw", "")
    options = q.get("options", {})

    if len(question) < 20:
        return True, "too_short"

    bad_terms = [
        "this section contains",
        "total marks",
        "single correct answer type",
        "multiple correct",
        "integer answer type",
        "matrix-match",
        "darken the bubbles",
        "ors",
    ]

    q_lower = question.lower()
    if any(term in q_lower for term in bad_terms):
        return True, "instruction_text"

    non_empty_options = sum(1 for v in options.values() if v.strip())

    # Keep integer-answer questions only if answer exists
    answer_status = q.get("answer_audit", {}).get("status", "")
    if non_empty_options < 2 and answer_status not in {"VALID_NUMERIC"}:
        return True, "insufficient_options"

    return False, ""


def run():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    cleaned = []
    removed = []
    seen = set()

    stats = {
        "input_count": len(questions),
        "cleaned_count": 0,
        "removed_count": 0,
        "duplicate_count": 0,
        "removed_reasons": {}
    }

    for q in questions:
        q["question_raw"] = clean_text(q.get("question_raw", ""))
        q["options"] = normalize_options(q.get("options", {}))

        fp = fingerprint(q["question_raw"], q["options"])

        if fp in seen:
            q["removed_reason"] = "duplicate"
            removed.append(q)
            stats["duplicate_count"] += 1
            stats["removed_reasons"]["duplicate"] = stats["removed_reasons"].get("duplicate", 0) + 1
            continue

        is_junk, reason = is_junk_question(q)

        if is_junk:
            q["removed_reason"] = reason
            removed.append(q)
            stats["removed_reasons"][reason] = stats["removed_reasons"].get(reason, 0) + 1
            continue

        seen.add(fp)

        q["processing"]["cleaned"] = True
        q["cleaning"] = {
            "fingerprint": fp,
            "status": "cleaned"
        }

        cleaned.append(q)

    stats["cleaned_count"] = len(cleaned)
    stats["removed_count"] = len(removed)

    with open(CLEAN_JSON, "w", encoding="utf-8") as f:
        json.dump(cleaned, f, indent=2)

    with open(REMOVED_JSON, "w", encoding="utf-8") as f:
        json.dump(removed, f, indent=2)

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("\n" + "=" * 60)
    print("QUESTION CLEANING COMPLETE")
    print("=" * 60)
    print(f"Input questions  : {stats['input_count']}")
    print(f"Cleaned questions: {stats['cleaned_count']}")
    print(f"Removed questions: {stats['removed_count']}")
    print(f"Duplicates       : {stats['duplicate_count']}")
    print(f"Clean dataset    : {CLEAN_JSON}")
    print(f"Report           : {REPORT_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    run()