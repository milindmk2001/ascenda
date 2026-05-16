import os
from pathlib import Path
from dotenv import load_dotenv
import pdfplumber

# Load env
load_dotenv()
root = os.getenv("PROJECT_ROOT")

if not root:
    raise ValueError("PROJECT_ROOT not set")

input_folder = Path(root) / "input_pdfs"
output_folder = Path(root) / "output" / "raw_text"

# Ensure output exists
output_folder.mkdir(parents=True, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")

    return text


def generate_filename(original_name):
    """
    You can later enhance this using:
    - subject detection
    - unit/subtopic extraction
    """
    base = Path(original_name).stem

    # Placeholder naming (you will enrich later)
    return f"{base}_raw.txt"


def process_pdfs():
    pdf_files = list(input_folder.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDFs found in input_pdfs")
        return

    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")

        text = extract_text_from_pdf(pdf_file)

        if not text.strip():
            print(f"⚠️ No text extracted from {pdf_file.name}")
            continue

        output_file_name = generate_filename(pdf_file.name)
        output_path = output_folder / output_file_name

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Saved: {output_path}")


if __name__ == "__main__":
    process_pdfs()