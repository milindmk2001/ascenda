"""
ai_tutor.py

Streams Gemini AI explanations using:
  1. public.prompt_templates  — system prompt + template text
  2. public.prompt_parameters — topic metadata (joined via curriculum_tree_id)
  3. Supabase RPC functions   — semantic search (optional — only if
                                 SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY set)
  4. public.explanations      — cache layer

CRITICAL FIX vs previous version:
  - Database lookups (curriculum_tree, prompt_templates, prompt_parameters,
    explanations) use SQLAlchemy SessionLocal — the SAME working connection
    as curriculum.py. They do NOT depend on the supabase-py REST client.
  - Only semantic search (RPC calls) requires the supabase-py client.
    If that client is unavailable, semantic search is skipped gracefully
    and the fallback prompt still works — it no longer causes a 404.
  - Column names corrected to match actual schema:
      curriculum_tree.prompt_template_id  (no prompt_param_id column exists)
      prompt_parameters.curriculum_tree_id (join key, not ct.prompt_param_id)
      explanations.curriculum_tree_id / prompt_template_id /
        prompt_parameter_id / explanation_text / is_cached / cache_version
  - Embedding model corrected to models/gemini-embedding-2 @ 3072 dims
    (matches what generated_embeddings/question_embeddings were built with).
  - Removed experimental response_modalities=["TEXT","AUDIO"] — not
    supported reliably via generate_content_stream on gemini-2.5-flash;
    that is a Live API feature and was a silent failure point.
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
SUPABASE_URL   = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY   = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

GEN_MODEL   = "gemini-2.5-flash"
EMBED_MODEL = "models/gemini-embedding-2"   # matches generated_embeddings table
EMBED_DIMS  = 3072

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# NOTE: supabase-py REST client is no longer needed anywhere in this file.
# All database access — including semantic search RPC calls — goes
# through SQLAlchemy / DATABASE_URL, which is already configured on
# Railway. SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY are not required.


# ── REQUEST SCHEMA ────────────────────────────────────────────
class ExplanationRequest(BaseModel):
    leaf_id: Optional[str] = Field(None, alias="leaf_id")
    leafId:  Optional[str] = Field(None, alias="leafId")

    class Config:
        populate_by_name = True


# ── STEP 1: FETCH LEAF + TEMPLATE + PARAMETERS (SQLAlchemy only) ──
def fetch_leaf_context(leaf_id: str) -> Optional[dict]:
    """
    Uses SQLAlchemy SessionLocal exclusively — same connection pattern
    as curriculum.py. Never depends on the supabase REST client.
    """
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


# ── STEP 2: CACHE LOOKUP (correct explanations schema) ────────
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


# ── STEP 3: EMBEDDING (correct model + dims) ──────────────────
def embed_query(topic: str, unit: str) -> Optional[list]:
    if not gemini_client:
        return None
    try:
        response = gemini_client.models.embed_content(
            model=EMBED_MODEL,
            contents=f"{topic} {unit} IITJEE Physics",
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
# Calls the Postgres RPC functions DIRECTLY via the existing
# DATABASE_URL / SQLAlchemy connection — no supabase-py REST client
# and no SUPABASE_URL/SUPABASE_SERVICE_ROLE_KEY required at all.
# match_generated_content / match_questions are plain SQL functions
# already created in Supabase — calling them via SQL is identical
# to calling them via supabase.rpc(), just over the existing
# Postgres connection instead of REST.
def _embedding_to_pgvector(embedding: list) -> str:
    """Format a Python float list as a pgvector literal string."""
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
                NULL,
                NULL,
                :content_type,
                :threshold
            )
        """), {
            "vec":          vec,
            "match_count":  top_k,
            "content_type": content_type,
            "threshold":    threshold,
        }).mappings().all()
        return [dict(r) for r in rows]
    except Exception as e:
        logger.warning(f"Generated content search failed: {e}")
        return []
    finally:
        db.close()


