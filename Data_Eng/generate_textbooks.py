"""
generate_textbooks.py
Generates IITJEE Physics textbooks — one per unit.

Pipeline:
  1. Load IITJEE Physics curriculum topics from Supabase
  2. For each topic: semantic search textbook chunks + JEE questions
  3. Claude rewrites content aligned to curriculum (NOT raw copy)
  4. Saves one .md file per unit to OUTPUT_DIR

Output: C:/projects/Data_Engineering/textgen/output/generated_textbooks/Physics/
"""

import os
import time
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv
from google import genai
import anthropic

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL          = os.environ["DATABASE_DIRECT_URL"]
GEMINI_KEY      = os.environ["GEMINI_API_KEY"]
ANTHROPIC_KEY   = os.environ["ANTHROPIC_KEY"]
EMBED_MODEL     = "models/gemini-embedding-2"   # must match stored vectors
GEN_MODEL       = "claude-sonnet-4-20250514"    # for rewriting
OUTPUT_DIMS     = 3072
OUTPUT_DIR      = Path(r"C:\projects\Data_Engineering\textgen\output\generated_textbooks\Physics")
SLEEP_GEN       = 2.0    # seconds between Claude calls
SLEEP_EMBED     = 0.3    # seconds between Gemini embed calls

# ── CLIENTS ───────────────────────────────────────────────────
gemini_client    = genai.Client(api_key=GEMINI_KEY)
anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── SETUP ─────────────────────────────────────────────────────
def setup():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── EMBED QUERY (Gemini — must match stored vectors) ──────────
def embed_query(text: str) -> list[float]:
    response = gemini_client.models.embed_content(
        model    = EMBED_MODEL,
        contents = text,
        config   = {
            "task_type":             "RETRIEVAL_QUERY",
            "output_dimensionality": OUTPUT_DIMS,
        },
    )
    time.sleep(SLEEP_EMBED)
    return response.embeddings[0].values

# ── LOAD IITJEE PHYSICS CURRICULUM FROM SUPABASE ─────────────
def load_curriculum(conn) -> list[dict]:
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            c.section_title,
            c.content,
            c.chunk_index
        FROM public.chunks c
        JOIN public.books b ON b.id = c.book_id
        WHERE b.curriculum_type = 'iitjee'
          AND c.chunk_strategy  = 'curriculum_topic'
          AND c.content         LIKE '%| Physics |%'
        ORDER BY c.chunk_index
    """)
    rows = cur.fetchall()
    cur.close()
    return rows

# ── GROUP TOPICS BY UNIT ──────────────────────────────────────
def group_by_unit(topics: list[dict]) -> dict:
    units = {}
    for t in topics:
        parts      = t["section_title"].split(" › ")
        unit_name  = parts[0].strip() if len(parts) > 1 else "General"
        topic_name = parts[1].strip() if len(parts) > 1 else t["section_title"]
        if unit_name not in units:
            units[unit_name] = []
        units[unit_name].append({
            "topic":   topic_name,
            "content": t["content"],
        })
    return units

# ── SEMANTIC SEARCH: TEXTBOOK CHUNKS ─────────────────────────
def search_textbook_chunks(conn, query: str, top_k: int = 6) -> list[dict]:
    vector = embed_query(query)
    cur    = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM match_chunks(%s::vector, %s, NULL, NULL, NULL, 0.25)",
        (vector, top_k)
    )
    results = cur.fetchall()
    cur.close()
    return results

# ── SEMANTIC SEARCH: JEE QUESTIONS ───────────────────────────
def search_questions(conn, query: str, top_k: int = 5) -> list[dict]:
    vector = embed_query(query)
    cur    = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # Adjust exam_type to match what is stored in your questions table
    cur.execute(
        "SELECT * FROM match_questions(%s::vector, %s, 'Physics', NULL, NULL, 0.25)",
        (vector, top_k)
    )
    results = cur.fetchall()
    cur.close()
    return results

# ── BUILD PHYSICS CONTEXT STRING ─────────────────────────────
def build_physics_context(chunks: list, questions: list) -> str:
    ctx = ""

    if chunks:
        ctx += "SOURCE PHYSICS CONTENT (understand and rewrite — do not copy):\n"
        ctx += "─" * 60 + "\n"
        for i, c in enumerate(chunks, 1):
            ctx += f"\n[{c['book_title']} | {c['section_title']} | p.{c['page_start']}]\n"
            ctx += c["content"][:700].strip() + "\n"

    if questions:
        ctx += "\n\nJEE EXAM QUESTIONS ON THIS TOPIC:\n"
        ctx += "─" * 60 + "\n"
        for i, q in enumerate(questions, 1):
            opts = ""
            if q.get("options"):
                for k, v in (q["options"] if isinstance(q["options"], dict)
                             else {}).items():
                    opts += f"  {k}) {v}\n"
            ctx += f"\nJEE {q.get('exam_year','')} | {q.get('difficulty','')} | {q.get('question_type','')}\n"
            ctx += f"Q: {q.get('question_final','')}\n"
            if opts:
                ctx += opts
            ctx += f"Answer: {q.get('correct_answer','')}\n"
            if q.get("explanation"):
                ctx += f"Explanation: {q.get('explanation','')[:500]}\n"
            if q.get("formulae"):
                formulae = q.get("formulae", [])
                if isinstance(formulae, list):
                    ctx += f"Formulae: {', '.join(formulae[:3])}\n"

    return ctx

# ── GENERATE ONE TOPIC SECTION (Claude rewrites from scratch) ─
def generate_topic_section(
    unit_name:          str,
    topic_name:         str,
    curriculum_content: str,
    physics_context:    str
) -> str:
    """
    Claude reads source physics content and JEE questions,
    then writes completely original curriculum-aligned content.
    """

    prompt = f"""You are writing a JEE Physics textbook section.

