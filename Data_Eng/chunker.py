import os
import re
import json
import hashlib
import uuid
import psycopg2
import psycopg2.extras
import fitz
import tiktoken
from pathlib import Path
from tqdm import tqdm
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

load_dotenv()

# ── PATHS & CONFIG ────────────────────────────────────────────
DB_URL        = os.environ["DATABASE_DIRECT_URL"]
PDF_DIR       = Path(r"C:\projects\Data_Engineering\sourceData\openumn\chem")
METADATA_JSON = Path(r"C:\projects\Data_Engineering\book_metadata_chem.json")

# ── UPDATED: 1024 tokens for denser STEM context ─────────────
# gemini-embedding-2 handles longer context better than smaller models
CHUNK_SIZE    = 1024
CHUNK_OVERLAP = 100   # larger overlap at 1024 to preserve cross-boundary context

# Tokenizer — cl100k is closest to Gemini's tokenizer
EMBED_MODEL   = "cl100k_base"

# ── LOAD METADATA JSON ────────────────────────────────────────
if not METADATA_JSON.exists():
    raise FileNotFoundError(
        f"book_metadata.json not found at {METADATA_JSON}\n"
        f"Run scan_metadata.py first."
    )
with open(METADATA_JSON, encoding="utf-8") as f:
    BOOK_METADATA = json.load(f)

# ── TOKENIZER ─────────────────────────────────────────────────
tokenizer = tiktoken.get_encoding(EMBED_MODEL)

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
def detect_headings(pdf_path: Path) -> list[dict]:
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
            headings.append({
                "title": s["text"],
                "level": level,
                "page":  s["page"],
            })

    seen, unique = set(), []
    for h in headings:
        key = (h["title"], h["page"])
        if key not in seen:
            seen.add(key)
            unique.append(h)
    return unique

# ── PAGE RANGE EXTRACTION ─────────────────────────────────────
def extract_page_range(doc: fitz.Document, start: int, end: int) -> str:
    texts = []
    for i in range(start - 1, min(end, len(doc))):
        texts.append(doc[i].get_text())
    return "\n".join(texts)

# ── SPLITTER — updated for 1024 token chunks ──────────────────
splitter = RecursiveCharacterTextSplitter(
    chunk_size      = CHUNK_SIZE,
    chunk_overlap   = CHUNK_OVERLAP,
    length_function = count_tokens,
    separators      = ["\n\n", "\n", ". ", "! ", "? ", " ", ""]
)

# ── SPLIT SECTION INTO CHUNKS ─────────────────────────────────
def split_section(
    text: str, book_id: str,
    chapter_title: str, section_title: str,
    page_start: int, page_end: int,
    chunk_offset: int,
) -> list[dict]:
    raw    = splitter.split_text(text)
    chunks = []
    for i, content in enumerate(raw):
        content = content.strip()
        if not content or count_tokens(content) < 30:
            continue
        # Prefix with chapter/section context — improves retrieval accuracy
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

# ── MAIN CHUNKING LOGIC ───────────────────────────────────────
def chunk_book(pdf_path: Path, book_id: str) -> list[dict]:
    doc      = fitz.open(str(pdf_path))
    headings = detect_headings(pdf_path)

    # ── FALLBACK ──────────────────────────────────────────────
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

    # ── HIERARCHICAL ──────────────────────────────────────────
    headings.append({"title": "__END__", "level": 1, "page": len(doc) + 1})

    all_chunks      = []
    chunk_counter   = 0
    current_chapter = "Introduction"
    current_section = "Introduction"

    for idx in range(len(headings) - 1):
        h        = headings[idx]
        next_h   = headings[idx + 1]
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

# ── DATABASE PIPELINE ─────────────────────────────────────────
def process_all_pdfs():
    pdf_files = sorted(PDF_DIR.glob("**/*.pdf"))
    print(f"\n{'='*60}")
    print(f"  chunker.py")
    print(f"  Chunk size    : {CHUNK_SIZE} tokens")
    print(f"  Chunk overlap : {CHUNK_OVERLAP} tokens")
    print(f"  Found         : {len(pdf_files)} PDF(s)")
    print(f"  Metadata      : {len(BOOK_METADATA)} book(s)")
    print(f"{'='*60}\n")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    success_count = 0
    skip_count    = 0
    fail_count    = 0

    for pdf_path in tqdm(pdf_files, desc="Chunking PDFs"):
        cur = conn.cursor()
        try:
            # ── 1. Dedup check ─────────────────────────────────
            file_hash = get_file_hash(pdf_path)
            cur.execute(
                "SELECT id, status FROM public.books WHERE file_hash = %s",
                (file_hash,)
            )
            existing = cur.fetchone()
            if existing and existing[1] == "chunked":
                print(f"\n  ⏭  Already chunked: {pdf_path.name}")
                cur.close()
                skip_count += 1
                continue

            # ── 2. Metadata & page count ───────────────────────
            meta     = BOOK_METADATA.get(pdf_path.name, {})
            book_id  = str(uuid.uuid4())
            doc_temp = fitz.open(str(pdf_path))
            n_pages  = len(doc_temp)
            doc_temp.close()

            # ── 3. Upsert book row ─────────────────────────────
            cur.execute("""
                INSERT INTO public.books (
                    id, title, authors, license,
                    source_url, attribution,
                    file_name, file_hash, total_pages,
                    curriculum_type, status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'processing')
                ON CONFLICT (file_hash) DO UPDATE
                    SET status     = 'processing',
                        updated_at = NOW()
                RETURNING id
            """, (
                book_id,
                meta.get("title", pdf_path.stem.replace("_", " ").title()),
                meta.get("authors", []),
                meta.get("license", "CC-BY-4.0"),
                meta.get("source_url", ""),
                meta.get("attribution", ""),
                pdf_path.name,
                file_hash,
                n_pages,
                meta.get("curriculum_type", "open"),
            ))

            returned = cur.fetchone()
            if returned:
                book_id = str(returned[0])

            conn.commit()

            # ── 4. Chunk ───────────────────────────────────────
            chunks = chunk_book(pdf_path, book_id)

            if not chunks:
                print(f"\n  ⚠  No chunks for {pdf_path.name} — skipping")
                cur.close()
                skip_count += 1
                continue

            # ── 5. Delete stale chunks (safe re-run) ───────────
            cur.execute("DELETE FROM public.chunks WHERE book_id = %s", (book_id,))

            # ── 6. Bulk insert ─────────────────────────────────
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

            # ── 7. Mark done ───────────────────────────────────
            cur.execute("""
                UPDATE public.books
                SET status = 'chunked', chunked_at = NOW()
                WHERE id = %s
            """, (book_id,))

            conn.commit()
            cur.close()
            success_count += 1

            strategy = chunks[0]["chunk_strategy"] if chunks else "n/a"
            print(f"\n  ✓  {pdf_path.name}")
            print(f"     Pages: {n_pages}  |  Chunks: {len(chunks)}  |  Strategy: {strategy}")

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
            print(f"\n  ❌ Failed: {pdf_path.name}")
            print(f"     Error : {e}")
            continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Chunking complete")
    print(f"  ✅ Success : {success_count}")
    print(f"  ⏭  Skipped : {skip_count}")
    print(f"  ❌ Failed  : {fail_count}")
    if fail_count == 0:
        print(f"  Next step : python embedder.py")
    else:
        print(f"  Fix errors then re-run — done PDFs are skipped automatically")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    process_all_pdfs()
