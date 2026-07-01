import os
import re
import uuid
import hashlib
import psycopg2
import psycopg2.extras
import fitz
import tiktoken
from pathlib import Path
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL             = os.environ["DATABASE_DIRECT_URL"]
PDF_DIR            = Path(r"C:\projects\Data_Engineering\sourceData\cbse\maths_6")
REGULAR_SUBJECT_ID = "83ccb181-4c17-44f3-96b5-74682548d7aa"

CHUNK_SIZE    = 800
CHUNK_OVERLAP = 150

# ── TOKENIZER ─────────────────────────────────────────────────
tokenizer = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(tokenizer.encode(text))

def get_file_hash(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

# ── TEXT CLEANING ─────────────────────────────────────────────
def clean_text(text: str) -> str:
    text = text.replace('\x00', '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'-\n(\w)', r'\1', text)
    return text.strip()

# ── HEADING DETECTION ─────────────────────────────────────────
def detect_headings(pdf_path: Path) -> list:
    doc   = fitz.open(str(pdf_path))
    spans = []
    for page_num, page in enumerate(doc):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    text = span["text"].strip()
                    if not text or len(text) < 3:
                        continue
                    spans.append({
                        "text": text,
                        "size": round(span["size"], 1),
                        "bold": "Bold" in span.get("font", ""),
                        "page": page_num + 1,
                    })
    doc.close()
    if not spans:
        return []
    sizes   = sorted(set(s["size"] for s in spans), reverse=True)
    h_sizes = sizes[:3] if len(sizes) >= 3 else sizes
    headings = []
    for s in spans:
        if s["size"] in h_sizes or (s["bold"] and s["size"] > 11):
            level = (h_sizes.index(s["size"]) + 1) if s["size"] in h_sizes else 3
            headings.append({"title": s["text"], "level": level, "page": s["page"]})
    seen, unique = set(), []
    for h in headings:
        key = (h["title"], h["page"])
        if key not in seen:
            seen.add(key)
            unique.append(h)
    return unique

# ── SPLITTER ──────────────────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size      = CHUNK_SIZE,
    chunk_overlap   = CHUNK_OVERLAP,
    length_function = count_tokens,
    separators      = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]
)

def extract_page_range(doc, start: int, end: int) -> str:
    texts = []
    for i in range(start - 1, min(end, len(doc))):
        texts.append(doc[i].get_text())
    return "\n".join(texts)

def split_section(text, book_id, chapter_title, section_title,
                  page_start, page_end, chunk_offset):
    raw    = splitter.split_text(text)
    chunks = []
    for i, content in enumerate(raw):
        content = content.strip()
        if not content or count_tokens(content) < 30:
            continue
        prefixed = f"[{chapter_title} > {section_title}]\n\n{content}"
        chunks.append({
            "id":             str(uuid.uuid4()),
            "book_id":        book_id,
            "chunk_index":    chunk_offset + i,
            "section_title":  f"{chapter_title} › {section_title}",
            "page_start":     page_start,
            "page_end":       page_end,
            "content":        prefixed,
            "token_count":    count_tokens(prefixed),
            "chunk_strategy": "hierarchical",
            "overlap_tokens": CHUNK_OVERLAP,
        })
    return chunks