Your job: Read the source material below to understand the physics.
Then write completely original content aligned to the IITJEE curriculum.
Do NOT reproduce sentences from the source material.
Rewrite everything in your own words, calibrated for JEE preparation.

CURRICULUM CONTEXT:
Unit: {unit_name}
Topic: {topic_name}
Curriculum specification:
{curriculum_content[:600]}

SOURCE MATERIAL (read to understand — do not copy):
{physics_context[:3500]}

Write the following sections:

{topic_name}

THEORY
Write 400-500 words explaining this topic for a JEE student.
Cover every subtopic listed in the curriculum specification.
State physical laws precisely. Include derivations where JEE tests them.
Write in continuous paragraphs like a real textbook.
State all formulae clearly in plain text.

KEY FORMULAE
List every important formula for this topic.
Format: Name: formula (SI units of each quantity)
Include at least 6 formulae or all that are relevant.

SOLVED PROBLEMS

Problem 1 [Easy — JEE Main]
Write a numerical problem testing basic application of the formula.
Use realistic numbers with proper SI units.
Solution:
State which formula is being used.
Show every algebraic and numerical step.
Circle/state the final answer with units.

Problem 2 [Medium — JEE Main]
Write a problem requiring two-step reasoning or concept combination.
Solution:
Full step-by-step working.

Problem 3 [Hard — JEE Advanced]
Write a problem requiring deep conceptual understanding.
MCQ format with 4 options (A B C D).
Solution:
Full working identifying why each wrong option fails.

Problem 4 [Hard — JEE Advanced]
Integer type or multi-correct type problem.
Solution:
Full working.

Problem 5 [Conceptual — JEE Advanced]
A problem testing a common misconception or subtle point.
Solution:
Full working with explanation of the conceptual trap.

UNSOLVED PROBLEMS
Write 8 unsolved problems at varying difficulty.
For each: state the problem clearly, give answer only (no working).

1. [Easy] Problem text. (Answer: ___)
2. [Easy] Problem text. (Answer: ___)
3. [Medium] Problem text. (Answer: ___)
4. [Medium] Problem text. (Answer: ___)
5. [Medium] Problem text. (Answer: ___)
6. [Hard] Problem text. (Answer: ___)
7. [Hard — JEE Advanced] Problem text. (Answer: ___)
8. [Hard — JEE Advanced] Problem text. (Answer: ___)

COMMON EXAM MISTAKES
List 4 specific mistakes students make on JEE for this topic.
Be precise — name the exact error, not generic advice.

