import os
import time
import psycopg2
import psycopg2.extras
import anthropic
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL             = os.environ["DATABASE_DIRECT_URL"]
ANTHROPIC_KEY      = os.environ["ANTHROPIC_KEY"]
COURSE_ID          = "f017622e-b6eb-42ce-be4a-be263f3b295d"
REGULAR_SUBJECT_ID = "83ccb181-4c17-44f3-96b5-74682548d7aa"

OUTPUT_DIR = Path(r"C:\projects\data_sources\school\cbse\grade_6\mathematics\generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CLAUDE_MODEL = "claude-opus-4-6"
SLEEP_SEC    = 2

# ── SYSTEM PROMPT — PART 1 (sections 1-3) ────────────────────
SYSTEM_PROMPT_PART1 = """You are an expert mathematics educator writing a comprehensive teacher's reference guide for CBSE Class 6 Mathematics (Ganita Prakash, 2024 edition).

This content will be used as the primary knowledge source by an AI tutoring system. Write deeply thorough, accurate, and richly detailed reference content.

CONTENT GOALS:
- Cover every concept exhaustively
- Explain the WHY behind every rule, not just the HOW
- Include edge cases, exceptions, and nuances
- Provide multiple representations of each concept
- Use precise mathematical language throughout

SVG DIAGRAM RULES:
- Include 1 to 2 SVG diagrams in these sections where genuinely helpful
- SVG must be self-contained and lightweight. Maximum 50 lines each.
- White background. Colors: #4A90D9 blue, #E86C3A orange, #2ECC71 green, #F5A623 yellow, #9B59B6 purple, #333333 dark text, #777777 light text
- Font: Arial sans-serif 12-14px. No gradients, shadows, or filters.
- ViewBox: "0 0 500 280" or "0 0 600 300"
- Wrap each SVG: ```svg ... ```

Write EXACTLY these 3 sections with EXACTLY these headers:

## CONCEPT EXPLANATION
Thorough conceptual introduction. Define core mathematical objects precisely.
Explain historical/mathematical motivation. Connect to Class 5 prior knowledge and Class 7 future topics.
Use at least 3 progressively complex examples. Include SVG diagram if it aids understanding.
Address common misconceptions upfront.

## KEY RULES AND DEFINITIONS
Complete precise definitions for every key term and rule.
Each definition: (a) simple example, (b) counterexample where relevant.
State every formula with full derivation or justification.
Include boundary conditions and special cases. Include SVG if visual aids precision.

## STEP BY STEP WORKED EXAMPLES
At least 5 fully worked examples from basic to advanced.
Never skip algebraic or arithmetic steps.
Label each: Example 1, Example 2, etc.
State which concept is applied at each step.
After each example write a brief instructive note."""

# ── SYSTEM PROMPT — PART 2 (sections 4-6) ────────────────────
SYSTEM_PROMPT_PART2 = """You are an expert mathematics educator writing a comprehensive teacher's reference guide for CBSE Class 6 Mathematics (Ganita Prakash, 2024 edition).

This content will be used as the primary knowledge source by an AI tutoring system. Write deeply thorough, accurate, and richly detailed reference content.

SVG DIAGRAM RULES:
- Include 1 to 2 SVG diagrams where genuinely helpful
- SVG must be self-contained and lightweight. Maximum 50 lines each.
- White background. Colors: #4A90D9 blue, #E86C3A orange, #2ECC71 green, #F5A623 yellow, #9B59B6 purple, #333333 dark text, #777777 light text
- Font: Arial sans-serif 12-14px. No gradients, shadows, or filters.
- ViewBox: "0 0 500 280" or "0 0 600 300"
- Wrap each SVG: ```svg ... ```

Write EXACTLY these 3 sections with EXACTLY these headers:

## PRACTICE PROBLEMS
8 practice problems with complete worked solutions.
Problems 1-3: Single-concept, straightforward application.
Problems 4-6: Multi-step, requiring synthesis of multiple concepts.
Problems 7-8: Extension problems connecting to real-world contexts or other chapters.
Each problem: full solution, key insight required, common mistakes to avoid.
Vary problem types: numerical, geometric, pattern-based, word problems.

## COMMON CONFUSIONS
5-6 conceptual errors students commonly make.
For each: precisely describe the error, explain WHY students make it,
show a concrete example of the error, then show the correct approach.
Note any notational ambiguities that cause confusion.

## REAL LIFE CONNECTIONS
4-5 detailed real-world applications showing actual mathematical working.
Include: science connections, technology connections, everyday Indian life contexts, cross-curricular links.
For any application involving measurement or data, include an SVG diagram.
Explain how mastery of this chapter enables the real-world application."""

# ── CHAPTER LIST — Ganita Prakash 2024 ───────────────────────
CHAPTERS = [
    {"chapter_number": 1,  "title": "Patterns in Mathematics"},
    {"chapter_number": 2,  "title": "Lines and Angles"},
    {"chapter_number": 3,  "title": "Number Play"},
    {"chapter_number": 4,  "title": "Data Handling and Presentation"},
    {"chapter_number": 5,  "title": "Prime Time"},
    {"chapter_number": 6,  "title": "Perimeter and Area"},
    {"chapter_number": 7,  "title": "Fractions"},
    {"chapter_number": 8,  "title": "Playing with Constructions"},
    {"chapter_number": 9,  "title": "Symmetry"},
    {"chapter_number": 10, "title": "The Other Side of Zero"},
]

# ── GENERATE PART 1 (sections 1-3) ───────────────────────────
def generate_part1(client, chapter_number: int, title: str) -> str:
    response = client.messages.create(
        model      = CLAUDE_MODEL,
        max_tokens = 8000,
        system     = SYSTEM_PROMPT_PART1,
        messages   = [{
            "role": "user",
            "content": f"""Write sections 1-3 of the teacher's reference guide for:

Chapter {chapter_number}: {title}
Textbook: Ganita Prakash — NCERT Class 6 Mathematics (2024 edition)
Grade: 6 | Age group: 11-12 years

Write all 3 sections exhaustively. Be thorough, precise, and comprehensive.
Include SVG diagrams where they genuinely aid understanding."""
        }],
    )
    return response.content[0].text

# ── GENERATE PART 2 (sections 4-6) ───────────────────────────
def generate_part2(client, chapter_number: int, title: str, part1_content: str) -> str:
    response = client.messages.create(
        model      = CLAUDE_MODEL,
        max_tokens = 8000,
        system     = SYSTEM_PROMPT_PART2,
        messages   = [{
            "role": "user",
            "content": f"""Write sections 4-6 of the teacher's reference guide for:

Chapter {chapter_number}: {title}
Textbook: Ganita Prakash — NCERT Class 6 Mathematics (2024 edition)
Grade: 6 | Age group: 11-12 years

For context, here is what was already written in sections 1-3:
---
{part1_content[:3000]}
---

Now write sections 4-6 (PRACTICE PROBLEMS, COMMON CONFUSIONS, REAL LIFE CONNECTIONS).
Be thorough and comprehensive. Include SVG diagrams where relevant."""
        }],
    )
    return response.content[0].text

# ── MARK CHAPTER AS GENERATED IN DB ──────────────────────────
def mark_generated(conn, course_id: str, chapter_number: int):
    cur = conn.cursor()
    cur.execute("""
        UPDATE public.course_chapters
        SET content_generated = true
        WHERE course_id = %s AND chapter_number = %s
    """, (course_id, chapter_number))
    conn.commit()
    cur.close()

# ── MAIN ──────────────────────────────────────────────────────
def main():
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    conn   = psycopg2.connect(DB_URL)

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT chapter_number, title, content_generated
        FROM public.course_chapters
        WHERE course_id = %s
        ORDER BY chapter_number
    """, (COURSE_ID,))
    all_chapters = cur.fetchall()
    cur.close()

    # ── CHANGE THIS LINE TO CONTROL WHICH CHAPTERS RUN ────────
    # Test run — Chapter 1 only:
    # pending = [ch for ch in all_chapters if ch["chapter_number"] == 1]
    # Full run — all chapters:
    pending = [ch for ch in all_chapters if not ch["content_generated"]]

    print(f"\n{'='*60}")
    print(f"  generate_cbse_maths6.py  [Split 2-call mode]")
    print(f"  Model   : {CLAUDE_MODEL}")
    print(f"  Tokens  : 8000 x 2 calls per chapter")
    print(f"  Output  : {OUTPUT_DIR}")
    print(f"  Pending : {len(pending)} chapter(s)")
    print(f"{'='*60}\n")

    generated = 0
    failed    = 0

    for ch in pending:
        num   = ch["chapter_number"]
        title = ch["title"]
        fname = OUTPUT_DIR / f"Ch{num:02d}_{title.replace(' ', '_')}.md"

        if fname.exists():
            print(f"  ⏭  Already exists: {fname.name}")
            mark_generated(conn, COURSE_ID, num)
            generated += 1
            continue

        print(f"  ✍  Chapter {num}: {title}")

        try:
            # Call 1 — sections 1-3
            print(f"     → Part 1 (Concept, Rules, Worked Examples)...")
            part1 = generate_part1(client, num, title)
            time.sleep(SLEEP_SEC)

            # Call 2 — sections 4-6
            print(f"     → Part 2 (Practice, Confusions, Real Life)...")
            part2 = generate_part2(client, num, title, part1)
            time.sleep(SLEEP_SEC)

            # Merge and save
            full_content = part1.strip() + "\n\n" + part2.strip()

            with open(fname, "w", encoding="utf-8") as f:
                f.write(f"# Chapter {num}: {title}\n")
                f.write(f"*Ganita Prakash — NCERT Class 6 Mathematics (2024)*\n\n")
                f.write(full_content)

            mark_generated(conn, COURSE_ID, num)
            generated += 1
            print(f"  ✅ Saved: {fname.name} ({len(full_content):,} chars)")

        except Exception as e:
            failed += 1
            print(f"  ❌ Failed Chapter {num}: {e}")

    conn.close()

    print(f"\n{'='*60}")
    print(f"  ✅ Generated : {generated}")
    print(f"  ❌ Failed    : {failed}")
    print(f"\n  Verify all 6 sections in each file:")
    print(f"  findstr \"^##\" \"Ch01_Patterns_in_Mathematics.md\"")
    print(f"\n  Expected:")
    print(f"  ## CONCEPT EXPLANATION")
    print(f"  ## KEY RULES AND DEFINITIONS")
    print(f"  ## STEP BY STEP WORKED EXAMPLES")
    print(f"  ## PRACTICE PROBLEMS")
    print(f"  ## COMMON CONFUSIONS")
    print(f"  ## REAL LIFE CONNECTIONS")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
