import os
import json
import time
import uuid
import psycopg2
import psycopg2.extras
from pathlib import Path
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

# Only process this file — skip the report file
JSON_DIR    = Path(r"C:\projects\Data_Engineering\textgen\output\final_dataset")
TARGET_FILE = "final_dataset.json"

client = genai.Client(api_key=GEMINI_KEY)

# ── BUILD RICH EMBED TEXT ─────────────────────────────────────
# Combines all meaningful fields into one string for embedding.
# More context = better semantic retrieval.
def build_embed_text(record: dict) -> str:
    c   = record.get("classification", {})
    q   = record.get("question", {})
    opt = record.get("options", {})
    sol = record.get("solution", {})

    topics    = ", ".join(c.get("topic", []))
    subtopics = ", ".join(c.get("sub_topic", []))
    concepts  = ", ".join(c.get("concepts", []))
    options   = "\n".join([f"{k}: {v}" for k, v in opt.items()])
    formulae  = "\n".join(sol.get("formulae", []))
    steps     = "\n".join(sol.get("solution_steps", []))

    return f"""[{c.get('subject','')} | {c.get('unit','')} | {topics}]

Question: {q.get('final', q.get('raw', ''))}

Options:
{options}

Subtopics: {subtopics}
Concepts: {concepts}

Solution:
{sol.get('explanation', '')}

Steps:
{steps}

Formulae:
{formulae}""".strip()

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

# ── LOAD JSON ─────────────────────────────────────────────────
def load_questions() -> list[dict]:
    path = JSON_DIR / TARGET_FILE
    if not path.exists():
        raise FileNotFoundError(f"Not found: {path}")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    print(f"  Loaded {len(data)} questions from {TARGET_FILE}")
    return data

# ── CHECK ALREADY PROCESSED ───────────────────────────────────
def get_existing_ids(conn) -> set:
    cur = conn.cursor()
    cur.execute("SELECT id FROM public.questions")
    ids = {str(row[0]) for row in cur.fetchall()}
    cur.close()
    return ids

# ── INSERT QUESTION ROW ───────────────────────────────────────
def insert_question(cur, record: dict, embed_text_val: str):
    c   = record.get("classification", {})
    q   = record.get("question", {})
    sol = record.get("solution", {})
    ex  = record.get("exam", {})
    ans = record.get("answer", {})

    cur.execute("""
        INSERT INTO public.questions (
            id, exam_type, exam_year, exam_paper, source_file,
            subject, unit, topics, sub_topics, concepts,
            difficulty, difficulty_score, question_type,
            question_raw, question_final,
            options, correct_answer,
            explanation, solution_steps, formulae,
            embed_text
        ) VALUES (
            %s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,
            %s,%s,%s,
            %s,%s,
            %s,%s,
            %s,%s,%s,
            %s
        )
        ON CONFLICT (id) DO NOTHING
    """, (
        record["id"],
        ex.get("type"),
        ex.get("year"),
        ex.get("paper"),
        ex.get("source_file"),
        c.get("subject"),
        c.get("unit"),
        c.get("topic", []),
        c.get("sub_topic", []),
        c.get("concepts", []),
        c.get("difficulty"),
        c.get("difficulty_score"),
        c.get("question_type"),
        q.get("raw"),
        q.get("final"),
        json.dumps(record.get("options", {})),
        ans.get("correct_answer"),
        sol.get("explanation"),
        sol.get("solution_steps", []),
        sol.get("formulae", []),
        embed_text_val,
    ))

# ── MAIN ──────────────────────────────────────────────────────
def embed_questions():
    questions = load_questions()

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False

    # Find already-processed questions
    existing_ids = get_existing_ids(conn)
    pending = [q for q in questions if q["id"] not in existing_ids]

    print(f"  Total questions : {len(questions)}")
    print(f"  Already done    : {len(existing_ids)}")
    print(f"  To process      : {len(pending)}\n")

    if not pending:
        print("  ✅ All questions already embedded.")
        conn.close()
        return

    total_embedded = 0
    total_failed   = 0

    print(f"\n{'='*60}")
    print(f"  Question Embedder")
    print(f"  Model     : {EMBED_MODEL}")
    print(f"  Dims      : {OUTPUT_DIMS}")
    print(f"  Questions : {len(pending)}")
    print(f"{'='*60}\n")

    for record in tqdm(pending, desc="  Embedding questions"):
        cur = conn.cursor()
        try:
            # Build rich text for embedding
            embed_text_val = build_embed_text(record)

            # Insert question metadata
            insert_question(cur, record, embed_text_val)

            # Get embedding
            vector = embed_text(embed_text_val)

            # Insert embedding
            cur.execute("""
                INSERT INTO public.question_embeddings
                    (id, question_id, embedding, model)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (question_id) DO NOTHING
            """, (
                str(uuid.uuid4()),
                record["id"],
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
            print(f"\n  ❌ Failed: {record.get('id','?')} — {e}")
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"     Rate limited — waiting 30s...")
                time.sleep(30)
            continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Question embedding complete")
    print(f"  ✅ Embedded : {total_embedded}")
    print(f"  ❌ Failed   : {total_failed}")
    if total_failed > 0:
        print(f"  Re-run to retry failed questions — done ones are skipped")
    else:
        print(f"\n  Verify in Supabase:")
        print(f"  SELECT COUNT(*) FROM public.questions;        -- expect 477")
        print(f"  SELECT COUNT(*) FROM public.question_embeddings; -- expect 477")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    embed_questions()
