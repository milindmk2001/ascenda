import os
import json
import time
import re
from pathlib import Path
from dotenv import load_dotenv

from gemini_client import repair_warning, repair_bad
from validation_layer_v2 import calculate_score

load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

STRUCTURED_DIR = Path(ROOT) / "output" / "structured"
RAW_TEXT_DIR = Path(ROOT) / "output" / "raw_text"

FINAL_DIR = Path(ROOT) / "output" / "final"
WARNING_DIR = Path(ROOT) / "output" / "warning_repaired"
BAD_DIR = Path(ROOT) / "output" / "bad_repaired"
FAILED_OCR_DIR = Path(ROOT) / "output" / "failed_ocr"

REPORT_PATH = Path(ROOT) / "output" / "quality_reports" / "quality_report.json"

for p in [FINAL_DIR, WARNING_DIR, BAD_DIR, FAILED_OCR_DIR]:
    p.mkdir(parents=True, exist_ok=True)


def classify(score):
    if score >= 0.85:
        return "GOOD"
    elif score >= 0.65:
        return "WARNING"
    else:
        return "BAD"


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_raw(file_name):
    base = file_name.replace("_structured.json", "")

    candidates = [
        RAW_TEXT_DIR / f"{base}.txt",
        RAW_TEXT_DIR / f"{base}_ocr.txt",
        RAW_TEXT_DIR / f"{base.replace('_raw', '_ocr')}.txt",
        RAW_TEXT_DIR / f"{base.replace('_ocr', '_raw')}.txt"
    ]

    for path in candidates:
        if path.exists():
            return path

    return None


def clean_raw_text(text):
    text = re.sub(r"===== PAGE \d+ =====", " ", text)
    text = re.sub(r"(Answer\s*){3,}", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def is_garbage_text(text):
    text_lower = text.lower()

    if len(text.strip()) < 500:
        return True

    if text_lower.count("answer") > 20 and text_lower.count("question") < 3:
        return True

    if sum(c.isdigit() for c in text) < 5:
        return True

    mcq_signal = (
        text.count("(A)") +
        text.count("(B)") +
        text.count("(C)") +
        text.count("(D)") +
        text.count(" A ") +
        text.count(" B ") +
        text.count(" C ") +
        text.count(" D ")
    )

    if mcq_signal < 4:
        return True

    return False


def save_failed_ocr(file_name, raw_text, reason):
    out = FAILED_OCR_DIR / file_name.replace("_structured.json", "_failed_ocr.json")
    save_json({
        "file": file_name,
        "reason": reason,
        "raw_preview": raw_text[:1000]
    }, out)


def run():
    if not REPORT_PATH.exists():
        print("❌ Run validation_layer_v2.py first")
        return

    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        report = json.load(f)

    print(f"📦 Found {len(report)} files\n")

    stats = {
        "GOOD": 0,
        "WARNING": 0,
        "BAD": 0,
        "PROMOTED": 0,
        "FAILED_OCR": 0,
        "FAILED": 0
    }

    for item in report:
        file_name = item["file"]
        score = item["score"]
        status = classify(score)

        print(f"\n🔍 {file_name}")
        print(f"📊 Original: {score:.3f} → {status}")

        structured_path = STRUCTURED_DIR / file_name

        if not structured_path.exists():
            print("❌ Missing structured file")
            stats["FAILED"] += 1
            continue

        data = load_json(structured_path)

        try:
            if status == "GOOD":
                save_json(data, FINAL_DIR / file_name)
                print("🟢 FINAL")
                stats["GOOD"] += 1

            elif status == "WARNING":
                repaired = repair_warning(data)

                new_score = calculate_score(repaired)
                new_status = classify(new_score)

                print(f"📈 New: {new_score:.3f} → {new_status}")

                if new_status == "GOOD":
                    save_json(repaired, FINAL_DIR / file_name)
                    print("🟢 WARNING → GOOD")
                    stats["PROMOTED"] += 1
                else:
                    save_json(repaired, WARNING_DIR / file_name)
                    print("🟡 SAVED WARNING")
                    stats["WARNING"] += 1

            else:
                raw_file = get_raw(file_name)

                if not raw_file:
                    print("❌ Missing raw text")
                    stats["FAILED"] += 1
                    continue

                raw_text = raw_file.read_text(encoding="utf-8")

                print("🧪 RAW TEXT DEBUG")
                print(f"📄 Length: {len(raw_text)}")
                print(f"📄 Preview: {raw_text[:200]}")
                print("-" * 40)

                if is_garbage_text(raw_text):
                    print("🚫 Garbage OCR detected → skipping Gemini")
                    save_failed_ocr(file_name, raw_text, "garbage_or_answer_only_text")
                    stats["FAILED_OCR"] += 1
                    continue

                cleaned_text = clean_raw_text(raw_text)

                rebuilt = repair_bad(cleaned_text)

                if not rebuilt or len(rebuilt) < 3:
                    print("🚫 Too few questions extracted → failed OCR")
                    save_failed_ocr(file_name, raw_text, "too_few_questions_extracted")
                    stats["FAILED_OCR"] += 1
                    continue

                new_score = calculate_score(rebuilt)
                new_status = classify(new_score)

                print(f"📈 New: {new_score:.3f} → {new_status}")

                if new_status == "GOOD":
                    save_json(rebuilt, FINAL_DIR / file_name)
                    print("🟢 BAD → GOOD")
                    stats["PROMOTED"] += 1
                elif new_status == "WARNING":
                    save_json(rebuilt, WARNING_DIR / file_name)
                    print("🟡 BAD → WARNING")
                    stats["PROMOTED"] += 1
                else:
                    save_json(rebuilt, BAD_DIR / file_name)
                    print("🔴 STILL BAD")
                    stats["BAD"] += 1

        except Exception as e:
            print(f"❌ Error: {e}")
            stats["FAILED"] += 1

        time.sleep(1)

    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(json.dumps(stats, indent=2))
    print("=" * 60)


if __name__ == "__main__":
    run()