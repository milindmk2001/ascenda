"""
populate_prompt_parameters_cbse_maths6.py

Populates public.prompt_parameters for CBSE Grade 6 Mathematics.
Uses hardcoded parameters per chapter — no Gemini API call needed.
Safe to re-run — skips already-populated leaves.
"""

import os
import psycopg2
import psycopg2.extras
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

DB_URL             = os.environ["DATABASE_DIRECT_URL"]
TEMPLATE_ID        = "bceb2901-d53c-4eb9-ab53-da11fbdf51ce"
REGULAR_SUBJECT_ID = "83ccb181-4c17-44f3-96b5-74682548d7aa"
EXAM_TYPE          = "CBSE"
SUBJECT            = "Mathematics"

# ── HARDCODED PARAMETERS PER CHAPTER ─────────────────────────
CHAPTER_PARAMS = {
    1: {
        "title":           "Chapter 1: Patterns in Mathematics",
        "difficulty":      "Foundational",
        "key_formulae":    ["Triangular number Tn = n x (n+1) / 2", "Square number = n x n", "Cube number = n x n x n", "Powers of 2: 1, 2, 4, 8, 16, ..."],
        "common_mistakes": ["Confusing square numbers with even numbers", "Assuming all patterns must increase", "Confusing the position of a term with its value"],
        "prerequisites":   ["Multiplication tables up to 10", "Basic addition and subtraction", "Skip counting"],
    },
    2: {
        "title":           "Chapter 2: Lines and Angles",
        "difficulty":      "Foundational",
        "key_formulae":    ["Angles on a straight line add up to 180 degrees", "Angles around a point add up to 360 degrees", "Vertically opposite angles are equal", "Right angle = 90 degrees"],
        "common_mistakes": ["Confusing acute and obtuse angles", "Measuring angles from wrong baseline", "Confusing supplementary and complementary angles"],
        "prerequisites":   ["Basic shapes recognition", "Understanding of straight lines and curves", "Concept of a point"],
    },
    3: {
        "title":           "Chapter 3: Number Play",
        "difficulty":      "Developing",
        "key_formulae":    ["Even numbers are divisible by 2", "Odd numbers leave remainder 1 when divided by 2", "Sum of digits test for divisibility by 3 and 9", "Last digit test for divisibility by 2 and 5"],
        "common_mistakes": ["Confusing factors with multiples", "Missing factors when listing factor pairs", "Assuming 1 is a prime number"],
        "prerequisites":   ["Multiplication tables", "Division with remainders", "Concept of factors and multiples"],
    },
    4: {
        "title":           "Chapter 4: Data Handling and Presentation",
        "difficulty":      "Foundational",
        "key_formulae":    ["Mean = Sum of all values / Number of values", "Range = Largest value - Smallest value", "Frequency = number of times a value occurs"],
        "common_mistakes": ["Not tallying frequency correctly", "Confusing mean with median", "Drawing bar graphs with unequal bar widths"],
        "prerequisites":   ["Basic addition and division", "Reading tables and charts", "Counting"],
    },
    5: {
        "title":           "Chapter 5: Prime Time",
        "difficulty":      "Developing",
        "key_formulae":    ["A prime number has exactly 2 factors: 1 and itself", "HCF = Highest Common Factor", "LCM = Lowest Common Multiple", "HCF x LCM = Product of two numbers"],
        "common_mistakes": ["Thinking 1 is a prime number", "Confusing HCF and LCM", "Missing prime factors in factor tree"],
        "prerequisites":   ["Factors and multiples", "Division", "Multiplication tables"],
    },
    6: {
        "title":           "Chapter 6: Perimeter and Area",
        "difficulty":      "Developing",
        "key_formulae":    ["Perimeter of rectangle = 2 x (length + breadth)", "Area of rectangle = length x breadth", "Perimeter of square = 4 x side", "Area of square = side x side"],
        "common_mistakes": ["Confusing perimeter and area", "Using wrong units for area (should be square units)", "Adding only two sides instead of all four for perimeter"],
        "prerequisites":   ["Multiplication", "Understanding of length and measurement", "Basic shapes"],
    },
    7: {
        "title":           "Chapter 7: Fractions",
        "difficulty":      "Developing",
        "key_formulae":    ["Equivalent fractions: a/b = (a x n)/(b x n)", "Adding fractions with same denominator: a/c + b/c = (a+b)/c", "Comparing fractions: cross multiply", "Proper fraction: numerator < denominator"],
        "common_mistakes": ["Adding numerators and denominators separately when adding fractions", "Confusing proper and improper fractions", "Not finding common denominator before adding"],
        "prerequisites":   ["Division", "Multiplication", "Concept of equal parts"],
    },
    8: {
        "title":           "Chapter 8: Playing with Constructions",
        "difficulty":      "Foundational",
        "key_formulae":    ["A circle has infinite lines of symmetry", "Perpendicular bisector divides a line into two equal halves at 90 degrees", "An angle bisector divides an angle into two equal parts"],
        "common_mistakes": ["Not keeping compass width fixed when drawing arcs", "Rough pencil lines causing inaccuracy", "Confusing diameter and radius"],
        "prerequisites":   ["Basic shapes", "Concept of angles", "Using a ruler"],
    },
    9: {
        "title":           "Chapter 9: Symmetry",
        "difficulty":      "Foundational",
        "key_formulae":    ["A square has 4 lines of symmetry", "An equilateral triangle has 3 lines of symmetry", "A circle has infinite lines of symmetry", "A rectangle has 2 lines of symmetry"],
        "common_mistakes": ["Confusing rotational symmetry with reflection symmetry", "Incorrectly drawing lines of symmetry at wrong angles", "Assuming all shapes have symmetry"],
        "prerequisites":   ["Basic 2D shapes", "Concept of reflection", "Angles"],
    },
    10: {
        "title":           "Chapter 10: The Other Side of Zero",
        "difficulty":      "Developing",
        "key_formulae":    ["Negative + Positive: subtract and keep sign of larger", "Adding two negatives: add and keep negative sign", "On number line: right = positive, left = negative", "Opposite of a negative is positive: -(-a) = a"],
        "common_mistakes": ["Confusing subtraction of negatives with addition", "Thinking a larger negative number is greater", "Errors when adding positive and negative integers"],
        "prerequisites":   ["Whole numbers", "Number line", "Basic addition and subtraction"],
    },
}

