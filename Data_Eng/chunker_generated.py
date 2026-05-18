"""
chunker_generated.py
Parses Claude-generated Physics textbook .md files.

Actual structure per topic block:
  # Topic Name                     ← single # heading
  ## THEORY                        ← double ## for sections
  ## KEY FORMULAE
  ## SOLVED PROBLEMS
    **Problem 1 [Easy ...]**
    **Problem 2 [Medium ...]**
    ...
  ## UNSOLVED PROBLEMS
  ## COMMON EXAM MISTAKES

Inserts into public.generated_content with curriculum FK link.
"""

import os
import re
import uuid
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL    = os.environ["DATABASE_DIRECT_URL"]
INPUT_DIR = Path(r"C:\projects\Data_Engineering\textgen\output\generated_textbooks\Physics")
EXAM_TYPE = "IITJEE"
SUBJECT   = "Physics"
GEN_BY    = "claude-sonnet-4-20250514"

# ── HELPERS ───────────────────────────────────────────────────
def clean(text: str) -> str:
    text = text.replace('\x00', '')
    text = re.sub(r'\n{4,}', '\n\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

def extract_unit_from_filename(fname: str) -> str:
    """Unit01_Unit_1__Units_and_Measurement → Unit 1 — Units and Measurement"""
    stem = Path(fname).stem
    stem = re.sub(r'^Unit\d+_', '', stem)
    stem = stem.replace('__', ' — ').replace('_', ' ')
    return stem.strip()

def strip_heading(line: str) -> str:
    """Remove leading # characters and strip"""
    return line.lstrip('#').strip()

# ── SECTION TYPE DETECTION ────────────────────────────────────
def detect_section_type(line: str) -> str | None:
    """
    Detects ## section headers.
    Returns section type string or None.
    """
    stripped = line.strip()
    # Must start with ## (double hash = section header)
    if not stripped.startswith('##'):
        return None

    heading = strip_heading(stripped).upper()

    if heading.startswith('THEORY'):
        return 'theory'
    if 'KEY FORMULAE' in heading or heading.startswith('FORMULAE'):
        return 'formulae'
    if 'SOLVED PROBLEMS' in heading or 'WORKED EXAMPLE' in heading:
        return 'solved_problems'
    if 'UNSOLVED PROBLEMS' in heading or 'PRACTICE PROBLEMS' in heading:
        return 'unsolved_problem'
    if 'COMMON' in heading and ('MISTAKE' in heading or 'ERROR' in heading):
        return 'common_mistakes'
    if heading.startswith('SUMMARY') or 'QUICK REVISION' in heading:
        return 'summary'
    return None

def is_problem_header(line: str) -> bool:
    """Detects **Problem N [...]** lines"""
    stripped = line.strip()
    return bool(re.match(r'^\*\*Problem\s+\d+', stripped, re.IGNORECASE))

def get_problem_difficulty(line: str) -> str:
    """Extract difficulty from **Problem N [Easy — JEE Main]**"""
    line_upper = line.upper()
    if 'HARD' in line_upper or 'ADVANCED' in line_upper:
        return 'Hard'
    if 'MEDIUM' in line_upper:
        return 'Medium'
    return 'Easy'

# ── PARSE ONE TOPIC BLOCK ─────────────────────────────────────
def parse_topic_block(block: str, unit: str, filename: str) -> dict | None:
    """
    Parse one topic block (between --- separators).
    Returns dict with topic name and typed section chunks.
    """
    lines        = block.split('\n')
    topic_name   = ""
    sections     = []

    current_type    = None
    current_content = []
    current_diff    = None
    in_solved       = False   # are we inside ## SOLVED PROBLEMS?

    def flush():
        nonlocal current_type, current_content, current_diff
        text = clean('\n'.join(current_content))
        if text and len(text.strip()) >= 30 and current_type:
            sections.append({
                "content_type": current_type,
                "content":      text,
                "difficulty":   current_diff,
            })
        current_content = []
        current_diff    = None

    for line in lines:
        stripped = line.strip()

        # ── Detect topic name: single # heading ───────────────
        if not topic_name:
            if stripped.startswith('# ') and not stripped.startswith('##'):
                topic_name = strip_heading(stripped)
            continue   # skip header metadata lines until topic found

        # ── Detect ## section headers ─────────────────────────
        section_type = detect_section_type(line)
        if section_type is not None:
            flush()
            if section_type == 'solved_problems':
                in_solved    = True
                current_type = 'worked_example'
            else:
                in_solved    = False
                current_type = section_type
            continue

        # ── Inside SOLVED PROBLEMS: split on each Problem N ───
        if in_solved and is_problem_header(line):
            flush()
            current_type = 'worked_example'
            current_diff = get_problem_difficulty(line)
            current_content.append(line)
            continue

        # ── Accumulate content ────────────────────────────────
        if current_type:
            current_content.append(line)

    flush()  # flush last section

    if not topic_name or not sections:
        return None

    return {
        "topic":    topic_name,
        "unit":     unit,
        "filename": filename,
        "sections": sections,
    }

# ── PARSE FULL .md FILE ───────────────────────────────────────
def parse_md_file(filepath: Path) -> list[dict]:
    text   = filepath.read_text(encoding="utf-8")
    unit   = extract_unit_from_filename(filepath.name)
    blocks = re.split(r'\n---+\n', text)
    topics = []

    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Skip file header (CONTENTS block) and sources footer
        if 'CONTENTS' in block[:300] and block.count('\n') < 20:
            continue
        if block.upper().startswith('SOURCES'):
            continue

        parsed = parse_topic_block(block, unit, filepath.name)
        if parsed and parsed.get("topic") and parsed.get("sections"):
            topics.append(parsed)

    return topics

# ── FIND MATCHING CURRICULUM CHUNK ───────────────────────────
def find_curriculum_chunk_id(cur, topic: str) -> str | None:
    cur.execute("""
        SELECT c.id
        FROM public.chunks c
        JOIN public.books b ON b.id = c.book_id
        WHERE b.curriculum_type = 'iitjee'
          AND c.chunk_strategy  = 'curriculum_topic'
          AND c.section_title   ILIKE %s
        LIMIT 1
    """, (f"%{topic[:35]}%",))
    row = cur.fetchone()
    return str(row[0]) if row else None

# ── INSERT TOPIC SECTIONS ─────────────────────────────────────
def insert_topic(cur, topic_data: dict) -> int:
    unit     = topic_data["unit"]
    topic    = topic_data["topic"]
    filename = topic_data["filename"]
    sections = topic_data["sections"]
    inserted = 0

    curr_chunk_id = find_curriculum_chunk_id(cur, topic)

    for section in sections:
        content = section["content"]
        if not content or len(content.strip()) < 30:
            continue

        # Prefix with context for richer embedding
        prefixed = (
            f"[{EXAM_TYPE} | {SUBJECT} | {unit} | {topic} | {section['content_type']}]\n\n"
            f"{content}"
        )

        cur.execute("""
            INSERT INTO public.generated_content (
                id, unit, subject, exam_type, topic,
                content_type, content, difficulty,
                source_file, generated_by, curriculum_chunk_id
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            str(uuid.uuid4()),
            unit, SUBJECT, EXAM_TYPE, topic,
            section["content_type"],
            prefixed,
            section.get("difficulty"),
            filename,
            GEN_BY,
            curr_chunk_id,
        ))
        inserted += 1

    return inserted

# ── ALREADY PROCESSED CHECK ───────────────────────────────────
def already_processed(cur, filename: str) -> bool:
    cur.execute(
        "SELECT COUNT(*) FROM public.generated_content WHERE source_file = %s",
        (filename,)
    )
    return cur.fetchone()[0] > 0

# ── MAIN ──────────────────────────────────────────────────────
def chunk_all():
    md_files = sorted(INPUT_DIR.glob("Unit*.md"))

    print(f"\n{'='*60}")
    print(f"  chunker_generated.py (fixed)")
    print(f"  Input  : {INPUT_DIR}")
    print(f"  Found  : {len(md_files)} .md file(s)")
    print(f"  Target : public.generated_content")
    print(f"{'='*60}\n")

    if not md_files:
        print(f"  No Unit*.md files found")
        return

    conn           = psycopg2.connect(DB_URL)
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
            topics = parse_md_file(md_path)
            print(f"     Topics found: {len(topics)}")

            file_inserted = 0
            for t in topics:
                n = insert_topic(cur, t)
                file_inserted += n
                print(f"     ✓  {t['topic']} — {n} chunks "
                      f"({[s['content_type'] for s in t['sections']]})")

            conn.commit()
            cur.close()
            total_inserted += file_inserted
            print(f"     File total: {file_inserted}")

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
    if fail_count == 0 and total_inserted > 0:
        print(f"\n  Verify:")
        print(f"  SELECT content_type, COUNT(*)")
        print(f"  FROM public.generated_content")
        print(f"  GROUP BY content_type ORDER BY count DESC;")
        print(f"\n  Next: python embedder_generated.py")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    chunk_all()