Write the complete section now."""

    message = anthropic_client.messages.create(
        model      = GEN_MODEL,
        max_tokens = 4000,
        messages   = [{"role": "user", "content": prompt}]
    )
    return message.content[0].text

# ── GENERATE ONE UNIT FILE ────────────────────────────────────
def generate_unit(
    conn,
    unit_number: int,
    unit_name:   str,
    topics:      list[dict]
) -> Path:
    clean   = "".join(c for c in unit_name.replace(" ", "_") if c.isalnum() or c == "_")
    fname   = f"Unit{unit_number:02d}_{clean[:45]}.md"
    fpath   = OUTPUT_DIR / fname

    print(f"\n  {'='*55}")
    print(f"  Unit {unit_number:02d}: {unit_name}")
    print(f"  Topics : {len(topics)}")
    print(f"  File   : {fname}")
    print(f"  {'='*55}")

    # ── Unit header ───────────────────────────────────────────
    md  = f"# IITJEE Physics — {unit_name}\n\n"
    md += f"Exam: IIT JEE Main and Advanced\n"
    md += f"Subject: Physics\n"
    md += f"Unit {unit_number:02d}: {unit_name}\n"
    md += f"Topics: {len(topics)}\n\n"
    md += "---\n\n"

    # ── Table of contents ─────────────────────────────────────
    md += "CONTENTS\n\n"
    for i, t in enumerate(topics, 1):
        md += f"{i}. {t['topic']}\n"
    md += "\n---\n\n"

    # ── Generate each topic ───────────────────────────────────
    for i, t in enumerate(topics, 1):
        topic = t["topic"]
        print(f"    [{i}/{len(topics)}] {topic}")

        try:
            query   = f"IITJEE Physics {unit_name} {topic}"
            chunks  = search_textbook_chunks(conn, query, top_k=6)
            qns     = search_questions(conn, query, top_k=5)

            print(f"           {len(chunks)} chunks  {len(qns)} questions retrieved")

            context = build_physics_context(chunks, qns)
            section = generate_topic_section(
                unit_name          = unit_name,
                topic_name         = topic,
                curriculum_content = t["content"],
                physics_context    = context,
            )

            md += section + "\n\n---\n\n"
            time.sleep(SLEEP_GEN)

        except Exception as e:
            print(f"           ERROR: {e}")
            md += f"{topic}\n\n[Generation failed: {e}]\n\n---\n\n"
            time.sleep(3)
            continue

    # ── Attribution footer ────────────────────────────────────
    md += "\n\nSOURCES\n\n"
    md += "Generated using content from CC-BY licensed open textbooks:\n\n"
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT DISTINCT title, attribution, license
        FROM public.books
        WHERE curriculum_type IN ('open','supplement')
        ORDER BY title
    """)
    for row in cur.fetchall():
        md += f"  {row['attribution']}\n"
    cur.close()
    md += "\nContent rewritten for IIT JEE preparation. "
    md += "Original sources licensed under CC-BY / CC-BY-SA.\n"

    fpath.write_text(md, encoding="utf-8")
    print(f"    SAVED: {fpath}")
    return fpath

# ── MAIN ──────────────────────────────────────────────────────
def main():
    setup()

    print(f"\n{'='*60}")
    print(f"  IITJEE Physics Textbook Generator")
    print(f"  Embedding : Gemini {EMBED_MODEL}")
    print(f"  Generation: Claude {GEN_MODEL}")
    print(f"  Output    : {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    conn      = psycopg2.connect(DB_URL)
    topics    = load_curriculum(conn)
    units     = group_by_unit(topics)
    unit_list = list(units.items())

    print(f"  Units found: {len(unit_list)}")
    for i, (u, t) in enumerate(unit_list, 1):
        print(f"    {i:02d}. {u}  ({len(t)} topics)")

    generated = []
    failed    = []

    for unit_number, (unit_name, unit_topics) in enumerate(unit_list, 1):
        clean = "".join(c for c in unit_name.replace(" ", "_") if c.isalnum() or c == "_")
        fname = f"Unit{unit_number:02d}_{clean[:45]}.md"
        fpath = OUTPUT_DIR / fname

        # Skip already generated files — safe to re-run
        if fpath.exists():
            print(f"\n  SKIP (exists): {fname}")
            generated.append(fpath)
            continue

        try:
            path = generate_unit(conn, unit_number, unit_name, unit_topics)
            generated.append(path)
        except Exception as e:
            print(f"\n  FAILED: {unit_name} — {e}")
            failed.append(unit_name)

    conn.close()

    print(f"\n{'='*60}")
    print(f"  Done")
    print(f"  Generated : {len(generated)} unit files")
    print(f"  Failed    : {len(failed)}")
    print(f"  Output    : {OUTPUT_DIR}")
    if failed:
        print(f"  Failed units (re-run to retry):")
        for u in failed:
            print(f"    {u}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
