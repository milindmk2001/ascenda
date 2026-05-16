# save as inspect_questions.py in Data_Eng folder
import json
from pathlib import Path

JSON_DIR = Path(r"C:\projects\Data_Engineering\textgen\output\final_dataset")

files = list(JSON_DIR.glob("**/*.json"))
print(f"Found {len(files)} JSON file(s)\n")

# Show structure of first file
if files:
    with open(files[0], encoding="utf-8") as f:
        data = json.load(f)

    print(f"File: {files[0].name}")
    print(f"Type: {type(data)}")

    if isinstance(data, list):
        print(f"Records: {len(data)}")
        print(f"\nFirst record keys: {data[0].keys()}")
        print(f"\nFirst record sample:")
        print(json.dumps(data[0], indent=2)[:1000])

    elif isinstance(data, dict):
        print(f"Keys: {data.keys()}")
        print(f"\nSample:")
        print(json.dumps(data, indent=2)[:1000])