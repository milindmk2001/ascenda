"""
generate_visual_lesson.py

Generates visual lesson JSON for ALL CBSE curriculum leaf nodes.
Loops over curriculum_tree dynamically — no hardcoding of chapter numbers.
Skips nodes that already have a complete lesson in visual_lesson_cache.
Safe to re-run — idempotent.
"""

import os
import re
import json
import uuid
import time
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# ── CONFIG ────────────────────────────────────────────────────
DB_URL             = os.environ["DATABASE_DIRECT_URL"]
GEMINI_KEY         = os.environ["GEMINI_API_KEY"]
GEN_MODEL          = "gemini-2.5-flash"
REGULAR_SUBJECT_ID = "83ccb181-4c17-44f3-96b5-74682548d7aa"
COURSE_ID          = "f017622e-b6eb-42ce-be4a-be263f3b295d"
MD_DIR             = Path(r"C:\projects\data_sources\school\cbse\grade_6\mathematics\generated")
SLEEP_BETWEEN      = 2   # seconds between API calls

client = genai.Client(api_key=GEMINI_KEY)

# ── PROMPT — lesson structure (no SVG) ───────────────────────
PROMPT_STRUCTURE = """You are an educational content designer for an AI tutoring platform for Grade 6 students in India.

Generate a visual lesson structure. Return ONLY valid JSON with exactly this structure:
{
  "schemaVersion": "1.0",
  "lessonId": "ch1-patterns-concept",
  "initialScene": "s1",
  "metadata": {
    "subject": "Mathematics",
    "grade": 6,
    "book": "Ganita Prakash",
    "chapter": "Chapter 1: Patterns in Mathematics",
    "topic": "topic name",
    "concept": "concept name"
  },
  "learningObjectives": ["objective 1", "objective 2", "objective 3"],
  "prerequisites": {
    "curriculumNodes": [],
    "conceptsRequired": ["concept 1", "concept 2"],
    "enforcementMode": "warn"
  },
  "assessmentPolicy": {
    "mode": "formative",
    "passMark": 0.7,
    "scoreMethod": "correct_answers_ratio",
    "requireAllSlides": true,
    "allowRetry": true,
    "maxRetries": 3
  },
  "masteryCriteria": {
    "minimumScore": 0.7,
    "minimumSlidesViewed": 3,
    "requiredInteractions": ["answered_question"],
    "awardBadge": false,
    "unlocks": []
  },
  "interactionPolicy": {
    "onCorrect": "reveal_answer",
    "onWrong": "show_hint",
    "onStudentQuestion": "call_tutor_router",
    "onSlideComplete": "follow_transition",
    "onLessonComplete": "show_summary",
    "allowSkip": false,
    "allowReplay": true,
    "maxHintsPerSlide": 2
  },
  "slides": [
    {
      "slideId": "s1",
      "slideIndex": 0,
      "sceneType": "animated_explanation",
      "title": "slide title max 6 words",
      "learningObjective": "one sentence what student will understand",
      "narration": "2-3 warm spoken sentences using Indian examples",
      "visualSpec": {
        "visualType": "number_sequence",
        "sequence": [5, 10, 15, 20, 25],
        "rule": "+5",
        "ruleType": "additive",
        "showQuestionMark": false
      },
      "animationTimeline": [
        {"action": "fadeIn",    "target": "term_0",     "duration": 400},
        {"action": "drawArrow", "target": "arrow_0",    "duration": 300},
        {"action": "reveal",    "target": "term_1",     "duration": 400},
        {"action": "highlight", "target": "rule_label", "duration": 600}
      ],
      "transitions": {
        "animation_complete": "s1_question",
        "student_question":   "tutor_router",
        "replay_requested":   "s1"
      }
    },
    {
      "slideId": "s1_question",
      "slideIndex": 1,
      "sceneType": "student_response",
      "question": "question text",
      "answer": "correct answer as string",
      "hint": "one helpful hint",
      "misconception": "common error students make",
      "visualSpec": {
        "visualType": "number_sequence",
        "sequence": [5, 10, 15, 20, 25],
        "rule": "+5",
        "ruleType": "additive",
        "showQuestionMark": true
      },
      "transitions": {
        "student_correct":  "s2",
        "student_wrong":    "s1_hint",
        "student_question": "tutor_router",
        "max_attempts":     "s1_reveal"
      }
    },
    {
      "slideId": "s1_hint",
      "slideIndex": 2,
      "sceneType": "hint_delivery",
      "narration": "gentle re-explanation with Indian example",
      "transitions": {
        "animation_complete": "s1_question",
        "student_question":   "tutor_router"
      }
    }
  ]
}

STRICT RULES:
- sceneType: animated_explanation | student_response | hint_delivery | tutor_response | lesson_summary
- animationTimeline actions: fadeIn | show | hide | highlight | pulse | reveal | zoomTo | drawArrow
- transition targets must match slideId values in the slides array OR be: tutor_router
- visualType: number_sequence | number_line | fraction_strip | geometry_construct | data_bar_chart | symmetry_grid | area_grid | factor_tree
- narration: warm, simple, Indian examples (mangoes, cricket, rupees, Diwali)
- Return ONLY the JSON object. No markdown. No explanation."""

