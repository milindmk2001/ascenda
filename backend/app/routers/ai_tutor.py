"""
ai_tutor.py

Streams Gemini AI explanations using:
  1. public.prompt_templates  — system prompt + template text
  2. public.prompt_parameters — topic metadata (joined via curriculum_tree_id)
  3. Supabase RPC functions   — semantic search (executed via SQLAlchemy)
  4. public.explanations      — cache layer
"""

import os
import logging
from typing import Optional, AsyncGenerator
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text

from google import genai
from google.genai import types

router = APIRouter(prefix="/api/ai_tutor", tags=["ai_tutor"])
logger = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

GEN_MODEL   = "gemini-2.5-flash"
EMBED_MODEL = "models/gemini-embedding-2"   # matches generated_embeddings table
EMBED_DIMS  = 3072

COMPETITIVE_EXAM_BOARDS = {"IITJEE", "JEE", "NEET"}

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


# ── REQUEST SCHEMA ────────────────────────────────────────────
class ExplanationRequest(BaseModel):
    leaf_id: Optional[str] = Field(None, alias="leaf_id")
    leafId:  Optional[str] = Field(None, alias="leafId")

    class Config:
        populate_by_name = True


# ── STEP 1: FETCH LEAF + TEMPLATE + PARAMETERS ────────────────
def fetch_leaf_context(leaf_id: str) -> Optional[dict]:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        row = db.execute(text("""
            SELECT
                ct.id               AS leaf_id,
                ct.title            AS leaf_title,
                ct.content_type     AS leaf_type,
                ct.unit_number,
                ct.content_id,
                ct.prompt_template_id,
                parent.title        AS topic_title,
                grandparent.title   AS unit_title,

                gc.content          AS raw_content,
                gc.topic            AS gc_topic,
                gc.unit             AS gc_unit,
                gc.difficulty       AS gc_difficulty,
                gc.exam_type        AS gc_exam_type,
                gc.subject          AS gc_subject,

                pt.template_text,
                pt.system_prompt,

                pp.id               AS param_id,
                pp.topic            AS param_topic,
                pp.unit             AS param_unit,
                pp.difficulty,
                pp.weightage,
                pp.key_formulae,
                pp.common_mistakes,
                pp.prerequisites,
                pp.top_k_theory,
                pp.top_k_examples,
                pp.top_k_questions,
                pp.similarity_threshold

            FROM public.curriculum_tree ct
            LEFT JOIN public.curriculum_tree parent
              ON parent.id = ct.parent_id
            LEFT JOIN public.curriculum_tree grandparent
              ON grandparent.id = parent.parent_id
            LEFT JOIN public.generated_content gc
              ON gc.id = ct.content_id
            LEFT JOIN public.prompt_templates pt
              ON pt.id = ct.prompt_template_id
             AND pt.is_active = true
            LEFT JOIN public.prompt_parameters pp
              ON pp.curriculum_tree_id = ct.id
            WHERE ct.id = :leaf_id
              AND ct.is_leaf = true
            LIMIT 1
        """), {"leaf_id": leaf_id}).mappings().first()

        return dict(row) if row else None

    except Exception as e:
        logger.error(f"fetch_leaf_context SQL error for {leaf_id}: {e}")
        return None
    finally:
        db.close()


# ── STEP 2: CACHE LOOKUP ──────────────────────────────────────
def get_cached_explanation(leaf_id: str) -> Optional[str]:
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        row = db.execute(text("""
            SELECT explanation_text
            FROM public.explanations
            WHERE curriculum_tree_id = :leaf_id
              AND is_cached = true
            ORDER BY cache_version DESC
            LIMIT 1
        """), {"leaf_id": leaf_id}).mappings().first()
        return row["explanation_text"] if row else None
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")
        return None
    finally:
        db.close()


def save_explanation(leaf_id: str, template_id: Optional[str],
                      param_id: Optional[str], explanation_text: str) -> None:
    if not explanation_text.strip():
        return
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        db.execute(text("""
            INSERT INTO public.explanations (
                id, curriculum_tree_id, prompt_template_id,
                prompt_parameter_id, explanation_text,
                generated_by, is_cached, cache_version
            ) VALUES (
                :id, :leaf_id, :template_id,
                :param_id, :explanation_text,
                :model, true, 1
            )
            ON CONFLICT (curriculum_tree_id, cache_version)
            DO UPDATE SET
                explanation_text = EXCLUDED.explanation_text,
                generated_by     = EXCLUDED.generated_by
        """), {
            "id":               str(uuid4()),
            "leaf_id":          leaf_id,
            "template_id":      template_id,
            "param_id":         param_id,
            "explanation_text": explanation_text,
            "model":            GEN_MODEL,
        })
        db.commit()
        logger.info(f"Cached explanation for leaf {leaf_id}")
    except Exception as e:
        logger.warning(f"Cache save failed: {e}")
        db.rollback()
    finally:
        db.close()


