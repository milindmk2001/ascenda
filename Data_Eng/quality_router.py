import json
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

STRUCTURED = Path(ROOT) / "output" / "structured"
ROUTED = Path(ROOT) / "output" / "routed"

GOOD = ROUTED / "good"
WARNING = ROUTED / "warning"
BAD = ROUTED / "bad"

for p in [GOOD, WARNING, BAD]:
    p.mkdir(parents=True, exist_ok=True)


# ----------------------------
# classify file
# ----------------------------
def classify(score):
    if score >= 0.85:
        return "good"
    elif score >= 0.6:
        return "warning"
    return "bad"


# ----------------------------
# route files
# ----------------------------
def route():
    files = list(STRUCTURED.glob("*structured.json"))

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        # compute avg score
        scores = [
            q.get("validation", {}).get("confidence", 0)
            for q in data
        ]

        avg_score = sum(scores) / len(scores) if scores else 0

        category = classify(avg_score)

        target_folder = {
            "good": GOOD,
            "warning": WARNING,
            "bad": BAD
        }[category]

        out_path = target_folder / file.name

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print(f"📦 {file.name} → {category.upper()} ({avg_score:.2f})")


if __name__ == "__main__":
    route()