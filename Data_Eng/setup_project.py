import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Get root path
root = os.getenv("PROJECT_ROOT")

if not root:
    raise ValueError("PROJECT_ROOT not set in .env")

# Define folder structure
folders = [
    "input_pdfs",
    "output/raw_text",
    "output/reworded_text",
    "output/json_output",
    "logs"
]

# Create folders
for folder in folders:
    path = Path(root) / folder
    path.mkdir(parents=True, exist_ok=True)
    print(f"Created: {path}")

print("✅ Folder structure ready.")