# ── SVG BUILDER — from visualSpec ────────────────────────────
def build_svg_from_spec(visual_spec: dict, slide_index: int) -> str:
    visual_type = visual_spec.get("visualType", "number_sequence")
    if visual_type == "number_sequence":
        return build_number_sequence_svg(visual_spec, slide_index)
    else:
        # Fallback for other visual types
        return build_placeholder_svg(visual_type, slide_index)

def build_number_sequence_svg(spec: dict, idx: int) -> str:
    sequence      = spec.get("sequence", [])
    rule          = spec.get("rule", "")
    show_question = spec.get("showQuestionMark", False)
    colors        = ["#4A90D9","#E86C3A","#2ECC71","#F5A623","#9B59B6"]
    cx_start, cy, r = 60, 130, 24
    spacing       = min(90, (380 - 60) // max(len(sequence), 1))
    elements      = []

    elements.append(
        '<text x="240" y="35" text-anchor="middle" font-family="Arial" '
        'font-size="15" font-weight="bold" fill="#333333">Number Pattern</text>'
    )
    elements.append(
        f'<rect id="rule_label" x="360" y="18" width="100" height="28" '
        f'rx="6" fill="#9B59B6"/>'
    )
    elements.append(
        f'<text x="410" y="37" text-anchor="middle" font-family="Arial" '
        f'font-size="14" fill="white">Rule: {rule}</text>'
    )

    for i, num in enumerate(sequence):
        cx    = cx_start + i * spacing
        color = colors[i % len(colors)]
        elements.append(
            f'<circle id="term_{i}" cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
        )
        elements.append(
            f'<text x="{cx}" y="{cy+5}" text-anchor="middle" '
            f'font-family="Arial" font-size="16" font-weight="bold" '
            f'fill="white">{num}</text>'
        )
        if i < len(sequence) - 1:
            cx_next = cx_start + (i+1) * spacing
            x1, x2 = cx + r + 4, cx_next - r - 4
            xmid   = (x1 + x2) // 2
            elements.append(
                f'<line id="arrow_{i}" x1="{x1}" y1="{cy}" x2="{x2}" y2="{cy}" '
                f'stroke="#333333" stroke-width="2" marker-end="url(#ah)"/>'
            )
            elements.append(
                f'<text x="{xmid}" y="{cy-10}" text-anchor="middle" '
                f'font-family="Arial" font-size="12" fill="#E86C3A">{rule}</text>'
            )

    if show_question:
        qcx = cx_start + len(sequence) * spacing
        if qcx < 460:
            elements.append(
                f'<circle id="question_mark" cx="{qcx}" cy="{cy}" r="{r}" '
                f'fill="#eeeeee" stroke="#333333" stroke-width="2" stroke-dasharray="4"/>'
            )
            elements.append(
                f'<text x="{qcx}" y="{cy+5}" text-anchor="middle" '
                f'font-family="Arial" font-size="20" fill="#333333">?</text>'
            )

    elements.append(
        '<text x="240" y="230" text-anchor="middle" font-family="Arial" '
        'font-size="13" fill="#777777">What comes next?</text>'
    )

    inner = "\n  ".join(elements)
    return f'''<svg viewBox="0 0 480 260" xmlns="http://www.w3.org/2000/svg">
  <rect width="480" height="260" fill="white"/>
  <defs>
    <marker id="ah" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#333333"/>
    </marker>
  </defs>
  {inner}
</svg>'''

def build_placeholder_svg(visual_type: str, idx: int) -> str:
    return (
        f'<svg viewBox="0 0 480 260" xmlns="http://www.w3.org/2000/svg">'
        f'<rect width="480" height="260" fill="white"/>'
        f'<rect x="40" y="40" width="400" height="180" rx="8" '
        f'fill="#f0f4ff" stroke="#4A90D9" stroke-width="1.5"/>'
        f'<text x="240" y="125" text-anchor="middle" font-family="Arial" '
        f'font-size="15" fill="#4A90D9">{visual_type}</text>'
        f'<text x="240" y="150" text-anchor="middle" font-family="Arial" '
        f'font-size="12" fill="#777777">Visual coming soon</text>'
        f'</svg>'
    )

# ── FETCH HELPERS ─────────────────────────────────────────────
def fetch_generated_content(conn, node: dict) -> str:
    """Fetch generated content for this node's content_type and chapter."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT content FROM public.generated_content
        WHERE exam_type    = 'CBSE'
        AND   subject      = 'Mathematics'
        AND   content_type = %s
        AND   unit         ILIKE %s
        LIMIT 1
    """, (node["content_type"], f"%Chapter {node['unit_number']}%"))
    row = cur.fetchone()
    cur.close()
    return row["content"][:3000] if row else ""

