import os
import re
import json
from pathlib import Path
from dotenv import load_dotenv

# ----------------------------
# Load env
# ----------------------------
load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

if not ROOT:
    raise ValueError("PROJECT_ROOT not set in .env")

# ----------------------------
# Paths
# ----------------------------
RAW_TEXT_PATH = Path(ROOT) / "output" / "raw_text"
STRUCTURED_PATH = Path(ROOT) / "output" / "structured"
STRUCTURED_PATH.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Regex patterns
# ----------------------------
QUESTION_SPLIT_PATTERN = re.compile(r"\n\s*(?:Q\s*)?\d+[\.\)]", re.IGNORECASE)
OPTION_PATTERN = re.compile(r"\(?[A-D]\)")

# ----------------------------
# Clean helper
# ----------------------------
def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()

# ----------------------------
# Extract options
# ----------------------------
def extract_options(block):
    options = {"A": "", "B": "", "C": "", "D": ""}

    parts = re.split(r"\(?[A-D]\)", block)
    labels = ["A", "B", "C", "D"]

    for i in range(1, len(parts)):
        if i-1 < len(labels):
            options[labels[i-1]] = parts[i].strip()

    return options

# ----------------------------
# Structure detection
# ----------------------------
def detect_structure(text):
    text = clean_text(text)

    # Split by question markers
    questions = re.split(r"\n\s*(?:Q\s*)?\d+[\.\)]", text)

    structured_data = []

    q_id = 1

    for q_block in questions:
        q_block = q_block.strip()

        if len(q_block) < 10:
            continue

        # Split question vs options (heuristic)
        option_split = re.split(r"\(?[A-D]\)", q_block, maxsplit=1)

        question_text = option_split[0].strip()

        options_text = q_block[len(question_text):].strip()

        options = extract_options(options_text)

        structured_data.append({
            "question_id": q_id,
            "question": question_text,
            "options": options
        })

        q_id += 1

    return structured_data

# ----------------------------
# Process all files
# ----------------------------
def process_all():
    files = list(RAW_TEXT_PATH.glob("*.txt"))

    if not files:
        print("❌ No raw text files found")
        return

    print(f"📦 Found {len(files)} files")

    for file in files:
        print(f"🔍 Processing: {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            text = f.read()

        structured = detect_structure(text)

        output_file = STRUCTURED_PATH / f"{file.stem}_structured.json"

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured, f, indent=2)

        print(f"✅ Saved: {output_file}")

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    process_all()