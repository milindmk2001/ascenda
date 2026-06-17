"""
ai_tutor.py

Streams Gemini AI explanations using:
  1. public.prompt_templates  — system prompt + template text (from Supabase)
  2. public.prompt_parameters — topic metadata (difficulty, formulae, mistakes)
  3. Supabase RPC functions   — semantic search for relevant content
  4. public.explanations      — cache layer (skip Gemini on repeat visits)

Flow per request:
  leaf_id
    → fetch curriculum_tree node + prompt_template + prompt_parameters
    → check explanations cache
    → if cached: stream cached text directly
    → if not cached:
        → embed topic query
        → semantic search: theory + formulae + examples + JEE questions
        → fill template placeholders
        → stream Gemini response
        → cache result in public.explanations
"""

import os
import json
import logging
from typing import Optional, AsyncGenerator
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from supabase import create_client, Client

from google import genai
from google.genai import types

router = APIRouter(prefix="/api/ai_tutor", tags=["ai_tutor"])
logger = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────
GEMINI_API_KEY   = os.environ.get("GEMINI_API_KEY", "")
SUPABASE_URL     = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY     = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
GEN_MODEL        = "gemini-2.5-flash"
EMBED_MODEL      = "models/gemini-embedding-2"
EMBED_DIMS       = 3072

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None


# ── REQUEST SCHEMA ────────────────────────────────────────────
class ExplanationRequest(BaseModel):
    leaf_id: Optional[str] = Field(None, alias="leaf_id")
    leafId:  Optional[str] = Field(None, alias="leafId")

    class Config:
        populate_by_name = True


# ── STEP 1: FETCH EVERYTHING NEEDED IN ONE DB QUERY ──────────
def fetch_leaf_context(leaf_id: str) -> dict | None:
    """
    Fetches from THREE tables in one query:
      - curriculum_tree node
      - prompt_templates (via prompt_template_id FK)
      - prompt_parameters (via curriculum_tree_id FK)
    Returns everything needed to build the prompt.
    """
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        row = db.execute(text("""
            SELECT
                -- Curriculum tree node
                ct.id               AS leaf_id,
                ct.title            AS leaf_title,
                ct.content_type     AS leaf_type,
                ct.unit_number,
                ct.content_id,
                ct.exam_type,
                parent.title        AS topic_title,
                grandparent.title   AS unit_title,

                -- Raw generated content (direct via content_id)
                gc.content          AS raw_content,
                gc.topic            AS gc_topic,
                gc.unit             AS gc_unit,
                gc.difficulty       AS gc_difficulty,

                -- Prompt template from public.prompt_templates
                pt.id               AS template_id,
                pt.template_text,
                pt.system_prompt,
                pt.content_type     AS template_type,

                -- Prompt parameters from public.prompt_parameters
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

            -- Parent = topic node (level 2)
            LEFT JOIN public.curriculum_tree parent
              ON parent.id = ct.parent_id

            -- Grandparent = unit node (level 1)
            LEFT JOIN public.curriculum_tree grandparent
              ON grandparent.id = parent.parent_id

            -- Raw content via content_id
            LEFT JOIN public.generated_content gc
              ON gc.id = ct.content_id

            -- Prompt template linked on curriculum_tree leaf
            LEFT JOIN public.prompt_templates pt
              ON pt.id = ct.prompt_template_id
             AND pt.is_active = true

            -- Prompt parameters for this specific leaf
            LEFT JOIN public.prompt_parameters pp
              ON pp.curriculum_tree_id = ct.id

            WHERE ct.id = :leaf_id
              AND ct.is_leaf = true
            LIMIT 1
        """), {"leaf_id": leaf_id}).mappings().first()

        return dict(row) if row else None

    finally:
        db.close()


# ── STEP 2: CHECK CACHE ───────────────────────────────────────
def get_cached_explanation(leaf_id: str) -> str | None:
    """Check public.explanations for cached response."""
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
    finally:
        db.close()


# ── STEP 3: EMBED TOPIC QUERY ─────────────────────────────────
def embed_query(topic: str, unit: str) -> list[float] | None:
    """Embed the topic query for semantic search."""
    if not gemini_client:
        return None
    try:
        query_text = f"{topic} {unit} IITJEE Physics"
        response = gemini_client.models.embed_content(
            model=EMBED_MODEL,
            contents=query_text,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=EMBED_DIMS
            )
        )
        return response.embeddings[0].values
    except Exception as e:
        logger.warning(f"Embedding failed: {e}")
        return None