def fetch_source_chunks(conn, unit_number: int, limit: int = 5) -> list:
    """Fetch source PDF chunks for this chapter."""
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT ch.id, ch.content
        FROM public.chunks ch
        JOIN public.books b ON b.id = ch.book_id
        WHERE b.regular_subject_id = %s
        AND   ch.section_title ILIKE %s
        ORDER BY ch.chunk_index
        LIMIT %s
    """, (REGULAR_SUBJECT_ID, f"%Chapter {unit_number}%", limit))
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]

def load_md_section(unit_number: int, content_type: str) -> str:
    """Load relevant section from teacher reference .md file."""
    files = list(MD_DIR.glob(f"Ch{unit_number:02d}_*.md"))
    if not files:
        return ""
    text = files[0].read_text(encoding="utf-8")

    section_map = {
        "concept":        "## CONCEPT EXPLANATION",
        "rules":          "## KEY RULES AND DEFINITIONS",
        "worked_example": "## STEP BY STEP WORKED EXAMPLES",
        "practice":       "## PRACTICE PROBLEMS",
        "common_mistakes":"## COMMON CONFUSIONS",
        "real_life":      "## REAL LIFE CONNECTIONS",
    }
    header = section_map.get(content_type, "## CONCEPT EXPLANATION")
    match  = re.search(
        rf'{re.escape(header)}\s*(.*?)(?=^## |\Z)',
        text, re.DOTALL | re.MULTILINE
    )
    return match.group(1).strip()[:2000] if match else text[:2000]

# ── GEMINI CALL ───────────────────────────────────────────────
def call_gemini_json(prompt: str) -> dict:
    response = client.models.generate_content(
        model    = GEN_MODEL,
        contents = prompt,
        config   = types.GenerateContentConfig(
            system_instruction = PROMPT_STRUCTURE,
            response_mime_type = "application/json",
            temperature        = 0.2,
            max_output_tokens  = 3000,
        )
    )
    raw = response.text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw.strip())

# ── INSERT TO DB ──────────────────────────────────────────────
def insert_lesson(conn, lesson_json: dict, node: dict,
                  source_chunk_ids: list) -> str:
    lesson_id      = str(uuid.uuid4())
    uuid_array_str = '{' + ','.join(str(c) for c in source_chunk_ids) + '}'

    cur = conn.cursor()
    cur.execute("""
        INSERT INTO public.visual_lesson_cache (
            lesson_id, curriculum_node_id, source_chunk_ids,
            grade, subject, book, chapter, topic, concept,
            lesson_json, schema_version, prompt_version,
            model_used, renderer_version,
            generation_status, validation_status
        ) VALUES (
            %s, %s, %s::uuid[],
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (curriculum_node_id)
        DO UPDATE SET
            lesson_json       = EXCLUDED.lesson_json,
            generation_status = EXCLUDED.generation_status,
            schema_version    = EXCLUDED.schema_version,
            renderer_version  = EXCLUDED.renderer_version,
            updated_at        = NOW()
    """, (
        lesson_id,
        str(node["id"]),
        uuid_array_str,
        'Grade 6', 'Mathematics', 'Ganita Prakash',
        f"Chapter {node['unit_number']}: {node['chapter_title']}",
        node["chapter_title"],
        node["content_type"],
        json.dumps(lesson_json),
        '1.0', 'visual-v4', GEN_MODEL, '1.0',
        'complete', 'unvalidated',
    ))
    conn.commit()
    cur.close()
    return lesson_id

# ── FETCH ALL NODES TO PROCESS ────────────────────────────────
def fetch_pending_nodes(conn) -> list:
    """
    Fetch all CBSE leaf nodes that do NOT yet have a complete
    visual lesson. Fully dynamic — works for any number of chapters.
    """
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            ct.id,
            ct.title,
            ct.content_type,
            ct.unit_number,
            ct.course_id,
            cc.title AS chapter_title
        FROM public.curriculum_tree ct
        JOIN public.course_chapters cc
            ON  cc.course_id      = ct.course_id
            AND cc.chapter_number = ct.unit_number
        WHERE ct.exam_type   = 'CBSE'
        AND   ct.subject_id  = %s
        AND   ct.is_leaf     = true
        AND   ct.level       = 2
        -- Skip nodes that already have a complete lesson
        AND NOT EXISTS (
            SELECT 1 FROM public.visual_lesson_cache vlc
            WHERE vlc.curriculum_node_id = ct.id
            AND   vlc.generation_status  = 'complete'
        )
        ORDER BY ct.unit_number ASC, ct.content_type ASC
    """, (REGULAR_SUBJECT_ID,))
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]

