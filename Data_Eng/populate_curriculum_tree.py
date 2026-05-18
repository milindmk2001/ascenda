"""
populate_curriculum_tree.py

Populates public.curriculum_tree for IITJEE Physics from
public.generated_content.

Tree structure per topic:
  level=1  unit node
  level=2  topic node
  level=3  leaf nodes: concept | solved_problems | unsolved_problems | concept_test

subject_id values come from public.exam_subjects (already seeded).
course_id = NULL (courses table empty — Gemini will populate later).
"""

import os
import uuid
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.environ["DATABASE_DIRECT_URL"]

# ── HARDCODED IDs FROM public.exam_subjects ───────────────────
# These are the actual UUIDs from your Supabase exam_subjects table
SUBJECT_IDS = {
    "IITJEE_PHYSICS":   "4ae2ad11-6a55-484e-8050-5b27668c7606",
    "IITJEE_CHEMISTRY": "cb723aae-9c0f-4d69-8d1c-ea9d88703ad8",
    "IITJEE_MATHS":     "97eab215-a05d-41eb-ad83-e182aef22bde",
    "NEET_PHYSICS":     "ba8dda58-d5bf-4c16-9e0f-87d9c065755d",
    "NEET_BIOLOGY":     "85eb0707-137e-4a67-8674-214b372398c3",
    "NEET_CHEMISTRY":   "bdb52926-ed1a-4a8a-9f77-38e5e0e6c9da",
}

# ── LEAF NODE DEFINITIONS ─────────────────────────────────────
# Each topic gets these 4 leaves in this order
LEAF_NODES = [
    {
        "content_type": "concept",
        "title":        "Concept",
        "gc_types":     ["theory", "formulae"],   # pulls from generated_content
        "display_order": 1,
    },
    {
        "content_type": "solved_problems",
        "title":        "Solved Problems",
        "gc_types":     ["worked_example"],
        "display_order": 2,
    },
    {
        "content_type": "unsolved_problems",
        "title":        "Unsolved Problems",
        "gc_types":     ["unsolved_problem"],
        "display_order": 3,
    },
    {
        "content_type": "concept_test",
        "title":        "Concept Test",
        "gc_types":     [],    # no content_id — FastAPI queries questions at runtime
        "display_order": 4,
    },
]

# ── LOAD GENERATED CONTENT GROUPED BY UNIT → TOPIC ───────────
def load_content_map(conn, exam_type: str, subject: str) -> dict:
    """
    Returns:
    {
      "Unit 1 — Units and Measurement": {
        "unit_number": 1,
        "topics": {
          "SI Units and Dimensions": {
            "theory": [content_id, ...],
            "formulae": [content_id, ...],
            "worked_example": [content_id, ...],
            ...
          }
        }
      }
    }
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT id, unit, topic, content_type
        FROM public.generated_content
        WHERE exam_type = %s AND subject = %s
        ORDER BY unit, topic, content_type
    """, (exam_type, subject))
    rows = cur.fetchall()
    cur.close()

    units = {}
    for row in rows:
        unit  = row["unit"]
        topic = row["topic"]
        ctype = row["content_type"]
        cid   = str(row["id"])

        if unit not in units:
            # Extract unit number from "Unit 1 — ..." or "Unit 01 — ..."
            import re
            match = re.search(r'Unit\s*(\d+)', unit, re.IGNORECASE)
            units[unit] = {
                "unit_number": int(match.group(1)) if match else 99,
                "topics": {}
            }

        if topic not in units[unit]["topics"]:
            units[unit]["topics"][topic] = {}

        if ctype not in units[unit]["topics"][topic]:
            units[unit]["topics"][topic][ctype] = []

        units[unit]["topics"][topic][ctype].append(cid)

    return units

