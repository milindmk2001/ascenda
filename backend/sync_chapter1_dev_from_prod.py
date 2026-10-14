#!/usr/bin/env python3
"""
Sync Chapter 1 ("Patterns in Mathematics") curriculum_tree subtree + its
visual_lesson_cache rows from Prod (ascenda) into Dev (ascenda-dev),
replacing Dev's current divergent/legacy data for that chapter only.

Confirmed before writing this script:
  - Dev's Chapter 1 node ids are completely different from Prod's (two
    independently-seeded trees), but subject_id/course_id ARE identical
    across both environments, so no FK remapping is needed.
  - Dev's cached visual lessons for this chapter are legacy schema
    (schema_version 1.0) migrated earlier from the old `visual_lessons`
    table — this script replaces them with Prod's current-schema rows.

This is a pure DATA operation (no DDL/schema change). It only touches
rows under Dev's Chapter 1 subtree (id='36f4f8c4-bfe7-4179-a54b-54f0eedc5e91')
and the corresponding Prod subtree (id='9779e634-d519-4f13-ab07-51c25354a1eb').
Nothing else in Dev is touched.

Usage:
    export PROD_DATABASE_URL="postgresql://...ascenda prod pooler url..."
    export DEV_DATABASE_URL="postgresql://...ascenda-dev pooler url..."
    pip install psycopg2-binary --break-system-packages
    python3 sync_chapter1_dev_from_prod.py
        # will print a dry-run summary and ask for confirmation before writing
"""

import os
import sys
import psycopg2
import psycopg2.extras

PROD_CHAPTER1_ID = "9779e634-d519-4f13-ab07-51c25354a1eb"
DEV_CHAPTER1_ID = "36f4f8c4-bfe7-4179-a54b-54f0eedc5e91"

CT_COLUMNS = [
    "id", "subject_id", "course_id", "parent_id", "title", "level",
    "content_type", "created_at", "exam_type", "unit_number",
    "content_id", "is_leaf", "display_order", "prompt_template_id",
]

VLC_COLUMNS = [
    "lesson_id", "curriculum_node_id", "source_chunk_ids", "grade",
    "subject", "book", "chapter", "topic", "concept", "lesson_json",
    "schema_version", "prompt_version", "model_used", "generation_status",
    "validation_status", "created_at", "updated_at", "renderer_version",
]


def fetch_subtree(conn, root_id):
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            """
            WITH RECURSIVE subtree AS (
                SELECT * FROM public.curriculum_tree WHERE id = %s
                UNION ALL
                SELECT ct.* FROM public.curriculum_tree ct
                JOIN subtree s ON ct.parent_id = s.id
            )
            SELECT * FROM subtree ORDER BY level, display_order;
            """,
            (root_id,),
        )
        return [dict(r) for r in cur.fetchall()]


def fetch_visual_lessons(conn, node_ids):
    if not node_ids:
        return []
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM public.visual_lesson_cache WHERE curriculum_node_id = ANY(%s::uuid[]);",
            ([str(n) for n in node_ids],),
        )
        return [dict(r) for r in cur.fetchall()]


