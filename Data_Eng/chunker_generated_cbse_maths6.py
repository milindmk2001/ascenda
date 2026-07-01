"""
chunker_generated_cbse_maths6.py
Parses Claude-generated CBSE Maths 6 (Ganita Prakash) .md files.

Section structure per chapter file:
  # Chapter N: Title
  ## CONCEPT EXPLANATION
  ## KEY RULES AND DEFINITIONS
  ## STEP BY STEP WORKED EXAMPLES
  ## PRACTICE PROBLEMS
  ## COMMON CONFUSIONS
  ## REAL LIFE CONNECTIONS

Inserts into public.generated_content.
"""

import os
import re
import uuid
import psycopg2
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL    = os.environ["DATABASE_DIRECT_URL"]
INPUT_DIR = Path(r"C:\projects\data_sources\school\cbse\grade_6\mathematics\generated")
EXAM_TYPE = "CBSE"
SUBJECT   = "Mathematics"
GRADE     = "Grade 6"
GEN_BY    = "claude-opus-4-6"

# ── SECTION HEADER → content_type MAP ────────────────────────
SECTION_MAP = {
    "CONCEPT EXPLANATION":          "concept",
    "KEY RULES AND DEFINITIONS":    "rules",
    "STEP BY STEP WORKED EXAMPLES": "worked_example",
    "PRACTICE PROBLEMS":            "practice",
    "COMMON CONFUSIONS":            "common_mistakes",
    "REAL LIFE CONNECTIONS":        "real_life",
}

# ── HELPERS ───────────────────────────────────────────────────
def clean(text: str) -> str:
    text = text.replace('\x00', '')
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def strip_heading(line: str) -> str:
    return line.lstrip('#').strip()

def detect_section_type(line: str):
    stripped = line.strip()
    if not stripped.startswith('##'):
        return None
    heading = strip_heading(stripped).upper()
    for key, val in SECTION_MAP.items():
        if heading.startswith(key):
            return val
    return None

def extract_chapter_info(filepath: Path):
    """Ch01_Patterns_in_Mathematics.md → (1, 'Patterns in Mathematics')"""
    stem  = filepath.stem
    match = re.match(r'^Ch(\d+)_(.+)$', stem)
    if match:
        num   = int(match.group(1))
        title = match.group(2).replace('_', ' ')
        return num, title
    return 0, stem.replace('_', ' ')

# ── PARSE ONE CHAPTER FILE ────────────────────────────────────
def parse_chapter_file(filepath: Path) -> list:
    text       = filepath.read_text(encoding="utf-8")
    lines      = text.split('\n')
    chapter_num, chapter_title = extract_chapter_info(filepath)

    sections        = []
    current_type    = None
    current_content = []

    def flush():
        nonlocal current_type, current_content
        content = clean('\n'.join(current_content))
        if content and len(content.strip()) >= 30 and current_type:
            sections.append({
                "content_type":  current_type,
                "content":       content,
                "chapter_num":   chapter_num,
                "chapter_title": chapter_title,
            })
        current_content = []

    for line in lines:
        stripped = line.strip()
        # Skip top-level # heading lines
        if stripped.startswith('# ') and not stripped.startswith('##'):
            continue

        section_type = detect_section_type(line)
        if section_type is not None:
            flush()
            current_type = section_type
            continue

        if current_type:
            current_content.append(line)

    flush()
    return sections

# ── ALREADY PROCESSED CHECK ───────────────────────────────────
def already_processed(cur, source_file: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM public.generated_content WHERE source_file = %s AND exam_type = %s",
        (source_file, EXAM_TYPE)
    )
    return cur.fetchone()[0] > 0

# ── MAIN ──────────────────────────────────────────────────────
def chunk_all():
    md_files = sorted(INPUT_DIR.glob("Ch*.md"))

    print(f"\n{'='*60}")
    print(f"  chunker_generated_cbse_maths6.py")
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Found  : {len(md_files)} .md file(s)")
    print(f"  Target : public.generated_content")
    print(f"{'='*60}\n")

    if not md_files:
        print(f"  No Ch*.md files found in {INPUT_DIR}")
        return

    conn            = psycopg2.connect(DB_URL)
    conn.autocommit = False
    total_inserted  = 0
    skip_count      = 0
    fail_count      = 0

    for md_path in tqdm(md_files, desc="Chunking .md files"):
        cur = conn.cursor()
        try:
            if already_processed(cur, md_path.name):
                print(f"\n  ⏭  Already done: {md_path.name}")
                cur.close()
                skip_count += 1
                continue

            print(f"\n  📄 {md_path.name}")
            sections = parse_chapter_file(md_path)
            print(f"     Sections found: {len(sections)}")

            file_inserted = 0
            for sec in sections:
                content = sec["content"]
                if not content or len(content.strip()) < 30:
                    continue

                chapter_label = f"Chapter {sec['chapter_num']}: {sec['chapter_title']}"

                prefixed = (
                    f"[{EXAM_TYPE} | {SUBJECT} | {GRADE} | "
                    f"{chapter_label} | {sec['content_type']}]\n\n"
                    f"{content}"
                )

                cur.execute("""
                    INSERT INTO public.generated_content (
                        id, unit, subject, exam_type, topic,
                        content_type, content, difficulty,
                        source_file, generated_by
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (
                    str(uuid.uuid4()),
                    chapter_label,
                    SUBJECT,
                    EXAM_TYPE,
                    sec['chapter_title'],
                    sec['content_type'],
                    prefixed,
                    None,
                    md_path.name,
                    GEN_BY,
                ))
                file_inserted += 1
                print(f"     ✓  {sec['content_type']}")

            conn.commit()
            cur.close()
            total_inserted += file_inserted
            print(f"     File total: {file_inserted} chunks")

        except Exception as e:
            try:
                conn.rollback()
            except Exception:
                pass
            try:
                cur.close()
            except Exception:
                pass
            fail_count += 1
            print(f"\n  ❌ Failed: {md_path.name} — {e}")
            continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Done")
    print(f"  ✅ Inserted : {total_inserted} section chunks")
    print(f"  ⏭  Skipped  : {skip_count} files")
    print(f"  ❌ Failed   : {fail_count} files")
    print(f"\n  Verify in Supabase:")
    print(f"  SELECT content_type, COUNT(*)")
    print(f"  FROM public.generated_content")
    print(f"  WHERE exam_type = 'CBSE'")
    print(f"  GROUP BY content_type ORDER BY count DESC;")
    print(f"\n  Next: python embedder_generated.py")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    chunk_all()
