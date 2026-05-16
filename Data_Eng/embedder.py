import os
import time
import uuid
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from google import genai
from tqdm import tqdm

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL      = os.environ["DATABASE_DIRECT_URL"]
GEMINI_KEY  = os.environ["GEMINI_API_KEY"]

# Gemini Embedding 2 — 3072 dims, unified text+diagram space
EMBED_MODEL = "models/gemini-embedding-2"
OUTPUT_DIMS = 3072      # full quality — paid tier, no index limit concern
TASK_TYPE   = "RETRIEVAL_DOCUMENT"

# Paid tier — much higher rate limits, larger batches safe
BATCH_SIZE  = 20        # paid tier supports larger batches
SLEEP_SEC   = 0.5       # minimal sleep — paid tier has high RPM

client = genai.Client(api_key=GEMINI_KEY)

# ── EMBED ONE BATCH ───────────────────────────────────────────
def embed_batch(texts: list[str]) -> list[list[float]]:
    vectors = []
    for text in texts:
        response = client.models.embed_content(
            model    = EMBED_MODEL,
            contents = text,       # ← single string, not a list
            config   = {
                "task_type":             TASK_TYPE,
                "output_dimensionality": OUTPUT_DIMS,
            },
        )
        vectors.append(response.embeddings[0].values)
    return vectors

# ── FETCH UNEMBEDDED CHUNKS ───────────────────────────────────
def get_unembedded_chunks(conn, limit: int = 2000) -> list:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT c.id, c.book_id, c.content
        FROM   public.chunks c
        LEFT JOIN public.embeddings e ON e.chunk_id = c.id
        WHERE  e.id IS NULL
        ORDER  BY c.created_at
        LIMIT  %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    return rows

# ── MAIN ──────────────────────────────────────────────────────
def embed_all():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    total_embedded = 0
    total_failed   = 0
    batch_num      = 0

    print(f"\n{'='*60}")
    print(f"  Embedder — Gemini Paid Tier")
    print(f"  Model     : {EMBED_MODEL}")
    print(f"  Dims      : {OUTPUT_DIMS}")
    print(f"  Task type : {TASK_TYPE}")
    print(f"  Batch size: {BATCH_SIZE}")
    print(f"  Note      : No daily quota limits on paid tier")
    print(f"{'='*60}\n")

    while True:
        chunks = get_unembedded_chunks(conn, limit=2000)
        if not chunks:
            print("  ✅ All chunks embedded.\n")
            break

        print(f"  Found {len(chunks)} unembedded chunk(s) — processing...\n")

        for i in tqdm(range(0, len(chunks), BATCH_SIZE), desc="  Embedding batches"):
            batch     = chunks[i : i + BATCH_SIZE]
            texts     = [c["content"] for c in batch]
            batch_num += 1

            try:
                vectors = embed_batch(texts)

                rows = [
                    (
                        str(uuid.uuid4()),
                        str(batch[j]["id"]),
                        str(batch[j]["book_id"]),
                        vectors[j],
                        EMBED_MODEL,
                    )
                    for j in range(len(batch))
                ]

                cur = conn.cursor()
                psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO public.embeddings
                        (id, chunk_id, book_id, embedding, model)
                    VALUES %s
                    ON CONFLICT (chunk_id) DO NOTHING
                    """,
                    rows,
                    page_size=100
                )
                conn.commit()
                cur.close()

                total_embedded += len(rows)
                time.sleep(SLEEP_SEC)

            except Exception as e:
                error_msg = str(e)
                print(f"\n  ❌ Batch {batch_num} failed: {error_msg}")
                total_failed += len(batch)

                try:
                    conn.rollback()
                except Exception:
                    pass

                # Rate limited — wait and retry
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    wait = 30
                    print(f"     Rate limited — waiting {wait}s (paid tier limit)...")
                    time.sleep(wait)
                else:
                    time.sleep(2)
                continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Embedding complete")
    print(f"  ✅ Embedded : {total_embedded}")
    print(f"  ❌ Failed   : {total_failed}")
    if total_failed > 0:
        print(f"  Re-run embedder.py — already embedded chunks are skipped")
    else:
        print(f"\n  Pipeline complete:")
        print(f"  books → chunks → embeddings ✅")
        print(f"  Model: {EMBED_MODEL} ({OUTPUT_DIMS} dims)")
        print(f"\n  Next: test with python test_search.py")
        print(f"        then connect FastAPI /api/search")
    print(f"{'='*60}\n")

    # Verification reminder
    print("  Verify in Supabase SQL Editor:")
    print("  SELECT COUNT(*) FROM public.embeddings;")
    print(f"  Expected: all chunks from public.chunks\n")

if __name__ == "__main__":
    embed_all()
