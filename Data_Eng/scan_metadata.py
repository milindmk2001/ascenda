import os
import json
import re
import fitz
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── PATHS ─────────────────────────────────────────────────────
# Should be THIS — chem paths
PDF_DIR     = Path(r"C:\projects\Data_Engineering\sourceData\openumn\chem")
OUTPUT_JSON = Path(r"C:\projects\Data_Engineering\book_metadata_chem.json")

# ── KNOWN METADATA (pre-filled — no API call needed) ─────────
KNOWN_META = {
    "978-3-030-15195-9.pdf": {
        "title":           "Physics from Symmetry",
        "authors":         ["Jakob Schwichtenberg"],
        "edition":         "2nd Edition",
        "publisher":       "Springer",
        "pub_year":        2018,
        "subject":         "Physics",
        "is_solutions":    False,
        "license":         "CC-BY-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/978-3-030-15195-9",
        "curriculum_type": "open",
    },
    "Atomic Physics for Everyone_ An Introduction to Atomic Physics Q.pdf": {
        "title":           "Atomic Physics for Everyone: An Introduction to Atomic Physics",
        "authors":         [],
        "edition":         None,
        "publisher":       None,
        "pub_year":        None,
        "subject":         "Atomic Physics",
        "is_solutions":    False,
        "license":         "CC-BY-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/atomic-physics-for-everyone",
        "curriculum_type": "open",
    },
    "Electromagnetics_Vol1_Problems.pdf": {
        "title":           "Electromagnetics Vol 1 - Problems",
        "authors":         ["Steven Ellingson"],
        "edition":         None,
        "publisher":       "Virginia Tech",
        "pub_year":        2018,
        "subject":         "Electromagnetism",
        "is_solutions":    False,
        "license":         "CC-BY-SA-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/electromagnetics-vol-1",
        "curriculum_type": "supplement",
    },
    "Electromagnetics_Vol1_screen-reader-friendly.pdf": {
        "title":           "Electromagnetics Vol 1",
        "authors":         ["Steven Ellingson"],
        "edition":         None,
        "publisher":       "Virginia Tech",
        "pub_year":        2018,
        "subject":         "Electromagnetism",
        "is_solutions":    False,
        "license":         "CC-BY-SA-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/electromagnetics-vol-1",
        "curriculum_type": "open",
    },
    "Electromagnetics_Vol1_Solutions.pdf": {
        "title":           "Electromagnetics Vol 1 - Solutions",
        "authors":         ["Steven Ellingson"],
        "edition":         None,
        "publisher":       "Virginia Tech",
        "pub_year":        2018,
        "subject":         "Electromagnetism",
        "is_solutions":    True,
        "license":         "CC-BY-SA-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/electromagnetics-vol-1",
        "curriculum_type": "supplement",
    },
    "Electromagnetics_Vol2.pdf": {
        "title":           "Electromagnetics Vol 2",
        "authors":         ["Steven Ellingson"],
        "edition":         None,
        "publisher":       "Virginia Tech",
        "pub_year":        2020,
        "subject":         "Electromagnetism",
        "is_solutions":    False,
        "license":         "CC-BY-SA-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/electromagnetics-vol-2",
        "curriculum_type": "open",
    },
    "Vol1_(1.1)_Pblms.pdf": {
        "title":           "University Physics Volume 1 - Problems (v1.1)",
        "authors":         ["OpenStax"],
        "edition":         "1.1",
        "publisher":       "OpenStax",
        "pub_year":        2016,
        "subject":         "Physics",
        "is_solutions":    False,
        "license":         "CC-BY-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/university-physics-volume-1",
        "curriculum_type": "supplement",
    },
    "Vol1_(1.1)_Solutions.pdf": {
        "title":           "University Physics Volume 1 - Solutions (v1.1)",
        "authors":         ["OpenStax"],
        "edition":         "1.1",
        "publisher":       "OpenStax",
        "pub_year":        2016,
        "subject":         "Physics",
        "is_solutions":    True,
        "license":         "CC-BY-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/university-physics-volume-1",
        "curriculum_type": "supplement",
    },
    "Vol1_(1.3) Pblms.pdf": {
        "title":           "University Physics Volume 1 - Problems (v1.3)",
        "authors":         ["OpenStax"],
        "edition":         "1.3",
        "publisher":       "OpenStax",
        "pub_year":        2016,
        "subject":         "Physics",
        "is_solutions":    False,
        "license":         "CC-BY-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/university-physics-volume-1",
        "curriculum_type": "supplement",
    },
    "Vol1_(1.3) Solutions.pdf": {
        "title":           "University Physics Volume 1 - Solutions (v1.3)",
        "authors":         ["OpenStax"],
        "edition":         "1.3",
        "publisher":       "OpenStax",
        "pub_year":        2016,
        "subject":         "Physics",
        "is_solutions":    True,
        "license":         "CC-BY-4.0",
        "source_url":      "https://open.umn.edu/opentextbooks/textbooks/university-physics-volume-1",
        "curriculum_type": "supplement",
    },
}