def search_questions(embedding: Optional[list], top_k: int, threshold: float) -> list:
    if not embedding:
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
                'Physics',
                NULL,
                NULL,
                :threshold
            )
        """), {
            "vec":         vec,
            "match_count": top_k,
            "threshold":   threshold,
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
        return "No reference JEE questions retrieved."
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


# ── STEP 5: BUILD PROMPT (DB template, fallback if missing) ──
def build_prompt(ctx: dict, theory: list, formulae: list,
                  examples: list, questions: list) -> tuple[str, str]:
    topic     = ctx.get("param_topic") or ctx.get("gc_topic") or ctx.get("topic_title") or "Physics Concept"
    unit      = ctx.get("param_unit")  or ctx.get("gc_unit")  or ctx.get("unit_title")  or "Unknown Unit"
    diff      = ctx.get("difficulty")  or ctx.get("gc_difficulty") or "IITJEE Standard"
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

    # ── Fallback if no DB template found ──────────────────────
    leaf_type = ctx.get("leaf_type", "concept")
    type_instructions = {
        "concept":           "Deliver an exhaustive, crystal-clear conceptual explanation. Break down the physical mechanics from ground principles to advanced analytical insights. Do not ask questions or use leading dialog elements.",
        "solved_problems":   "Deconstruct each physics problem analytically. Provide full, unedited derivations and complete mathematical solutions from start to finish. Do not stop to wait for student feedback.",
        "unsolved_problems": "Provide a complete analytical blueprint detailing the step-by-step physics required to solve the scenario. Do not hide answers or leave variables isolated for the user to solve.",
        "concept_test":      "Provide an authoritative breakdown explaining why each option is conceptually valid or physically impossible.",
    }
    instruction = type_instructions.get(leaf_type, "Explain this content for a JEE student.")
    raw_content = ctx.get("raw_content", "")

    user_prompt = (
        f"Topic: {topic}\nUnit: {unit}\nDifficulty: {diff}\n\n"
        f"INSTRUCTION: {instruction}\n\n"
        f"REFERENCE CONTENT:\n{raw_content[:3000]}\n\n"
        f"KEY FORMULAE:\n{format_list(key_formulae)}\n\n"
        f"COMMON MISTAKES:\n{format_list(common_mistakes)}"
    )
    system_prompt = (
        "You are an expert female IIT JEE Physics professor. Give a comprehensive, continuous oral lecture breakdown "
        "of the topic material using the reference content as your source data. Do not stop to quiz the student, "
        "do not ask leading questions, and do not use chat check-ins or interactive conversational checkpoints."
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
                # NOTE: response_modalities=["TEXT","AUDIO"] removed —
                # not supported via generate_content_stream on this model;
                # that requires the Gemini Live API. Add back only after
                # testing against the Live API endpoint separately.
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
    topic       = ctx.get("param_topic") or ctx.get("gc_topic") or ctx.get("topic_title") or "Unknown"
    unit        = ctx.get("param_unit")  or ctx.get("gc_unit")  or ctx.get("unit_title")  or "Unknown"
    leaf_type   = ctx.get("leaf_type", "concept")

    logger.info(
        f"Stream request: leaf={leaf_id} topic={topic} type={leaf_type} "
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

    # Semantic search (skipped gracefully if supabase REST client unavailable)
    top_k_theory    = ctx.get("top_k_theory")    or 3
    top_k_examples  = ctx.get("top_k_examples")  or 3
    top_k_questions = ctx.get("top_k_questions") or 4
    threshold       = ctx.get("similarity_threshold") or 0.25

    embedding = embed_query(topic, unit)
    theory    = search_generated_content(embedding, "theory", top_k_theory, threshold)
    formulae  = search_generated_content(embedding, "formulae", 1, threshold)
    examples  = search_generated_content(embedding, "worked_example", top_k_examples, threshold)
    questions = search_questions(embedding, top_k_questions, threshold)

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
