import json
from pathlib import Path

f = Path(r"C:\projects\Data_Engineering\textgen\output\curr_dataset\iitjee_physics_curriculum.json")
with open(f, encoding="utf-8") as fh:
    data = json.load(fh)

# Show type and top-level structure
print(f"Type: {type(data)}")

if isinstance(data, list):
    print(f"Array length: {len(data)}")
    print(f"\nFirst item keys: {list(data[0].keys())}")
    print(f"\nFirst item sample:")
    print(json.dumps(data[0], indent=2)[:800])
elif isinstance(data, dict):
    print(f"Dict keys: {list(data.keys())}")
    print(json.dumps(data, indent=2)[:800])