# ── PYMUPDF EMBEDDED METADATA ─────────────────────────────────
def extract_embedded_metadata(pdf_path: Path) -> dict:
    try:
        doc   = fitz.open(str(pdf_path))
        meta  = doc.metadata or {}
        pages = len(doc)
        doc.close()
        return {
            "title":       (meta.get("title")  or "").strip(),
            "authors":     (meta.get("author") or "").strip(),
            "subject":     (meta.get("subject") or "").strip(),
            "total_pages": pages,
        }
    except Exception as e:
        print(f"    ⚠  PyMuPDF error: {e}")
        return {"title": "", "authors": "", "subject": "", "total_pages": 0}

# ── BUILD FINAL ENTRY ─────────────────────────────────────────
def build_entry(pdf_path: Path) -> dict:
    fname    = pdf_path.name
    known    = KNOWN_META.get(fname, {})
    embedded = extract_embedded_metadata(pdf_path)

    title = (
        known.get("title")
        or embedded["title"]
        or pdf_path.stem.replace("_", " ").title()
    )

    authors = known.get("authors", [])
    if not authors and embedded["authors"]:
        authors = [
            a.strip()
            for a in re.split(r"[;,]", embedded["authors"])
            if a.strip()
        ]

    source_url  = known.get("source_url", "")
    license_val = known.get("license", "CC-BY-4.0")
    edition     = known.get("edition")
    pub_year    = known.get("pub_year")
    author_str  = ", ".join(authors) if authors else "Unknown Author"
    edition_str = f", {edition}" if edition else ""
    year_str    = f" ({pub_year})" if pub_year else ""
    attribution = (
        f"{author_str}, {title}{edition_str}{year_str}, "
        f"{license_val}, {source_url or 'open.umn.edu'}"
    )

    return {
        "title":           title,
        "authors":         authors,
        "edition":         edition,
        "publisher":       known.get("publisher"),
        "pub_year":        pub_year,
        "subject":         known.get("subject") or embedded["subject"] or "Physics",
        "is_solutions":    known.get("is_solutions", False),
        "license":         license_val,
        "source_url":      source_url,
        "attribution":     attribution,
        "curriculum_type": known.get("curriculum_type", "open"),
        "total_pages":     embedded["total_pages"],
    }

# ── MAIN ──────────────────────────────────────────────────────
def scan_all():
    pdf_files = sorted(PDF_DIR.glob("**/*.pdf"))
    print(f"\n{'='*60}")
    print(f"  scan_metadata.py  (no API calls — instant)")
    print(f"{'='*60}")
    print(f"\n  Found {len(pdf_files)} PDF(s)\n")

    existing = {}
    if OUTPUT_JSON.exists():
        with open(OUTPUT_JSON, encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = {}
        print(f"  Loaded existing JSON — skipping already scanned\n")

    for pdf_path in pdf_files:
        if pdf_path.name in existing:
            print(f"  ⏭  Skipping : {pdf_path.name}")
            continue

        print(f"  🔍 Scanning : {pdf_path.name}")
        try:
            entry = build_entry(pdf_path)
            existing[pdf_path.name] = entry

            with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2, ensure_ascii=False)

            print(f"     ✓  Title     : {entry['title']}")
            print(f"        Authors   : {entry['authors']}")
            print(f"        Pages     : {entry['total_pages']}")
            print(f"        License   : {entry['license']}")
            print(f"        Type      : {entry['curriculum_type']}")
            print(f"        Solutions : {entry['is_solutions']}")
        except Exception as e:
            print(f"     ❌ Failed: {e}")

    scanned = sum(1 for f in pdf_files if f.name in existing)
    print(f"\n{'='*60}")
    print(f"  ✅ {scanned}/{len(pdf_files)} PDFs scanned — no API calls used")
    print(f"  Saved to: {OUTPUT_JSON}")
    print(f"\n  Next: python verify_metadata.py")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    scan_all()
