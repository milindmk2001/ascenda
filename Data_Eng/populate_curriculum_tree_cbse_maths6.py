"""
populate_curriculum_tree_cbse_maths6.py

Populates public.curriculum_tree for CBSE Grade 6 Mathematics
(Ganita Prakash 2024) from public.generated_content.

Tree structure:
  level=1  chapter node  (e.g. Chapter 1: Patterns in Mathematics)
  level=2  leaf nodes    (concept | rules | worked_example | practice | common_mistakes | real_life)

Uses regular_subject_id (not exam_subject_id) since CBSE is a school subject.
course_id is set from the confirmed CBSE Maths 6 course.
"""

import os
import uuid
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ["DATABASE_DIRECT_URL"]

# ── CONFIRMED IDs ─────────────────────────────────────────────
REGULAR_SUBJECT_ID = "83ccb181-4c17-44f3-96b5-74682548d7aa"
COURSE_ID          = "f017622e-b6eb-42ce-be4a-be263f3b295d"
EXAM_TYPE          = "CBSE"
SUBJECT            = "Mathematics"

# ── LEAF NODE DEFINITIONS ─────────────────────────────────────
# Each chapter gets these 6 leaves matching the generated content types
LEAF_NODES = [
    {"content_type": "concept",         "title": "Learn",          "gc_type": "concept",         "display_order": 1},
    {"content_type": "rules",           "title": "Rules",          "gc_type": "rules",            "display_order": 2},
    {"content_type": "worked_example",  "title": "Examples",       "gc_type": "worked_example",   "display_order": 3},
    {"content_type": "practice",        "title": "Practice",       "gc_type": "practice",         "display_order": 4},
    {"content_type": "common_mistakes", "title": "Watch Out",      "gc_type": "common_mistakes",  "display_order": 5},
    {"content_type": "real_life",       "title": "Real Life",      "gc_type": "real_life",        "display_order": 6},
]

# ── LOAD GENERATED CONTENT GROUPED BY CHAPTER ────────────────
def load_content_map(conn) -> dict:
    """
    Returns:
    {
      "Chapter 1: Patterns in Mathematics": {
        "chapter_number": 1,
        "content_types": {
          "concept":        [content_id, ...],
          "rules":          [content_id, ...],
          "worked_example": [content_id, ...],
          ...
        }
      }
    }
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, unit, topic, content_type
        FROM public.generated_content
        WHERE exam_type = %s AND subject = %s
        ORDER BY unit, content_type
    """, (EXAM_TYPE, SUBJECT))
    rows = cur.fetchall()
    cur.close()

    import re
    chapters = {}
    for row in rows:
        unit  = row["unit"]   # "Chapter 1: Patterns in Mathematics"
        ctype = row["content_type"]
        cid   = str(row["id"])

        if unit not in chapters:
            match = re.search(r'Chapter\s*(\d+)', unit, re.IGNORECASE)
            chapters[unit] = {
                "chapter_number": int(match.group(1)) if match else 99,
                "content_types":  {}
            }

        if ctype not in chapters[unit]["content_types"]:
            chapters[unit]["content_types"][ctype] = []
        chapters[unit]["content_types"][ctype].append(cid)

    return chapters

# ── MAIN ──────────────────────────────────────────────────────
def main():
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False
    cur  = conn.cursor()

    # Check if already populated
    cur.execute("""
        SELECT COUNT(*) FROM public.curriculum_tree
        WHERE exam_type = %s AND subject_id = %s
    """, (EXAM_TYPE, REGULAR_SUBJECT_ID))
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"  ⚠  Already populated ({existing} nodes). Delete first to re-run.")
        cur.close()
        conn.close()
        return

    content_map = load_content_map(conn)
    sorted_chapters = sorted(
        content_map.items(),
        key=lambda x: x[1]["chapter_number"]
    )

    print(f"\n{'='*60}")
    print(f"  populate_curriculum_tree_cbse_maths6.py")
    print(f"  Subject  : {SUBJECT}")
    print(f"  Exam     : {EXAM_TYPE}")
    print(f"  Chapters : {len(sorted_chapters)}")
    print(f"  SubjectID: {REGULAR_SUBJECT_ID}")
    print(f"  CourseID : {COURSE_ID}")
    print(f"{'='*60}\n")

    total_nodes = 0

    for chapter_name, chapter_data in sorted_chapters:
        chapter_num    = chapter_data["chapter_number"]
        content_types  = chapter_data["content_types"]

        # ── Level 1: Chapter node ─────────────────────────────
        chapter_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO public.curriculum_tree (
                id, subject_id, course_id, parent_id,
                title, level, content_type,
                exam_type, unit_number, content_id,
                is_leaf, display_order
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            chapter_id,
            REGULAR_SUBJECT_ID,
            COURSE_ID,
            None,
            chapter_name,
            1,
            "chapter",
            EXAM_TYPE,
            chapter_num,
            None,
            False,
            chapter_num,
        ))
        total_nodes += 1
        print(f"  Chapter {chapter_num:02d}: {chapter_name}")

        # ── Level 2: 6 leaf nodes ─────────────────────────────
        for leaf in LEAF_NODES:
            ids        = content_types.get(leaf["gc_type"], [])
            content_id = ids[0] if ids else None

            leaf_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO public.curriculum_tree (
                    id, subject_id, course_id, parent_id,
                    title, level, content_type,
                    exam_type, unit_number, content_id,
                    is_leaf, display_order
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                leaf_id,
                REGULAR_SUBJECT_ID,
                COURSE_ID,
                chapter_id,
                leaf["title"],
                2,
                leaf["content_type"],
                EXAM_TYPE,
                chapter_num,
                content_id,
                True,
                leaf["display_order"],
            ))
            total_nodes += 1
            status = "✅" if content_id else "⚠ "
            print(f"    {status} {leaf['title']}"
                  + (f" → {content_id[:8]}..." if content_id else " → no content found"))

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n{'='*60}")
    print(f"  ✅ Inserted {total_nodes} tree nodes")
    print(f"\n  Verify in Supabase:")
    print(f"  SELECT level, content_type, COUNT(*) AS count")
    print(f"  FROM public.curriculum_tree")
    print(f"  WHERE exam_type = 'CBSE'")
    print(f"  GROUP BY level, content_type")
    print(f"  ORDER BY level, content_type;")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