def chunk_book(pdf_path: Path, book_id: str) -> list:
    doc      = fitz.open(str(pdf_path))
    headings = detect_headings(pdf_path)

    if not headings:
        print(f"    ⚠  No headings — using recursive fallback")
        full_text = clean_text("\n".join(doc[i].get_text() for i in range(len(doc))))
        doc.close()
        raw = splitter.split_text(full_text)
        return [
            {
                "id":             str(uuid.uuid4()),
                "book_id":        book_id,
                "chunk_index":    i,
                "section_title":  "General",
                "page_start":     None,
                "page_end":       None,
                "content":        c.strip(),
                "token_count":    count_tokens(c),
                "chunk_strategy": "recursive_fallback",
                "overlap_tokens": CHUNK_OVERLAP,
            }
            for i, c in enumerate(raw)
            if c.strip() and count_tokens(c) >= 30
        ]

    headings.append({"title": "__END__", "level": 1, "page": len(doc) + 1})
    all_chunks    = []
    chunk_counter = 0
    current_chapter = "Introduction"
    current_section = "Introduction"

    for idx in range(len(headings) - 1):
        h      = headings[idx]
        next_h = headings[idx + 1]
        pg_start = h["page"]
        pg_end   = max(next_h["page"] - 1, pg_start)

        if h["level"] == 1:
            current_chapter = h["title"]
            current_section = h["title"]
        else:
            current_section = h["title"]

        section_text = clean_text(extract_page_range(doc, pg_start, pg_end))
        if not section_text or count_tokens(section_text) < 50:
            continue

        section_chunks = split_section(
            text          = section_text,
            book_id       = book_id,
            chapter_title = current_chapter,
            section_title = current_section,
            page_start    = pg_start,
            page_end      = pg_end,
            chunk_offset  = chunk_counter,
        )
        all_chunks    += section_chunks
        chunk_counter += len(section_chunks)

    doc.close()
    return all_chunks

# ── MAIN ──────────────────────────────────────────────────────
def main():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur = conn.cursor()

    # Fetch all book rows for this subject
    cur.execute("""
        SELECT id, file_name, status
        FROM public.books
        WHERE regular_subject_id = %s
        ORDER BY file_name
    """, (REGULAR_SUBJECT_ID,))
    books = cur.fetchall()
    cur.close()

    print(f"\n{'='*60}")
    print(f"  chunker_cbse_maths6.py")
    print(f"  Chunk size    : {CHUNK_SIZE} tokens")
    print(f"  Chunk overlap : {CHUNK_OVERLAP} tokens")
    print(f"  Books found   : {len(books)}")
    print(f"{'='*60}\n")

    success = skipped = failed = 0

    for book_id, file_name, status in tqdm(books, desc="Chunking"):
        if status == "chunked":
            print(f"\n  ⏭  Already chunked: {file_name}")
            skipped += 1
            continue

        pdf_path = PDF_DIR / file_name
        if not pdf_path.exists():
            print(f"\n  ❌ PDF not found: {pdf_path}")
            failed += 1
            continue

        cur = conn.cursor()
        try:
            # Mark as processing
            cur.execute(
                "UPDATE public.books SET status='processing', updated_at=NOW() WHERE id=%s",
                (book_id,)
            )
            conn.commit()

            # Chunk
            chunks = chunk_book(pdf_path, book_id)
            if not chunks:
                print(f"\n  ⚠  No chunks: {file_name}")
                skipped += 1
                cur.close()
                continue

            # Delete stale chunks (safe re-run)
            cur.execute("DELETE FROM public.chunks WHERE book_id = %s", (book_id,))

            # Bulk insert chunks
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

            # Update file_hash and mark chunked
            file_hash = get_file_hash(pdf_path)
            cur.execute("""
                UPDATE public.books
                SET status='chunked', chunked_at=NOW(),
                    file_hash=%s, updated_at=NOW()
                WHERE id=%s
            """, (file_hash, book_id))

            conn.commit()
            cur.close()
            success += 1
            print(f"\n  ✅ {file_name} → {len(chunks)} chunks")

        except Exception as e:
            conn.rollback()
            cur.close()
            failed += 1
            print(f"\n  ❌ Failed: {file_name}: {e}")

    conn.close()

    print(f"\n{'='*60}")
    print(f"  ✅ Success : {success}")
    print(f"  ⏭  Skipped : {skipped}")
    print(f"  ❌ Failed  : {failed}")
    print(f"\n  Verify in Supabase:")
    print(f"  SELECT b.title, COUNT(ch.id) AS chunks")
    print(f"  FROM public.books b")
    print(f"  LEFT JOIN public.chunks ch ON ch.book_id = b.id")
    print(f"  WHERE b.regular_subject_id = '{REGULAR_SUBJECT_ID}'")
    print(f"  GROUP BY b.title ORDER BY b.title;")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