def main():
    prod_url = os.environ.get("PROD_DATABASE_URL")
    dev_url = os.environ.get("DEV_DATABASE_URL")
    if not prod_url or not dev_url:
        sys.exit("Set PROD_DATABASE_URL and DEV_DATABASE_URL env vars first.")

    prod_conn = psycopg2.connect(prod_url)
    dev_conn = psycopg2.connect(dev_url)

    try:
        # ---- Read from Prod ----
        prod_rows = fetch_subtree(prod_conn, PROD_CHAPTER1_ID)
        if not prod_rows:
            sys.exit(f"No Chapter 1 subtree found in Prod for id={PROD_CHAPTER1_ID}")
        prod_ids = [r["id"] for r in prod_rows]
        prod_vlc_rows = fetch_visual_lessons(prod_conn, prod_ids)

        # ---- Read Dev's current subtree (what we're about to replace) ----
        dev_rows = fetch_subtree(dev_conn, DEV_CHAPTER1_ID)
        dev_ids = [r["id"] for r in dev_rows]
        dev_vlc_rows = fetch_visual_lessons(dev_conn, dev_ids)

        print("=== DRY RUN SUMMARY ===")
        print(f"Prod Chapter 1 subtree: {len(prod_rows)} curriculum_tree rows, "
              f"{len(prod_vlc_rows)} visual_lesson_cache rows")
        for r in prod_rows:
            print(f"   [PROD] {r['level']}  {r['title']:<30} id={r['id']}")
        print(f"\nDev Chapter 1 subtree (TO BE DELETED): {len(dev_rows)} curriculum_tree rows, "
              f"{len(dev_vlc_rows)} visual_lesson_cache rows")
        for r in dev_rows:
            print(f"   [DEV ] {r['level']}  {r['title']:<30} id={r['id']}")

        confirm = input("\nProceed with replacing Dev's Chapter 1 subtree with Prod's? [yes/N]: ")
        if confirm.strip().lower() != "yes":
            print("Aborted. No changes made.")
            return

        # ---- Write to Dev, single transaction ----
        with dev_conn:
            with dev_conn.cursor() as cur:
                # 1. Delete Dev's old visual_lesson_cache rows for this subtree
                if dev_ids:
                    cur.execute(
                        "DELETE FROM public.visual_lesson_cache WHERE curriculum_node_id = ANY(%s::uuid[]);",
                        ([str(n) for n in dev_ids],),
                    )
                    print(f"Deleted {cur.rowcount} old visual_lesson_cache rows from Dev")

                # 2. Delete Dev's old curriculum_tree rows, children before parent
                child_ids = [r["id"] for r in dev_rows if r["id"] != DEV_CHAPTER1_ID]
                if child_ids:
                    cur.execute(
                        "DELETE FROM public.curriculum_tree WHERE id = ANY(%s::uuid[]);",
                        ([str(n) for n in child_ids],),
                    )
                cur.execute(
                    "DELETE FROM public.curriculum_tree WHERE id = %s;",
                    (DEV_CHAPTER1_ID,),
                )
                print("Deleted Dev's old Chapter 1 curriculum_tree subtree")

                # 3. Insert Prod's curriculum_tree rows, parent first then children
                parent_rows = [r for r in prod_rows if r["id"] == PROD_CHAPTER1_ID]
                child_rows = [r for r in prod_rows if r["id"] != PROD_CHAPTER1_ID]
                col_list = ", ".join(CT_COLUMNS)
                placeholders = ", ".join(["%s"] * len(CT_COLUMNS))
                insert_ct_sql = f"INSERT INTO public.curriculum_tree ({col_list}) VALUES ({placeholders});"
                for r in parent_rows + child_rows:
                    cur.execute(insert_ct_sql, [r[c] for c in CT_COLUMNS])
                print(f"Inserted {len(prod_rows)} curriculum_tree rows from Prod")

                # 4. Insert Prod's visual_lesson_cache rows (same node ids, now valid)
                if prod_vlc_rows:
                    vcol_list = ", ".join(VLC_COLUMNS)
                    vplaceholders = ", ".join(["%s"] * len(VLC_COLUMNS))
                    insert_vlc_sql = f"INSERT INTO public.visual_lesson_cache ({vcol_list}) VALUES ({vplaceholders});"
                    for r in prod_vlc_rows:
                        values = []
                        for c in VLC_COLUMNS:
                            v = r[c]
                            if c == "lesson_json":
                                v = psycopg2.extras.Json(v)
                            values.append(v)
                        cur.execute(insert_vlc_sql, values)
                    print(f"Inserted {len(prod_vlc_rows)} visual_lesson_cache rows from Prod")

        print("\nDone. Dev's Chapter 1 subtree now matches Prod exactly (same IDs, same schema).")

    finally:
        prod_conn.close()
        dev_conn.close()


if __name__ == "__main__":
    main()
