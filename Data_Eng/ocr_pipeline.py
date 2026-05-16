import os
from pathlib import Path
from dotenv import load_dotenv
from pdf2image import convert_from_path
import pytesseract

# ----------------------------
# Load environment
# ----------------------------
load_dotenv()
ROOT = os.getenv("PROJECT_ROOT")

if not ROOT:
    raise ValueError("PROJECT_ROOT not set in .env")

# ----------------------------
# Paths
# ----------------------------
INPUT_FOLDER = Path(ROOT) / "input_pdfs" / "OCR"
OUTPUT_FOLDER = Path(ROOT) / "output" / "raw_text"
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

# Poppler path (FIXED)
POPPLER_PATH = r"C:\Release-26.02.0-0\poppler-26.02.0\Library\bin"

# Tesseract path
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


# ----------------------------
# OCR function
# ----------------------------
def ocr_pdf(pdf_path: Path):
    print(f"🔍 Processing OCR: {pdf_path.name}")

    try:
        pages = convert_from_path(
            pdf_path,
            dpi=300,
            poppler_path=POPPLER_PATH
        )
    except Exception as e:
        print(f"❌ Failed to convert PDF: {pdf_path.name} | {e}")
        return ""

    full_text = ""

    for i, page in enumerate(pages):
        try:
            text = pytesseract.image_to_string(page)
        except Exception as e:
            print(f"⚠️ OCR failed on page {i+1} of {pdf_path.name}: {e}")
            continue

        full_text += f"\n\n===== PAGE {i+1} =====\n\n"
        full_text += text

    return full_text


# ----------------------------
# Main pipeline
# ----------------------------
def process_all():
    pdf_files = list(INPUT_FOLDER.glob("*.pdf"))

    if not pdf_files:
        print("❌ No PDFs found in OCR folder")
        return

    print(f"📦 Found {len(pdf_files)} PDFs")

    for pdf in pdf_files:
        text = ocr_pdf(pdf)

        if not text.strip():
            print(f"⚠️ No text extracted: {pdf.name}")
            continue

        output_file = OUTPUT_FOLDER / f"{pdf.stem}_ocr.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(text)

        print(f"✅ Saved: {output_file}")


# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    process_all()