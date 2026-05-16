import os
import json
import re
import uuid
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------
# Load ENV
# -----------------------------
load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

FINAL_DIR = Path(ROOT) / "output" / "final"
WARNING_DIR = Path(ROOT) / "output" / "warning_repaired"
BAD_DIR = Path(ROOT) / "output" / "bad_repaired"

OUTPUT_DIR = Path(ROOT) / "output" / "questions_extracted"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MASTER_JSON = OUTPUT_DIR / "questions_master.json"

# -----------------------------
# Collect source files
# -----------------------------
SOURCE_DIRS = [
    FINAL_DIR,
    WARNING_DIR,
    BAD_DIR
]

# -----------------------------
# Helpers
# -----------------------------
def clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", str(text))
    text = text.replace("\n", " ")
    text = text.strip()

    return text


def extract_year(filename):
    match = re.search(r"(20\d{2}|19\d{2})", filename)
    return int(match.group(1)) if match else None


def extract_paper(filename):
    if "_1" in filename:
        return 1
    elif "_2" in filename:
        return 2
    return None


def normalize_options(options):
    clean = {}

    for key in ["A", "B", "C", "D"]:
        clean[key] = clean_text(options.get(key, ""))

    return clean


def build_question_record(q, source_file, idx):

    question = clean_text(q.get("question", ""))

    options = normalize_options(q.get("options", {}))

    answer = (
        q.get("correct_answer")
        or q.get("answer")
        or ""
    )

    record = {
        "id": str(uuid.uuid4()),

        "source": {
            "file": source_file,
            "year": extract_year(source_file),
            "paper": extract_paper(source_file)
        },

        "question_number": q.get(
            "question_number",
            q.get("question_id", idx)
        ),

        "question_raw": question,

        "options": options,

        "correct_answer": clean_text(answer),

        "metadata": {
            "subject": "",
            "topic": "",
            "difficulty": "",
            "exam": "JEE"
        },

        "processing": {
            "cleaned": False,
            "tagged": False,
            "reworded": False
        }
    }

    return record


# -----------------------------
# Validation
# -----------------------------
def is_valid_question(record):

    q = record["question_raw"]

    if len(q) < 20:
        return False

    opts = record["options"]

    non_empty = sum(
        1 for v in opts.values()
        if len(v.strip()) > 0
    )

    if non_empty < 2:
        return False

    return True


# -----------------------------
# Main extraction
# -----------------------------
def run():

    master_questions = []

    total_files = 0
    total_questions = 0

    for folder in SOURCE_DIRS:

        if not folder.exists():
            continue

        files = list(folder.glob("*.json"))

        for file in files:

            total_files += 1

            print(f"🔍 Processing: {file.name}")

            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if not isinstance(data, list):
                    continue

                valid_count = 0

                for idx, q in enumerate(data, start=1):

                    if not isinstance(q, dict):
                        continue

                    record = build_question_record(
                        q=q,
                        source_file=file.name,
                        idx=idx
                    )

                    if is_valid_question(record):

                        master_questions.append(record)
                        valid_count += 1

                total_questions += valid_count

                print(f"✅ Extracted: {valid_count}")

            except Exception as e:
                print(f"❌ Failed: {e}")

    # -------------------------
    # Save master dataset
    # -------------------------
    with open(MASTER_JSON, "w", encoding="utf-8") as f:
        json.dump(master_questions, f, indent=2)

    # -------------------------
    # Summary
    # -------------------------
    print("\n" + "=" * 60)
    print("QUESTION EXTRACTION COMPLETE")
    print("=" * 60)
    print(f"Files processed : {total_files}")
    print(f"Questions saved : {total_questions}")
    print(f"Master dataset  : {MASTER_JSON}")
    print("=" * 60)


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    run()