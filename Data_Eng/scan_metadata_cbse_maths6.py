import os
import fitz
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

# ── CONFIG — update these two UUIDs from Step E ───────────────
REGULAR_SUBJECT_ID = "83ccb181-4c17-44f3-96b5-74682548d7aa"
PDF_DIR            = Path(r"C:\projects\Data_Engineering\sourceData\cbse\maths_6")

# ── KNOWN METADATA for each NCERT PDF ─────────────────────────
# File names must match exactly what is in your folder
KNOWN_META = {
    "fegp101.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 1: Knowing Our Numbers",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp102.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 2: Whole Numbers",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp103.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 3: Playing with Numbers",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp104.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 4: Basic Geometrical Ideas",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp105.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 5: Understanding Elementary Shapes",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp106.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 6: Integers",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp107.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 7: Fractions",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp108.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 8: Decimals",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp109.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 9: Data Handling",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp110.pdf": {
        "title":           "NCERT Class 6 Mathematics - Chapter 10: Mensuration",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics, internal use only",
        "curriculum_type": "school",
        "language":        "en",
    },
    "fegp1ps.pdf": {
        "title":           "NCERT Class 6 Mathematics - Practice Set",
        "authors":         ["NCERT"],
        "edition":         None,
        "publisher":       "NCERT",
        "pub_year":        2023,
        "license":         "internal",
        "license_url":     None,
        "source_url":      "https://ncert.nic.in",
        "attribution":     "NCERT, Class 6 Mathematics Practice Set, internal use only",
        "curriculum_type": "supplement",
        "language":        "en",
    },
}

# ── GET PAGE COUNT FROM PDF ───────────────────────────────────
def get_page_count(pdf_path: Path) -> int:
    try:
        doc = fitz.open(str(pdf_path))
        pages = len(doc)
        doc.close()
        return pages
    except Exception as e:
        print(f"    ⚠  Could not read {pdf_path.name}: {e}")
        return 0

# ── MAIN ──────────────────────────────────────────────────────
def main():
    DATABASE_URL = os.environ.get("DATABASE_DIRECT_URL")
    if not DATABASE_URL:
        print("❌ DATABASE_URL not found in .env — aborting.")
        return

    engine = create_engine(DATABASE_URL)

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    print(f"\n{'='*60}")
    print(f"  scan_metadata_cbse_maths6.py")
    print(f"{'='*60}")
    print(f"\n  Found {len(pdf_files)} PDF(s) in {PDF_DIR}\n")

    inserted = 0
    skipped  = 0
    errors   = 0

    with engine.connect() as conn:
        for pdf_path in pdf_files:
            fname = pdf_path.name
            meta  = KNOWN_META.get(fname)

            if not meta:
                print(f"  ⚠  No metadata defined for: {fname} — skipping")
                skipped += 1
                continue

            # Check if already inserted (by file_name)
            existing = conn.execute(
                text("SELECT id FROM public.books WHERE file_name = :fn"),
                {"fn": fname}
            ).fetchone()

            if existing:
                print(f"  ⏭  Already in DB: {fname}")
                skipped += 1
                continue

            total_pages = get_page_count(pdf_path)

            try:
                conn.execute(text("""
                    INSERT INTO public.books (
                        id,
                        title,
                        authors,
                        regular_subject_id,
                        exam_subject_id,
                        license,
                        license_url,
                        source_url,
                        attribution,
                        publisher,
                        edition,
                        pub_year,
                        language,
                        curriculum_type,
                        file_name,
                        file_hash,
                        total_pages,
                        status,
                        created_at,
                        updated_at
                    ) VALUES (
                        gen_random_uuid(),
                        :title,
                        ARRAY['NCERT']::text[],
                        :regular_subject_id,
                        NULL,
                        :license,
                        :license_url,
                        :source_url,
                        :attribution,
                        :publisher,
                        :edition,
                        :pub_year,
                        :language,
                        :curriculum_type,
                        :file_name,
                        NULL,
                        :total_pages,
                        'pending',
                        NOW(),
                        NOW()
                    )
                """), {
                    "title":              meta["title"],
                    "authors":            meta["authors"],
                    "regular_subject_id": REGULAR_SUBJECT_ID,
                    "license":            meta["license"],
                    "license_url":        meta["license_url"],
                    "source_url":         meta["source_url"],
                    "attribution":        meta["attribution"],
                    "publisher":          meta["publisher"],
                    "edition":            meta["edition"],
                    "pub_year":           meta["pub_year"],
                    "language":           meta["language"],
                    "curriculum_type":    meta["curriculum_type"],
                    "file_name":          fname,
                    "total_pages":        total_pages,
                })
                conn.commit()
                print(f"  ✅ Inserted: {meta['title']} ({total_pages} pages)")
                inserted += 1

            except Exception as e:
                conn.rollback()
                print(f"  ❌ Failed to insert {fname}: {e}")
                errors += 1

    print(f"\n{'='*60}")
    print(f"  Done.")
    print(f"  ✅ Inserted : {inserted}")
    print(f"  ⏭  Skipped  : {skipped}")
    print(f"  ❌ Errors   : {errors}")
    print(f"\n  Next: verify in Supabase Studio:")
    print(f"  SELECT id, title, file_name, status")
    print(f"  FROM public.books")
    print(f"  WHERE regular_subject_id = '{REGULAR_SUBJECT_ID}'")
    print(f"  ORDER BY title;")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
