# save as inspect_full.py
import json
from pathlib import Path

JSON_DIR = Path(r"C:\projects\Data_Engineering\textgen\output\final_dataset")
files    = sorted(JSON_DIR.glob("**/*.json"))

with open(files[0], encoding="utf-8") as f:
    data = json.load(f)

# Show first full record
print(json.dumps(data[0], indent=2, ensure_ascii=False))
print(f"\n--- Total records across all files ---")
total = 0
for f in files:
    with open(f, encoding="utf-8") as fh:
        d = json.load(fh)
    print(f"  {f.name}: {len(d)} records")
    total += len(d)
print(f"  Total: {total}")