# ── STEP 4: SEMANTIC SEARCH ───────────────────────────────────
def search_generated_content(
    embedding: list[float],
    content_type: str,
    top_k: int,
    threshold: float = 0.25
) -> list[dict]:
    """Search public.generated_embeddings via Supabase RPC."""
    if not supabase or not embedding:
        return []
    try:
        result = supabase.rpc("match_generated_content", {
            "query_embedding":      embedding,
            "match_count":          top_k,
            "filter_content_type":  content_type,
            "similarity_threshold": threshold
        }).execute()
        return result.data or []
    except Exception as e:
        logger.warning(f"Generated content search failed: {e}")
        return []


def search_questions(
    embedding: list[float],
    top_k: int,
    threshold: float = 0.25
) -> list[dict]:
    """Search public.question_embeddings via Supabase RPC."""
    if not supabase or not embedding:
        return []
    try:
        result = supabase.rpc("match_questions", {
            "query_embedding":      embedding,
            "match_count":          top_k,
            "filter_subject":       "Physics",
            "filter_exam_type":     "JEE",
            "filter_difficulty":    None,
            "similarity_threshold": threshold
        }).execute()
        return result.data or []
    except Exception as e:
        logger.warning(f"Question search failed: {e}")
        return []


# ── STEP 5: FORMAT RETRIEVED CONTENT ─────────────────────────
def format_chunks(chunks: list[dict]) -> str:
    if not chunks:
        return "No additional content retrieved."
    return "\n\n---\n\n".join(
        c.get("content", "") for c in chunks if c.get("content")
    )


def format_questions(questions: list[dict]) -> str:
    if not questions:
        return "No JEE questions retrieved."
    lines = []
    for i, q in enumerate(questions, 1):
        lines.append(f"Q{i}. {q.get('question_final', '')}")
        opts = q.get("options", {})
        if isinstance(opts, dict):
            for k, v in opts.items():
                lines.append(f"   {k}) {v}")
        lines.append(f"   Answer: {q.get('correct_answer', '')}")
        lines.append(f"   Year: {q.get('exam_year', '')}")
        lines.append("")
    return "\n".join(lines)


def format_list(items) -> str:
    if not items:
        return "Not specified"
    if isinstance(items, list):
        return "\n".join(f"• {item}" for item in items)
    return str(items)


# ── STEP 6: BUILD PROMPT FROM TEMPLATE ───────────────────────
def build_prompt(ctx: dict, theory: list, formulae: list,
                 examples: list, questions: list) -> tuple[str, str]:
    """
    Fills template_text placeholders with retrieved content.
    Returns (system_prompt, user_prompt).

    Falls back to hardcoded prompt if no template in DB.
    """
    topic    = ctx.get("param_topic")  or ctx.get("gc_topic")    or ctx.get("topic_title") or "Unknown Topic"
    unit     = ctx.get("param_unit")   or ctx.get("gc_unit")      or ctx.get("unit_title")  or "Unknown Unit"
    diff     = ctx.get("difficulty")   or ctx.get("gc_difficulty") or "Medium"
    weightage     = ctx.get("weightage")     or "Medium"
    key_formulae  = ctx.get("key_formulae")  or []
    common_mistakes = ctx.get("common_mistakes") or []
    template_text = ctx.get("template_text")
    system_prompt = ctx.get("system_prompt")

    # ── Use DB template if available ──────────────────────────
    if template_text:
        try:
            user_prompt = template_text.format(
                topic               = topic,
                unit                = unit,
                difficulty          = diff,
                weightage           = weightage,
                key_formulae        = format_list(key_formulae),
                common_mistakes     = format_list(common_mistakes),
                theory_chunks       = format_chunks(theory),
                formulae_chunks     = format_chunks(formulae),
                worked_example_chunks = format_chunks(examples),
                jee_questions       = format_questions(questions),
            )
        except KeyError as e:
            logger.warning(f"Template placeholder missing: {e} — using raw template")
            user_prompt = template_text
    else:
        # ── Fallback hardcoded prompt ─────────────────────────
        logger.warning(f"No template found for leaf — using hardcoded fallback")
        leaf_type = ctx.get("leaf_type", "concept")
        type_instructions = {
            "concept":           "Explain this concept. Build intuition first, then math. End with 3 key points.",
            "solved_problems":   "Walk through each problem step by step. State formula before applying.",
            "unsolved_problems": "Give hints only. Guide thinking, not answers.",
            "concept_test":      "Explain why each answer is correct or wrong.",
        }
        instruction = type_instructions.get(leaf_type, "Explain this content for a JEE student.")
        raw_content = ctx.get("raw_content", "")

        user_prompt = (
            f"Topic: {topic}\nUnit: {unit}\nDifficulty: {diff}\n\n"
            f"INSTRUCTION: {instruction}\n\n"
            f"REFERENCE CONTENT:\n{raw_content[:3000]}\n\n"
            f"KEY FORMULAE:\n{format_list(key_formulae)}\n\n"
            f"COMMON MISTAKES TO ADDRESS:\n{format_list(common_mistakes)}"
        )

        system_prompt = (
            "You are an expert IIT JEE Physics tutor. "
            "Use the reference content as your knowledge base. "
            "Format responses in clean Markdown with plain text formulae."
        )

    return system_prompt or "", user_prompt