# ── BOARD / SUBJECT RESOLUTION ─────────────────────────────────
def resolve_board_and_subject(ctx: dict) -> tuple[str, str]:
    board   = ctx.get("gc_exam_type") or "General Board"
    subject = ctx.get("gc_subject")   or ctx.get("topic_title") or "this subject"
    return str(board), str(subject)


def is_competitive_exam(board: str) -> bool:
    return board.strip().upper() in COMPETITIVE_EXAM_BOARDS


# ── STEP 3: EMBEDDING ──────────────────────────────────────────
def embed_query(topic: str, unit: str, subject: str, board: str) -> Optional[list]:
    if not gemini_client:
        return None
    try:
        response = gemini_client.models.embed_content(
            model=EMBED_MODEL,
            contents=f"{topic} {unit} {subject} {board}",
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=EMBED_DIMS
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.warning(f"Embedding failed (semantic search will be skipped): {e}")
        return None


# ── STEP 4: SEMANTIC SEARCH ────────────────────────────────────
def _embedding_to_pgvector(embedding: list) -> str:
    return "[" + ",".join(str(v) for v in embedding) + "]"


def search_generated_content(embedding: Optional[list], content_type: str,
                              top_k: int, threshold: float) -> list:
    if not embedding:
        return []
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        vec = _embedding_to_pgvector(embedding)
        rows = db.execute(text("""
            SELECT *
            FROM match_generated_content(
                (:vec)::vector,
                :match_count,
                CAST(NULL AS text),
                CAST(NULL AS text),
                CAST(:content_type AS text),
                CAST(:threshold AS double precision)
            )
        """), {
            "vec":          vec,
            "match_count":  top_k,
            "content_type": content_type,
            "threshold":    float(threshold),
        }).mappings().all()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Generated content search failed: {e}")
        return []
    finally:
        db.close()


def search_questions(embedding: Optional[list], subject: str, board: str,
                      top_k: int, threshold: float) -> list:
    if not embedding or not is_competitive_exam(board):
        return []
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        vec = _embedding_to_pgvector(embedding)
        rows = db.execute(text("""
            SELECT *
            FROM match_questions(
                (:vec)::vector,
                :match_count,
                CAST(:subject AS text),
                CAST(:board AS text),
                CAST(NULL AS text),
                CAST(:threshold AS double precision)
            )
        """), {
            "vec":         vec,
            "match_count": top_k,
            "subject":     subject,
            "board":       board,
            "threshold":   float(threshold),
        }).mappings().all()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Question search failed: {e}")
        return []
    finally:
        db.close()


# ── FORMATTING HELPERS ─────────────────────────────────────────
def format_chunks(chunks: list) -> str:
    if not chunks:
        return "No additional reference content retrieved."
    return "\n\n---\n\n".join(c.get("content", "") for c in chunks if c.get("content"))


def format_questions(questions: list) -> str:
    if not questions:
        return "No reference practice questions retrieved."
    lines = []
    for i, q in enumerate(questions, 1):
        lines.append(f"Q{i}. {q.get('question_final', '')}")
        opts = q.get("options", {})
        if isinstance(opts, dict):
            for k, v in opts.items():
                lines.append(f"   {k}) {v}")
        lines.append(f"   Answer: {q.get('correct_answer', '')}")
        lines.append("")
    return "\n".join(lines)


def format_list(items) -> str:
    if not items:
        return "Not specified"
    if isinstance(items, list):
        return "\n".join(f"• {item}" for item in items)
    return str(items)


# ── STEP 5: BUILD PROMPT ───────────────────────────────────────
def build_prompt(ctx: dict, theory: list, formulae: list,
                  examples: list, questions: list) -> tuple[str, str]:
    board, subject = resolve_board_and_subject(ctx)
    exam_mode = is_competitive_exam(board)

    topic     = ctx.get("param_topic") or ctx.get("gc_topic") or ctx.get("topic_title") or "this topic"
    unit      = ctx.get("param_unit")  or ctx.get("gc_unit")  or ctx.get("unit_title")  or "this unit"
    diff      = ctx.get("difficulty")  or ctx.get("gc_difficulty") or ("IITJEE Standard" if exam_mode else "Standard")
    weightage = ctx.get("weightage")   or "Not specified"

    key_formulae    = ctx.get("key_formulae")    or []
    common_mistakes = ctx.get("common_mistakes") or []
    template_text   = ctx.get("template_text")
    system_prompt   = ctx.get("system_prompt")

    if template_text:
        try:
            user_prompt = template_text.format(
                topic=topic, unit=unit, difficulty=diff, weightage=weightage,
                key_formulae=format_list(key_formulae),
                common_mistakes=format_list(common_mistakes),
                theory_chunks=format_chunks(theory),
                formulae_chunks=format_chunks(formulae),
                worked_example_chunks=format_chunks(examples),
                jee_questions=format_questions(questions),
            )
            return system_prompt or "", user_prompt
        except KeyError as e:
            logger.warning(f"Template placeholder missing ({e}) — using fallback")

    leaf_type = ctx.get("leaf_type", "concept")

    if exam_mode:
        type_instructions = {
            "concept": (
                "Break down this physics concept using an active, engaging teaching voice. "
                "Do NOT write a textbook chapter or a formal script. Speak exactly like a passionate instructor "
                "standing at a physical blackboard tracking vectors. Use spoken transitions like: 'Look closely at this point...', "
                "'Now, think about what happens to the energy...', 'Wait, let's pause and observe this transition.' "
                "Keep sentences punchy and verbal."
            ),
            "solved_problems": (
                "Walk through the derivation of these sample problems step-by-step out loud. "
                "Explain the physical intuition *behind* choosing each equation before you write it down. "
                "Do not just state formulas—teach the analytical strategy dynamically."
            ),
            "unsolved_problems": (
                "Provide an interactive analytical blueprint for this challenge. Guide the student's mind through "
                "how to isolate components, draw free-body constraints, and set up equilibrium conditions, talking "
                "them through the setup like a personal tutor."
            ),
            "concept_test": (
                "Deconstruct each option vector out loud. Teach *why* a option is a trap and *why* another "
                "is mathematically or conceptually flawless. Break down the edge cases like an active professor."
            ),
        }
        instruction = type_instructions.get(leaf_type, f"Explain this content for a {board} {subject} student.")
        system_prompt = (
            f"You are an elite female {board} {subject} professor explaining core concepts dynamically to an active student. "
            "Adopt a direct, oral classroom teaching delivery style. Do not use overly formal textbook prose. "
            "Keep your syntax tailored for verbal listening—meaning shorter clauses, emphatic focal points, "
            "and clear structural transitions. Avoid chat check-ins or halting question checkpoints for this phase."
        )
    else:
        type_instructions = {
            "concept": (
                f"Explain this {subject} concept in a warm, encouraging voice for a school student. "
                "Do NOT write a textbook chapter. Speak like a friendly classroom teacher standing at the board. "
                "Use spoken transitions like: 'Let's look at this together...', 'Now notice what happens here...', "
                "'Think about it this way...'. Keep sentences short, clear, and age-appropriate."
            ),
            "worked_example": (
                "Walk through this worked example step-by-step out loud, the way a teacher would at the board. "
                "Explain *why* each step is taken before doing it, not just what the step is."
            ),
            "practice": (
                "Guide the student through how to approach these practice questions without simply giving the "
                "answer away — talk through the first step or two of reasoning like a tutor sitting beside them."
            ),
            "common_mistakes": (
                "Point out, in a friendly non-judgmental tone, the mistakes students commonly make on this topic "
                "and how to spot and avoid each one."
            ),
            "real_life": (
                "Connect this topic to everyday examples a school student would recognize, keeping it concrete and relatable."
            ),
        }
        instruction = type_instructions.get(leaf_type, f"Explain this {subject} content clearly for a school student.")
        system_prompt = (
            f"You are a warm, encouraging {board} {subject} teacher explaining concepts to a school student in "
            f"{unit}. Adopt a direct, spoken classroom teaching style — not formal textbook prose. "
            "Keep sentences short and clear, use concrete everyday examples, and keep the tone age-appropriate "
            "and encouraging rather than exam-pressure-driven."
        )

    raw_content = ctx.get("raw_content") or ""
    safe_content = raw_content[:3000]

    user_prompt = (
        f"Board: {board}\nSubject: {subject}\nTopic: {topic}\nUnit: {unit}\nDifficulty: {diff}\n\n"
        f"INSTRUCTION: {instruction}\n\n"
        f"REFERENCE CONTENT:\n{safe_content}\n\n"
        f"KEY FORMULAE:\n{format_list(key_formulae)}\n\n"
        f"COMMON MISTAKES:\n{format_list(common_mistakes)}"
    )
    return system_prompt, user_prompt


# ── STEP 6: STREAM ─────────────────────────────────────────────
async def stream_gemini(system_prompt: str, user_prompt: str, leaf_id: str,
                         template_id: Optional[str], param_id: Optional[str]
                         ) -> AsyncGenerator[str, None]:
    if not gemini_client:
        yield "AI engine not configured — GEMINI_API_KEY missing."
        return

    full_text = []
    try:
        response = gemini_client.models.generate_content_stream(
            model=GEN_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=0.5,
                max_output_tokens=2000,
            )
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
                full_text.append(chunk.text)

    except Exception as e:
        error_msg = f"\n\n**Error generating explanation:** {str(e)}"
        logger.error(f"Gemini stream error: {e}")
        yield error_msg
        full_text.append(error_msg)
        return

    if full_text:
        save_explanation(leaf_id, template_id, param_id, "".join(full_text))


# ── MAIN ENDPOINT ───────────────────────────────────────────────
@router.post("/stream")
async def stream_explanation_endpoint(request: ExplanationRequest):
    leaf_id = request.leaf_id or request.leafId
    if not leaf_id:
        raise HTTPException(status_code=422, detail="Missing leaf_id or leafId.")

    ctx = fetch_leaf_context(leaf_id.strip())
    if not ctx:
        raise HTTPException(
            status_code=404,
            detail=f"Leaf node {leaf_id} not found in curriculum_tree."
        )

    template_id = str(ctx["prompt_template_id"]) if ctx.get("prompt_template_id") else None
    param_id    = str(ctx["param_id"])            if ctx.get("param_id")            else None
    board, subject = resolve_board_and_subject(ctx)
    topic       = ctx.get("param_topic") or ctx.get("gc_topic") or ctx.get("topic_title") or "Unknown"
    unit        = ctx.get("param_unit")  or ctx.get("gc_unit")  or ctx.get("unit_title")  or "Unknown"
    leaf_type   = ctx.get("leaf_type", "concept")

    logger.info(
        f"Stream request: leaf={leaf_id} board={board} subject={subject} topic={topic} type={leaf_type} "
        f"template={'found' if template_id else 'MISSING'} "
        f"params={'found' if param_id else 'MISSING'}"
    )

    # Cache check
    cached = get_cached_explanation(leaf_id)
    if cached:
        async def stream_cached():
            yield cached
        return StreamingResponse(
            stream_cached(), media_type="text/plain",
            headers={"X-Cache": "HIT", "X-Topic": topic}
        )

    top_k_theory    = ctx.get("top_k_theory")    or 3
    top_k_examples  = ctx.get("top_k_examples")  or 3
    top_k_questions = ctx.get("top_k_questions") or 4
    threshold       = ctx.get("similarity_threshold") or 0.25

    embedding = embed_query(topic, unit, subject, board)
    theory    = search_generated_content(embedding, "theory", top_k_theory, threshold)
    formulae  = search_generated_content(embedding, "formulae", 1, threshold)
    examples  = search_generated_content(embedding, "worked_example", top_k_examples, threshold)
    questions = search_questions(embedding, subject, board, top_k_questions, threshold)

    logger.info(f"Semantic search: theory={len(theory)} formulae={len(formulae)} "
                f"examples={len(examples)} questions={len(questions)}")

    system_prompt, user_prompt = build_prompt(ctx, theory, formulae, examples, questions)

    return StreamingResponse(
        stream_gemini(system_prompt, user_prompt, leaf_id, template_id, param_id),
        media_type="text/plain",
        headers={
            "X-Cache":     "MISS",
            "X-Topic":     topic,
            "X-Leaf-Type": leaf_type,
            "X-Template":  "db" if template_id else "fallback",
            "Cache-Control": "no-cache",
        }
    )


@router.get("/health")
def health():
    return {
        "status":           "ok",
        "model":             GEN_MODEL,
        "gemini_configured": gemini_client is not None,
        "note": "All DB access including semantic search uses DATABASE_URL via SQLAlchemy.",
    }