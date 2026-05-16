import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

INPUT_FILE = Path(ROOT) / "output" / "questions_extracted" / "questions_master.json"

OUTPUT_DIR = Path(ROOT) / "output" / "answer_audit"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

AUDITED_JSON = OUTPUT_DIR / "questions_answer_audited.json"
REPORT_JSON = OUTPUT_DIR / "answer_audit_report.json"
MISSING_JSON = OUTPUT_DIR / "questions_missing_answers.json"
INVALID_JSON = OUTPUT_DIR / "questions_invalid_answers.json"


VALID_SINGLE = {"A", "B", "C", "D"}
VALID_SPECIAL = {"MARKS TO ALL", "BONUS", "ALL", ""}


def normalize_answer(ans):
    if ans is None:
        return ""

    ans = str(ans).strip().upper()
    ans = ans.replace("ANSWER:", "").replace("ANSWER", "").strip()
    ans = ans.replace("OPTION", "").strip()
    ans = re.sub(r"[^A-D0-9,\s]+", "", ans).strip()

    # Convert "A B D" or "ABD" to "A,B,D"
    if re.fullmatch(r"[A-D]{2,4}", ans):
        return ",".join(list(ans))

    if re.fullmatch(r"[A-D](\s+[A-D])+", ans):
        return ",".join(ans.split())

    return ans


def classify_answer(ans):
    ans = normalize_answer(ans)

    if ans == "":
        return "MISSING"

    if ans in VALID_SINGLE:
        return "VALID_SINGLE"

    if re.fullmatch(r"[A-D](,[A-D])+", ans):
        return "VALID_MULTI"

    if re.fullmatch(r"[0-9]+", ans):
        return "VALID_NUMERIC"

    if ans in VALID_SPECIAL:
        return "VALID_SPECIAL"

    return "INVALID"


def run():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_FILE}")

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        questions = json.load(f)

    audited = []
    missing = []
    invalid = []
    status_counter = Counter()
    year_counter = Counter()

    for q in questions:
        ans_raw = q.get("correct_answer", "")
        ans_norm = normalize_answer(ans_raw)
        status = classify_answer(ans_raw)

        q["correct_answer"] = ans_norm
        q["answer_audit"] = {
            "status": status,
            "has_answer": status != "MISSING",
            "is_valid": status.startswith("VALID")
        }

        audited.append(q)
        status_counter[status] += 1

        year = q.get("source", {}).get("year", "UNKNOWN")
        year_counter[str(year)] += 1

        if status == "MISSING":
            missing.append(q)

        if status == "INVALID":
            invalid.append(q)

    report = {
        "total_questions": len(questions),
        "answer_status_counts": dict(status_counter),
        "questions_missing_answers": len(missing),
        "questions_invalid_answers": len(invalid),
        "questions_by_year": dict(year_counter),
        "output_files": {
            "audited_json": str(AUDITED_JSON),
            "missing_answers": str(MISSING_JSON),
            "invalid_answers": str(INVALID_JSON)
        }
    }

    with open(AUDITED_JSON, "w", encoding="utf-8") as f:
        json.dump(audited, f, indent=2)

    with open(REPORT_JSON, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    with open(MISSING_JSON, "w", encoding="utf-8") as f:
        json.dump(missing, f, indent=2)

    with open(INVALID_JSON, "w", encoding="utf-8") as f:
        json.dump(invalid, f, indent=2)

    print("\n" + "=" * 60)
    print("ANSWER AUDIT COMPLETE")
    print("=" * 60)
    print(f"Total questions        : {len(questions)}")
    print(f"Missing answers        : {len(missing)}")
    print(f"Invalid answers        : {len(invalid)}")
    print(f"Audited dataset        : {AUDITED_JSON}")
    print(f"Report                 : {REPORT_JSON}")
    print("=" * 60)


if __name__ == "__main__":
    run()