# ── LOAD CHAPTER LEAF NODES ───────────────────────────────────
def load_chapter_leaves(cur) -> list:
    cur.execute("""
        SELECT id, title, unit_number
        FROM public.curriculum_tree
        WHERE exam_type  = %s AND subject_id = %s AND level = 1
        ORDER BY unit_number
    """, (EXAM_TYPE, REGULAR_SUBJECT_ID))
    chapters = cur.fetchall()

    result = []
    for ch in chapters:
        cur.execute("""
            SELECT id, content_type, title, prompt_template_id AS template_id
            FROM public.curriculum_tree
            WHERE parent_id = %s AND is_leaf = true
            ORDER BY display_order
        """, (str(ch["id"]),))
        leaves = cur.fetchall()
        result.append({
            "chapter_num":   ch["unit_number"] or 0,
            "chapter_title": ch["title"],
            "leaves":        [dict(l) for l in leaves],
        })
    return result

def already_exists(cur, leaf_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM public.prompt_parameters WHERE curriculum_tree_id = %s LIMIT 1",
        (leaf_id,)
    )
    return cur.fetchone() is not None

def insert_leaf(cur, leaf: dict, chapter_title: str, chapter_num: int, params: dict):
    template_id = str(leaf.get("template_id") or TEMPLATE_ID)
    cur.execute("""
        INSERT INTO public.prompt_parameters (
            id, curriculum_tree_id, prompt_template_id,
            topic, unit, exam_type, subject,
            difficulty, weightage,
            key_formulae, common_mistakes, prerequisites,
            top_k_theory, top_k_examples, top_k_questions,
            similarity_threshold
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (curriculum_tree_id, prompt_template_id)
        DO UPDATE SET
            difficulty           = EXCLUDED.difficulty,
            key_formulae         = EXCLUDED.key_formulae,
            common_mistakes      = EXCLUDED.common_mistakes,
            prerequisites        = EXCLUDED.prerequisites
    """, (
        str(uuid4()),
        str(leaf["id"]),
        template_id,
        chapter_title,
        f"Chapter {chapter_num}",
        EXAM_TYPE,
        SUBJECT,
        params["difficulty"],
        "Core",
        params["key_formulae"],
        params["common_mistakes"],
        params["prerequisites"],
        3, 3, 3, 0.25,
    ))

# ── MAIN ──────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  populate_prompt_parameters_cbse_maths6.py")
    print(f"  Mode    : Hardcoded (no API call)")
    print(f"  Target  : public.prompt_parameters")
    print(f"  Subject : CBSE Grade 6 Mathematics")
    print(f"{'='*60}\n")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur  = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    chapters = load_chapter_leaves(cur)
    inserted = skipped = failed = 0

    print(f"  Chapters found: {len(chapters)}\n")

    for ch in chapters:
        num    = ch["chapter_num"]
        title  = ch["chapter_title"]
        leaves = ch["leaves"]
        params = CHAPTER_PARAMS.get(num)

        print(f"  Chapter {num:02d}: {title}")

        if not params:
            print(f"    ⚠  No params defined — skipping")
            continue

        if not leaves:
            print(f"    ⚠  No leaf nodes found")
            continue

        all_exist = all(already_exists(cur, str(l["id"])) for l in leaves)
        if all_exist:
            print(f"    ⏭  Already populated — skipping")
            skipped += 1
            continue

        leaf_count = 0
        for leaf in leaves:
            try:
                insert_leaf(cur, leaf, title, num, params)
                leaf_count += 1
            except Exception as e:
                print(f"    ❌ Failed {leaf['content_type']}: {e}")
                conn.rollback()
                cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                failed += 1
                break

        conn.commit()
        inserted += leaf_count
        print(f"    ✅ {leaf_count} rows — difficulty={params['difficulty']}")

    cur.close()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  ✅ Inserted : {inserted} rows")
    print(f"  ⏭  Skipped  : {skipped} chapters")
    print(f"  ❌ Failed   : {failed} chapters")
    print(f"\n  Verify in Supabase:")
    print(f"  SELECT topic, difficulty, COUNT(*) AS leaves")
    print(f"  FROM public.prompt_parameters")
    print(f"  WHERE exam_type = 'CBSE'")
    print(f"  GROUP BY topic, difficulty ORDER BY topic;")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
