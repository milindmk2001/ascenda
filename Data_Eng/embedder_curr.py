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
EMBED_MODEL = "models/gemini-embedding-2"
OUTPUT_DIMS = 3072
TASK_TYPE   = "RETRIEVAL_DOCUMENT"
SLEEP_SEC   = 0.5

client = genai.Client(api_key=GEMINI_KEY)

# ── EMBED SINGLE TEXT ─────────────────────────────────────────
def embed_text(text: str) -> list[float]:
    response = client.models.embed_content(
        model    = EMBED_MODEL,
        contents = text,
        config   = {
            "task_type":             TASK_TYPE,
            "output_dimensionality": OUTPUT_DIMS,
        },
    )
    return response.embeddings[0].values

# ── FETCH UNEMBEDDED CURRICULUM CHUNKS ───────────────────────
# Only fetches chunks from curriculum_topic strategy
def get_unembedded_chunks(conn, limit: int = 2000) -> list:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT c.id, c.book_id, c.content, c.section_title
        FROM   public.chunks c
        LEFT JOIN public.embeddings e ON e.chunk_id = c.id
        WHERE  e.id IS NULL
          AND  c.chunk_strategy = 'curriculum_topic'
        ORDER  BY c.created_at
        LIMIT  %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    return rows

# ── MAIN ──────────────────────────────────────────────────────
def embed_curriculum():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    total_embedded = 0
    total_failed   = 0

    print(f"\n{'='*60}")
    print(f"  embedder_curr.py — Curriculum Embedder")
    print(f"  Model     : {EMBED_MODEL}")
    print(f"  Dims      : {OUTPUT_DIMS}")
    print(f"  Strategy  : curriculum_topic chunks only")
    print(f"{'='*60}\n")

    while True:
        chunks = get_unembedded_chunks(conn, limit=2000)
        if not chunks:
            print("  ✅ All curriculum chunks embedded.\n")
            break

        print(f"  Found {len(chunks)} unembedded curriculum chunk(s)\n")

        for chunk in tqdm(chunks, desc="  Embedding topics"):
            cur = conn.cursor()
            try:
                vector = embed_text(chunk["content"])

                cur.execute("""
                    INSERT INTO public.embeddings
                        (id, chunk_id, book_id, embedding, model)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (chunk_id) DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    str(chunk["id"]),
                    str(chunk["book_id"]),
                    vector,
                    EMBED_MODEL,
                ))

                conn.commit()
                cur.close()
                total_embedded += 1
                time.sleep(SLEEP_SEC)

            except Exception as e:
                conn.rollback()
                cur.close()
                total_failed += 1
                print(f"\n  ❌ Failed: {chunk.get('section_title','?')} — {e}")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"     Rate limited — waiting 30s...")
                    time.sleep(30)
                continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Curriculum embedding complete")
    print(f"  ✅ Embedded : {total_embedded}")
    print(f"  ❌ Failed   : {total_failed}")
    if total_failed > 0:
        print(f"  Re-run to retry — already done chunks are skipped")
    else:
        print(f"\n  Verify in Supabase:")
        print(f"""  SELECT b.title, COUNT(e.id) AS embedded
  FROM public.books b
  JOIN public.chunks c ON c.book_id = b.id
  JOIN public.embeddings e ON e.chunk_id = c.id
  WHERE c.chunk_strategy = 'curriculum_topic'
  GROUP BY b.title;""")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    embed_curriculum()
