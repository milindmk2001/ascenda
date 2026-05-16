import json
from pathlib import Path
import os
from dotenv import load_dotenv

# ----------------------------
# Load env
# ----------------------------
load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

STRUCTURED_PATH = Path(ROOT) / "output" / "structured"
VALIDATED_PATH = Path(ROOT) / "output" / "validated"
VALIDATED_PATH.mkdir(parents=True, exist_ok=True)

# ----------------------------
# Validation rules
# ----------------------------
def compute_confidence(q):
    score = 1.0

    question = q.get("question", "")
    options = q.get("options", {})

    # Rule 1: question length
    if len(question) < 20:
        score -= 0.3

    # Rule 2: missing options
    missing = [k for k, v in options.items() if not v.strip()]
    score -= 0.15 * len(missing)

    # Rule 3: OCR noise detection
    noise_chars = sum(not c.isalnum() and c not in " .?(),:-" for c in question)
    if noise_chars > 10:
        score -= 0.2

    # Rule 4: too short options
    short_opts = sum(len(v) < 5 for v in options.values() if v)
    score -= 0.1 * short_opts

    # Clamp between 0 and 1
    return max(0.0, min(1.0, score))


def validate_question(q):
    confidence = compute_confidence(q)

    q["validation"] = {
        "confidence": confidence,
        "is_valid": confidence >= 0.6
    }

    return q


# ----------------------------
# Process files
# ----------------------------
def process_all():
    files = list(STRUCTURED_PATH.glob("*structured.json"))

    if not files:
        print("❌ No structured files found")
        return

    for file in files:
        print(f"🔍 Validating: {file.name}")

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        validated = []

        for q in data:
            validated.append(validate_question(q))

        output_file = VALIDATED_PATH / file.name.replace("structured", "validated")

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(validated, f, indent=2)

        print(f"✅ Saved: {output_file}")


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    process_all()