# ── INSERT TREE NODES ─────────────────────────────────────────
def populate_tree(
    conn,
    exam_type:  str,
    subject:    str,
    subject_key: str,    # e.g. "IITJEE_PHYSICS"
):
    subject_id = SUBJECT_IDS[subject_key]
    content_map = load_content_map(conn, exam_type, subject)

    # Sort units by unit_number
    sorted_units = sorted(
        content_map.items(),
        key=lambda x: x[1]["unit_number"]
    )

    print(f"\n  Exam     : {exam_type}")
    print(f"  Subject  : {subject}")
    print(f"  Units    : {len(sorted_units)}")
    print(f"  SubjectID: {subject_id}")

    cur = conn.cursor()

    # Check if already populated
    cur.execute("""
        SELECT COUNT(*) FROM public.curriculum_tree
        WHERE exam_type = %s
          AND subject_id = %s
    """, (exam_type, subject_id))
    existing = cur.fetchone()[0]
    if existing > 0:
        print(f"  ⏭  Already populated ({existing} nodes). Skipping.")
        cur.close()
        return 0

    total_nodes = 0

    for unit_name, unit_data in sorted_units:
        unit_number = unit_data["unit_number"]
        topics      = unit_data["topics"]

        # ── Level 1: Unit node ────────────────────────────────
        unit_id = str(uuid.uuid4())
        cur.execute("""
            INSERT INTO public.curriculum_tree (
                id, subject_id, course_id, parent_id,
                title, level, content_type,
                exam_type, unit_number, content_id,
                is_leaf, display_order
            ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            unit_id,
            subject_id,
            None,       # course_id NULL — courses table empty
            None,       # no parent for unit
            unit_name,
            1,
            "unit",
            exam_type,
            unit_number,
            None,
            False,
            unit_number,
        ))
        total_nodes += 1
        print(f"\n    Unit {unit_number:02d}: {unit_name}")

        # Sort topics by their first appearance
        topic_list = list(topics.keys())

        for topic_order, topic_name in enumerate(topic_list, 1):
            topic_content = topics[topic_name]

            # ── Level 2: Topic node ───────────────────────────
            topic_id = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO public.curriculum_tree (
                    id, subject_id, course_id, parent_id,
                    title, level, content_type,
                    exam_type, unit_number, content_id,
                    is_leaf, display_order
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                topic_id,
                subject_id,
                None,
                unit_id,
                topic_name,
                2,
                "topic",
                exam_type,
                unit_number,
                None,
                False,
                topic_order,
            ))
            total_nodes += 1
            print(f"      Topic: {topic_name}")

            # ── Level 3: 4 leaf nodes ─────────────────────────
            for leaf in LEAF_NODES:
                # Find a content_id for this leaf type
                content_id = None
                for gc_type in leaf["gc_types"]:
                    ids = topic_content.get(gc_type, [])
                    if ids:
                        content_id = ids[0]   # first matching chunk
                        break

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
                    subject_id,
                    None,
                    topic_id,
                    leaf["title"],
                    3,
                    leaf["content_type"],
                    exam_type,
                    unit_number,
                    content_id,
                    True,
                    leaf["display_order"],
                ))
                total_nodes += 1
                available = "✓" if content_id else "○"
                print(f"        {available} {leaf['title']}"
                      + (f" → {content_id[:8]}..." if content_id else " → runtime query"))

    conn.commit()
    cur.close()
    print(f"\n  ✅ Inserted {total_nodes} tree nodes")
    return total_nodes

# ── VERIFY QUERY ──────────────────────────────────────────────
def print_verify_sql():
    print("""
  Verify in Supabase:

  SELECT
    level,
    content_type,
    COUNT(*) AS count
  FROM public.curriculum_tree
  WHERE exam_type = 'IITJEE'
  GROUP BY level, content_type
  ORDER BY level, content_type;
""")

# ── MAIN ──────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  populate_curriculum_tree.py")
    print(f"  Populating IITJEE Physics tree")
    print(f"{'='*60}")

    conn = psycopg2.connect(DB_URL)
    conn.autocommit = False

    try:
        total = populate_tree(
            conn,
            exam_type    = "IITJEE",
            subject      = "Physics",
            subject_key  = "IITJEE_PHYSICS",
        )

        print(f"\n{'='*60}")
        print(f"  Done — {total} nodes inserted")
        print_verify_sql()
        print(f"{'='*60}\n")

    except Exception as e:
        conn.rollback()
        print(f"\n  ❌ Failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
