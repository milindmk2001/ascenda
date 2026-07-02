"""
generate_visual_lesson.py
Generates a visual lesson JSON for CBSE Chapter 1 concept node.
Uses two-call approach: structure first, then SVG built in Python.
"""

import os
import re
import json
import uuid
import psycopg2
import psycopg2.extras
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

DB_URL     = os.environ["DATABASE_DIRECT_URL"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
GEN_MODEL  = "gemini-2.5-flash"

CURRICULUM_NODE_ID = "fcdcc169-c64d-4241-8a04-ea4c8ccf475c"
CONTENT_ID         = "3d3b57ae-46cf-4c83-9577-04d92eb13cde"
MD_DIR             = Path(r"C:\projects\data_sources\school\cbse\grade_6\mathematics\generated")

client = genai.Client(api_key=GEMINI_KEY)

PROMPT_STRUCTURE = """
Generate a visual lesson JSON for Grade 6 Mathematics.
Return ONLY valid JSON with this exact structure:

{
  "schemaVersion": "1.0",
  "lessonId": "ch1-patterns-concept",
  "initialScene": "s1",

  "metadata": {
    "subject": "Mathematics",
    "grade": 6,
    "book": "Ganita Prakash",
    "chapter": "Chapter N: Title",
    "topic": "Topic name",
    "concept": "Concept name",
    "curriculumNodeId": "paste-node-id-here"
  },

  "learningObjectives": [
    "objective 1",
    "objective 2",
    "objective 3"
  ],

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
      "learningObjective": "one sentence",
      "narration": "2-3 warm sentences with Indian examples",
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
      "answer": "correct answer",
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

RULES:
- sceneType must be one of:
  animated_explanation | student_response | hint_delivery |
  tutor_response | lesson_summary
- animationTimeline actions must be one of:
  fadeIn | show | hide | highlight | pulse | reveal | zoomTo | drawArrow
- transitions targets must match slideId values or be: tutor_router
- visualSpec.visualType must be one of:
  number_sequence | number_line | fraction_strip | geometry_construct |
  data_bar_chart | symmetry_grid | area_grid | factor_tree
- prerequisites.conceptsRequired must come from the prompt_parameters
  provided in context
- Return ONLY the JSON. No markdown. No explanation.
"""

# ── BUILD SVG IN PYTHON — fully reliable ──────────────────────
def build_number_sequence_svg(sequence: list, rule: str, slide_index: int) -> str:
    """Build a clean number sequence SVG with animation IDs."""
    n       = len(sequence)
    width   = 480
    height  = 260
    cx_start = 60
    spacing  = min(90, (width - 120) // max(n, 1))
    cy       = 130
    r        = 24
    colors   = ["#4A90D9", "#E86C3A", "#2ECC71", "#F5A623", "#9B59B6"]

    elements = []

    # Title area
    elements.append(f'<text x="240" y="35" text-anchor="middle" font-family="Arial" font-size="15" font-weight="bold" fill="#333333">Number Pattern</text>')

    # Rule label at top right
    elements.append(f'<rect id="rule_label_{slide_index}" x="360" y="18" width="100" height="28" rx="6" fill="#9B59B6"/>')
    elements.append(f'<text x="410" y="37" text-anchor="middle" font-family="Arial" font-size="14" fill="white">Rule: {rule}</text>')

    # Draw each number circle
    for i, num in enumerate(sequence):
        cx    = cx_start + i * spacing
        color = colors[i % len(colors)]
        nid   = f"num_{num}_{slide_index}_{i}"

        elements.append(f'<circle id="{nid}" cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>')
        elements.append(f'<text x="{cx}" y="{cy + 5}" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="white">{num}</text>')

        # Arrow to next number
        if i < len(sequence) - 1:
            cx_next  = cx_start + (i + 1) * spacing
            x1       = cx + r + 4
            x2       = cx_next - r - 4
            xmid     = (x1 + x2) // 2
            arrow_id = f"arrow_{slide_index}_{i}"
            label_id = f"label_{slide_index}_{i}"

            elements.append(f'<line id="{arrow_id}" x1="{x1}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="#333333" stroke-width="2" marker-end="url(#ah_{slide_index})"/>')
            elements.append(f'<text id="{label_id}" x="{xmid}" y="{cy - 10}" text-anchor="middle" font-family="Arial" font-size="12" fill="#E86C3A">{rule}</text>')

    # Question mark circle at end
    qcx = cx_start + len(sequence) * spacing
    if qcx < width - 30:
        elements.append(f'<circle id="question_circle_{slide_index}" cx="{qcx}" cy="{cy}" r="{r}" fill="#eeeeee" stroke="#333333" stroke-width="2" stroke-dasharray="4"/>')
        elements.append(f'<text x="{qcx}" y="{cy + 5}" text-anchor="middle" font-family="Arial" font-size="20" fill="#333333">?</text>')

    # Bottom label
    elements.append(f'<text x="240" y="230" text-anchor="middle" font-family="Arial" font-size="13" fill="#777777">What comes next?</text>')

    inner = "\n  ".join(elements)

    svg = f'''<svg viewBox="0 0 480 260" xmlns="http://www.w3.org/2000/svg">
  <rect width="480" height="260" fill="white"/>
  <defs>
    <marker id="ah_{slide_index}" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#333333"/>
    </marker>
  </defs>
  {inner}
</svg>'''

    return svg

def build_animation_timeline(sequence: list, rule: str, slide_index: int) -> list:
    """Build animation timeline matching the SVG element IDs."""
    timeline = []
    for i, num in enumerate(sequence):
        nid = f"num_{num}_{slide_index}_{i}"
        action = "fadeIn" if i == 0 else "reveal"
        timeline.append({"action": action, "target": nid, "duration": 400})
        if i < len(sequence) - 1:
            timeline.append({"action": "drawArrow", "target": f"arrow_{slide_index}_{i}", "duration": 300})
    timeline.append({"action": "highlight", "target": f"rule_label_{slide_index}", "duration": 600})
    timeline.append({"action": "pulse", "target": f"question_circle_{slide_index}", "duration": 500})
    return timeline

# ── FETCH / LOAD ──────────────────────────────────────────────
def fetch_content(conn):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT content, topic, unit, content_type FROM public.generated_content WHERE id = %s", (CONTENT_ID,))
    row = cur.fetchone()
    cur.close()
    return dict(row)

def fetch_source_chunks(conn, limit=5):
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT ch.id FROM public.chunks ch
        JOIN public.books b ON b.id = ch.book_id
        WHERE b.file_name = 'fegp101.pdf'
        ORDER BY ch.chunk_index LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    return [dict(r) for r in rows]

def load_md_concept(chapter_num=1):
    files = list(MD_DIR.glob(f"Ch{chapter_num:02d}_*.md"))
    if not files:
        return ""
    text  = files[0].read_text(encoding="utf-8")
    match = re.search(r'## CONCEPT EXPLANATION\s*(.*?)(?=## KEY RULES|## STEP|$)', text, re.DOTALL)
    return match.group(1).strip()[:3000] if match else text[:3000]

def call_gemini_json(prompt: str, system: str) -> dict:
    response = client.models.generate_content(
        model    = GEN_MODEL,
        contents = prompt,
        config   = types.GenerateContentConfig(
            system_instruction = system,
            response_mime_type = "application/json",
            temperature        = 0.2,
            max_output_tokens  = 2000,
        )
    )
    raw = response.text.strip()
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    return json.loads(raw.strip())

# ── INSERT ────────────────────────────────────────────────────
def insert_lesson(conn, lesson_json: dict, source_chunk_ids: list) -> str:
    lesson_id      = str(uuid.uuid4())
    uuid_array_str = '{' + ','.join(str(c) for c in source_chunk_ids) + '}'
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO public.visual_lesson_cache (
            lesson_id, curriculum_node_id, source_chunk_ids,
            grade, subject, book, chapter, topic, concept,
            lesson_json, schema_version, prompt_version, model_used,
            generation_status, validation_status
        ) VALUES (%s,%s,%s::uuid[],%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        lesson_id, CURRICULUM_NODE_ID, uuid_array_str,
        'Grade 6', 'Mathematics', 'Ganita Prakash',
        lesson_json.get('metadata', {}).get('chapter', 'Chapter 1'),
        lesson_json.get('metadata', {}).get('topic', 'Number Patterns'),
        lesson_json.get('metadata', {}).get('concept', 'Patterns'),
        json.dumps(lesson_json),
        '1.0', 'visual-v3', GEN_MODEL,
        'complete', 'unvalidated',
    ))
    conn.commit()
    cur.close()
    return lesson_id

# ── MAIN ──────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"  generate_visual_lesson.py  [Python SVG mode]")
    print(f"  Node  : {CURRICULUM_NODE_ID}")
    print(f"  Model : {GEN_MODEL}")
    print(f"{'='*60}\n")

    conn = psycopg2.connect(DB_URL)
    cur  = conn.cursor()
    cur.execute("SELECT lesson_id FROM public.visual_lesson_cache WHERE curriculum_node_id = %s LIMIT 1", (CURRICULUM_NODE_ID,))
    existing = cur.fetchone()
    cur.close()
    if existing:
        print(f"  ⏭  Already exists: {existing[0]}")
        print(f"  DELETE FROM public.visual_lesson_cache WHERE curriculum_node_id = '{CURRICULUM_NODE_ID}';")
        conn.close()
        return

    print("  📥 Fetching data...")
    content       = fetch_content(conn)
    source_chunks = fetch_source_chunks(conn)
    md_content    = load_md_concept(1)

    print(f"\n  🤖 Generating lesson structure via Gemini...")
    user_prompt = f"""Generate a 3-slide visual lesson for Grade 6 students.

Chapter: {content['unit']}
Topic: {content['topic']}

Reference content:
{content['content'][:2000]}

Context:
{md_content[:1000]}"""

    try:
        lesson = call_gemini_json(user_prompt, PROMPT_STRUCTURE)
        slides = lesson.get('slides', [])
        print(f"  ✅ {len(slides)} slides structured")
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        conn.close()
        return

    print(f"\n  🎨 Building SVGs in Python...")
    for i, slide in enumerate(slides):
        sequence = slide.get('sequence', [2, 4, 6, 8, 10])
        rule     = slide.get('rule', '+2')

        svg      = build_number_sequence_svg(sequence, rule, i + 1)
        timeline = build_animation_timeline(sequence, rule, i + 1)

        slide['svg']               = svg
        slide['animationTimeline'] = timeline

        print(f"     Slide {i+1}: {slide.get('title','?')} — seq={sequence} rule={rule} svg={len(svg)}chars")

    source_chunk_ids = [str(c['id']) for c in source_chunks]
    lesson.setdefault('metadata', {})['sourceChunkIds'] = source_chunk_ids

    out_dir  = MD_DIR.parent / "visual_lessons"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "Ch01_concept_lesson.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(lesson, f, indent=2, ensure_ascii=False)
    print(f"\n  💾 Saved: {out_path}")

    print(f"\n  📤 Inserting into visual_lesson_cache...")
    lesson_id = insert_lesson(conn, lesson, source_chunk_ids)
    conn.close()

    print(f"\n{'='*60}")
    print(f"  ✅ lesson_id: {lesson_id}")
    print(f"  Slides: {len(slides)}")
    print(f"\n  Verify:")
    print(f"  SELECT lesson_id, chapter, generation_status,")
    print(f"         jsonb_array_length(lesson_json->'slides') AS slides")
    print(f"  FROM public.visual_lesson_cache;")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
