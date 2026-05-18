"""
embedder_generated.py
Embeds public.generated_content into public.generated_embeddings.
Uses Gemini embedding-2 (3072 dims) — same model as all other embeddings.
"""

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

# ── FETCH UNEMBEDDED GENERATED CONTENT ───────────────────────
def get_unembedded(conn, limit: int = 1000) -> list:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT gc.id, gc.content, gc.content_type,
               gc.unit, gc.topic
        FROM   public.generated_content gc
        LEFT JOIN public.generated_embeddings ge ON ge.content_id = gc.id
        WHERE  ge.id IS NULL
        ORDER  BY gc.created_at
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

    print(f"\n{'='*60}")
    print(f"  embedder_generated.py")
    print(f"  Model  : {EMBED_MODEL}")
    print(f"  Dims   : {OUTPUT_DIMS}")
    print(f"  Source : public.generated_content")
    print(f"  Target : public.generated_embeddings")
    print(f"{'='*60}\n")

    while True:
        rows = get_unembedded(conn, limit=1000)
        if not rows:
            print("  ✅ All generated content embedded.\n")
            break

        print(f"  Found {len(rows)} unembedded rows — processing...\n")

        for row in tqdm(rows, desc="  Embedding"):
            cur = conn.cursor()
            try:
                vector = embed_text(row["content"])

                cur.execute("""
                    INSERT INTO public.generated_embeddings
                        (id, content_id, embedding, model)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (content_id) DO NOTHING
                """, (
                    str(uuid.uuid4()),
                    str(row["id"]),
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
                print(f"\n  ❌ Failed: {row.get('topic','?')} [{row.get('content_type','?')}] — {e}")
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    print(f"     Rate limited — waiting 30s...")
                    time.sleep(30)
                continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Embedding complete")
    print(f"  ✅ Embedded : {total_embedded}")
    print(f"  ❌ Failed   : {total_failed}")
    if total_failed > 0:
        print(f"  Re-run to retry — already done rows are skipped")
    else:
        print(f"\n  Verify in Supabase:")
        print(f"""
  SELECT
    gc.content_type,
    COUNT(gc.id)  AS total,
    COUNT(ge.id)  AS embedded,
    COUNT(gc.id) - COUNT(ge.id) AS missing
  FROM public.generated_content gc
  LEFT JOIN public.generated_embeddings ge ON ge.content_id = gc.id
  GROUP BY gc.content_type
  ORDER BY total DESC;""")
        print(f"\n  Next step: explanation_generator.py (Step 4)")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    embed_all()