# ── MAIN ──────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  generate_visual_lesson.py  [v4 — fully dynamic]")
    print(f"  Model   : {GEN_MODEL}")
    print(f"  Schema  : v1.0 (with state machine + runtime contract)")
    print(f"{'='*60}\n")

    conn = psycopg2.connect(DB_URL)

    pending = fetch_pending_nodes(conn)
    total   = len(pending)

    if total == 0:
        print("  ✅ All nodes already have complete visual lessons.")
        conn.close()
        return

    print(f"  Pending nodes: {total}")
    print(f"  (Skipping nodes that already have complete lessons)\n")

    success = failed = skipped = 0

    for i, node in enumerate(pending, 1):
        node_id      = str(node["id"])
        chapter_num  = node["unit_number"]
        content_type = node["content_type"]
        chapter_title= node["chapter_title"]

        print(f"  [{i}/{total}] Chapter {chapter_num}: "
              f"{chapter_title} — {content_type}")

        try:
            # Gather context
            gen_content    = fetch_generated_content(conn, node)
            source_chunks  = fetch_source_chunks(conn, chapter_num)
            md_content     = load_md_section(chapter_num, content_type)
            source_ids     = [str(c["id"]) for c in source_chunks]

            if not gen_content and not md_content:
                print(f"     ⚠  No content found — skipping")
                skipped += 1
                continue

            # Build Gemini prompt dynamically from node data
            user_prompt = f"""Generate a 3-scene visual lesson for:

Chapter {chapter_num}: {chapter_title}
Content type: {content_type}
Subject: CBSE Grade 6 Mathematics (Ganita Prakash 2024)
Student age: 11-12 years

Teacher reference content ({content_type}):
{gen_content[:2000]}

Additional context from textbook:
{md_content[:1000]}

Source chunk IDs (include in metadata.sourceChunkIds):
{json.dumps(source_ids)}

Make the lesson appropriate for the content type:
- concept: explain the core idea with examples
- rules: focus on definitions and rules with examples
- worked_example: show step-by-step solutions
- practice: give problems to solve
- common_mistakes: highlight errors and corrections
- real_life: connect to Indian everyday life"""

            # Call Gemini — structure only
            lesson = call_gemini_json(user_prompt)

            # Add source chunk IDs to metadata
            lesson.setdefault("metadata", {})["sourceChunkIds"] = source_ids
            lesson["metadata"]["curriculumNodeId"] = node_id

            # Build SVGs from visualSpec for each slide
            for slide in lesson.get("slides", []):
                if "visualSpec" in slide:
                    slide["svgCache"]        = build_svg_from_spec(
                        slide["visualSpec"],
                        slide.get("slideIndex", 0)
                    )
                    slide["svgCacheVersion"] = "1.0"

            # Insert to DB
            lesson_id = insert_lesson(conn, lesson, node, source_ids)
            success  += 1
            slides    = len(lesson.get("slides", []))
            print(f"     ✅ lesson_id={lesson_id[:8]}... slides={slides}")

            # Save local JSON for inspection
            out_dir = MD_DIR.parent / "visual_lessons"
            out_dir.mkdir(parents=True, exist_ok=True)
            fname   = f"Ch{chapter_num:02d}_{content_type}_lesson.json"
            with open(out_dir / fname, "w", encoding="utf-8") as f:
                json.dump(lesson, f, indent=2, ensure_ascii=False)

            time.sleep(SLEEP_BETWEEN)

        except Exception as e:
            failed += 1
            print(f"     ❌ Failed: {e}")
            time.sleep(SLEEP_BETWEEN)
            continue

    conn.close()

    print(f"\n{'='*60}")
    print(f"  ✅ Success : {success}")
    print(f"  ⏭  Skipped : {skipped}")
    print(f"  ❌ Failed  : {failed}")
    print(f"\n  Verify in Supabase:")
    print(f"  SELECT COUNT(*), generation_status")
    print(f"  FROM public.visual_lesson_cache")
    print(f"  GROUP BY generation_status;")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