# ── STEP 7: CACHE RESULT ──────────────────────────────────────
def save_explanation(leaf_id: str, template_id: str | None,
                     param_id: str | None, text: str,
                     source_chunks: list) -> None:
    """Cache the generated explanation in public.explanations."""
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
            "explanation_text": text,
            "model":            GEN_MODEL,
        })
        db.commit()
        logger.info(f"Cached explanation for leaf {leaf_id}")
    except Exception as e:
        logger.warning(f"Cache save failed: {e}")
        db.rollback()
    finally:
        db.close()


# ── STEP 8: STREAM GENERATOR ──────────────────────────────────
async def stream_gemini(
    system_prompt: str,
    user_prompt:   str,
    leaf_id:       str,
    template_id:   str | None,
    param_id:      str | None,
) -> AsyncGenerator[str, None]:
    """Streams Gemini output and caches the full response."""
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
        error_msg = f"\n\n**Error:** {str(e)}"
        yield error_msg
        full_text.append(error_msg)
        return

    # Cache after full stream completes
    if full_text:
        save_explanation(
            leaf_id, template_id, param_id,
            "".join(full_text), []
        )


# ── MAIN ENDPOINT ─────────────────────────────────────────────
@router.post("/stream")
async def stream_explanation_endpoint(request: ExplanationRequest):
    """
    Full pipeline:
      1. Fetch leaf + template + parameters from DB
      2. Check cache
      3. Embed + semantic search
      4. Fill template
      5. Stream Gemini
      6. Cache result
    """
    leaf_id = request.leaf_id or request.leafId
    if not leaf_id:
        raise HTTPException(status_code=422, detail="Missing leaf_id.")

    # Step 1: Fetch all context
    ctx = fetch_leaf_context(leaf_id.strip())
    if not ctx:
        raise HTTPException(
            status_code=404,
            detail=f"Leaf node {leaf_id} not found."
        )

    leaf_type   = ctx.get("leaf_type",   "concept")
    topic       = ctx.get("param_topic") or ctx.get("gc_topic") or ctx.get("topic_title") or "Unknown"
    unit        = ctx.get("param_unit")  or ctx.get("gc_unit")  or ctx.get("unit_title")  or "Unknown"
    template_id = str(ctx["template_id"])  if ctx.get("template_id")  else None
    param_id    = str(ctx["param_id"])     if ctx.get("param_id")     else None

    logger.info(f"Stream request: topic={topic} type={leaf_type} "
                f"template={'found' if template_id else 'MISSING'} "
                f"params={'found' if param_id else 'MISSING'}")

    # Step 2: Check cache
    cached = get_cached_explanation(leaf_id)
    if cached:
        logger.info(f"Cache hit for leaf {leaf_id}")
        async def stream_cached():
            yield cached
        return StreamingResponse(
            stream_cached(),
            media_type="text/plain",
            headers={"X-Cache": "HIT", "X-Topic": topic}
        )

    # Step 3: Embed query for semantic search
    top_k_theory    = ctx.get("top_k_theory",    3) or 3
    top_k_examples  = ctx.get("top_k_examples",  3) or 3
    top_k_questions = ctx.get("top_k_questions", 4) or 4
    threshold       = ctx.get("similarity_threshold", 0.25) or 0.25

    embedding = embed_query(topic, unit)

    # Step 4: Semantic search (runs even if embedding fails — returns empty lists)
    theory   = search_generated_content(embedding, "theory",        top_k_theory,    threshold) if embedding else []
    formulae = search_generated_content(embedding, "formulae",      1,               threshold) if embedding else []
    examples = search_generated_content(embedding, "worked_example",top_k_examples,  threshold) if embedding else []
    questions= search_questions(embedding, top_k_questions, threshold)                           if embedding else []

    logger.info(f"Semantic search: theory={len(theory)} formulae={len(formulae)} "
                f"examples={len(examples)} questions={len(questions)}")

    # Step 5: Build prompt from DB template or fallback
    system_prompt, user_prompt = build_prompt(ctx, theory, formulae, examples, questions)

    # Step 6: Stream
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


# ── HEALTH CHECK ──────────────────────────────────────────────
@router.get("/health")
def health():
    return {
        "status":   "ok",
        "model":    GEN_MODEL,
        "gemini":   gemini_client is not None,
        "supabase": supabase is not None,
    }
