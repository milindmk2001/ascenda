import os
import re
import json
import hashlib
import uuid
import psycopg2
import psycopg2.extras
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL   = os.environ["DATABASE_DIRECT_URL"]
CURR_DIR = Path(r"C:\projects\Data_Engineering\textgen\output\curr_dataset")

# ── HELPERS ───────────────────────────────────────────────────
def get_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def clean_text(text: str) -> str:
    text = text.replace('\x00', '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    return text.strip()

# ── BUILD CHUNK TEXT FROM FLAT TOPIC ITEM ────────────────────
# Each item in the JSON array is one topic — build rich embed text
def build_chunk_text(item: dict) -> str:
    exam       = item.get("exam",       "")
    subject    = item.get("subject",    "")
    unit       = item.get("unit",       "")
    topic      = item.get("topic",      "")
    subtopics  = ", ".join(item.get("subtopics", []))
    concepts   = ", ".join(item.get("concepts",  []))
    content    = clean_text(item.get("content",  ""))
    difficulty = item.get("difficulty", "")
    weightage  = item.get("weightage",  "")

    return f"""[{exam} | {subject} | {unit} | {topic}]

Topic: {topic}
Unit: {unit}
Difficulty: {difficulty} | Weightage: {weightage}
Subtopics: {subtopics}
Key Concepts: {concepts}

{content}""".strip()

# ── LOAD AND VALIDATE JSON FILE ───────────────────────────────
def load_curriculum_json(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list) or len(data) == 0:
        raise ValueError(f"Expected non-empty array in {path.name}")

    # Validate required fields on first item
    required = ["exam", "subject", "unit", "topic"]
    missing  = [k for k in required if k not in data[0]]
    if missing:
        raise ValueError(f"Missing fields {missing} in {path.name}")

    if data[0]["exam"] not in ("IITJEE", "NEET"):
        raise ValueError(f"exam must be IITJEE or NEET, got: {data[0]['exam']}")

    if data[0]["subject"] not in ("Physics", "Chemistry", "Mathematics", "Biology"):
        raise ValueError(f"Invalid subject: {data[0]['subject']}")

    return data

# ── INSERT ONE BOOK ROW PER FILE ─────────────────────────────
def insert_book(cur, exam: str, subject: str, file_name: str,
                file_hash: str, topic_count: int) -> str:
    book_id = str(uuid.uuid4())
    title   = f"{exam} {subject} Curriculum"

    cur.execute("""
        INSERT INTO public.books (
            id, title, authors, license,
            source_url, attribution,
            file_name, file_hash, total_pages,
            curriculum_type, status
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'processing')
        ON CONFLICT (file_hash) DO UPDATE
            SET status = 'processing', updated_at = NOW()
        RETURNING id
    """, (
        book_id,
        title,
        [],
        "internal",
        "",
        f"{exam} Official Curriculum — {subject}",
        file_name,
        file_hash,
        topic_count,
        exam.lower(),
    ))

    returned = cur.fetchone()
    return str(returned[0]) if returned else book_id

# ── BUILD CHUNKS FROM FLAT TOPIC ARRAY ───────────────────────
def build_chunks(items: list[dict], book_id: str) -> list[dict]:
    chunks = []
    for i, item in enumerate(items):
        content = build_chunk_text(item)
        if not content.strip():
            continue

        chunks.append({
            "id":             str(uuid.uuid4()),
            "book_id":        book_id,
            "chunk_index":    i,
            "section_title":  f"{item.get('unit','')} › {item.get('topic','')}",
            "page_start":     i + 1,
            "page_end":       i + 1,
            "content":        content,
            "token_count":    len(content.split()),
            "chunk_strategy": "curriculum_topic",
            "overlap_tokens": 0,
        })
    return chunks

# ── MAIN ──────────────────────────────────────────────────────
def process_all_curriculum():
    json_files = sorted(CURR_DIR.glob("**/*.json"))

    print(f"\n{'='*60}")
    print(f"  chunker_curr.py — Curriculum JSON Chunker")
    print(f"  Structure: flat topic array (one item = one topic)")
    print(f"  Found    : {len(json_files)} JSON file(s)")
    print(f"{'='*60}\n")

    if not json_files:
        print(f"  No JSON files found in {CURR_DIR}")
        return

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    success_count = 0
    skip_count    = 0
    fail_count    = 0

    for json_path in tqdm(json_files, desc="Chunking curriculum files"):
        cur = conn.cursor()
        try:
            items     = load_curriculum_json(json_path)
            file_text = json_path.read_text(encoding="utf-8")
            file_hash = get_text_hash(file_text)
            exam      = items[0]["exam"]
            subject   = items[0]["subject"]

            # Dedup check
            cur.execute(
                "SELECT id, status FROM public.books WHERE file_hash = %s",
                (file_hash,)
            )
            existing = cur.fetchone()
            if existing and existing[1] == "chunked":
                print(f"\n  ⏭  Already chunked: {json_path.name}")
                cur.close()
                skip_count += 1
                continue

            print(f"\n  🔍 {json_path.name}")
            print(f"     Exam: {exam} | Subject: {subject} | Topics: {len(items)}")

            # Insert book row
            book_id = insert_book(
                cur, exam, subject,
                json_path.name, file_hash, len(items)
            )
            conn.commit()

            # Build chunks
            chunks = build_chunks(items, book_id)
            if not chunks:
                print(f"     ⚠  No chunks produced")
                cur.close()
                skip_count += 1
                continue

            # Delete stale chunks
            cur.execute(
                "DELETE FROM public.chunks WHERE book_id = %s",
                (book_id,)
            )

            # Bulk insert
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO public.chunks
                    (id, book_id, chunk_index, section_title,
                     page_start, page_end, content,
                     token_count, chunk_strategy, overlap_tokens)
                VALUES %s
                ON CONFLICT (book_id, chunk_index) DO NOTHING
                """,
                [(
                    c["id"], c["book_id"], c["chunk_index"],
                    c["section_title"], c["page_start"], c["page_end"],
                    c["content"], c["token_count"],
                    c["chunk_strategy"], c["overlap_tokens"],
                ) for c in chunks],
                page_size=200
            )

            # Mark done
            cur.execute(
                "UPDATE public.books SET status='chunked', chunked_at=NOW() WHERE id=%s",
                (book_id,)
            )
            conn.commit()
            cur.close()
            success_count += 1
            print(f"     ✓  {len(chunks)} chunks created")

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
            print(f"\n  ❌ Failed: {json_path.name}")
            print(f"     Error : {e}")
            continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Chunking complete")
    print(f"  ✅ Success : {success_count} files")
    print(f"  ⏭  Skipped : {skip_count} files")
    print(f"  ❌ Failed  : {fail_count} files")
    if fail_count == 0:
        print(f"  Next step : python embedder_curr.py")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    process_all_curriculum()
