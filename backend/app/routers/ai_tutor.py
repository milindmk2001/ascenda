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
GEN_MODEL        = "gemini-2.5-flash"  # premium generation target

if not SUPABASE_URL or not SUPABASE_KEY:
    supabase = None
    logger.warning("Supabase environment variables missing; database actions will fail.")
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

if not GEMINI_API_KEY:
    gemini_client = None
    logger.warning("GEMINI_API_KEY environment variable missing.")
else:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


# ── REQUEST VALIDATOR SCHEMA ──────────────────────────────────
class ExplanationRequest(BaseModel):
    """
    Elastic validation layer accepting camelCase or snake_case payload parameters.
    """
    leaf_id: Optional[str] = Field(None, alias="leaf_id")
    leafId:  Optional[str] = Field(None, alias="leafId")

    class Config:
        populate_by_name = True


# ── DATABASE EXTRACTION HELPERS ────────────────────────────────
def fetch_leaf_context(leaf_id: str) -> Optional[dict]:
    """
    Queries curriculum tree and left joins custom prompt configurations.
    """
    if not supabase:
        return None
    try:
        query = """
            SELECT 
                ct.id AS leaf_id,
                ct.title AS leaf_title,
                ct.content_type AS leaf_type,
                ct.unit_number,
                ct.prompt_template_id,
                ct.prompt_param_id,
                pt.system_prompt,
                pt.template_text,
                pp.difficulty,
                pp.weightage,
                pp.key_formulae,
                pp.common_mistakes,
                parent.title AS topic_title
            FROM public.curriculum_tree ct
            LEFT JOIN public.curriculum_tree parent ON parent.id = ct.parent_id
            LEFT JOIN public.prompt_templates pt   ON pt.id = ct.prompt_template_id AND pt.is_active = true
            LEFT JOIN public.prompt_parameters pp ON pp.id = ct.prompt_param_id
            WHERE ct.id = :leaf_id AND ct.is_leaf = true
            LIMIT 1
        """
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            row = db.execute(text(query), {"leaf_id": leaf_id}).mappings().first()
            return dict(row) if row else None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error extracting tracking tokens from curriculum: {e}")
        return None


def lookup_cached_explanation(leaf_id: str, template_id: Optional[str], param_id: Optional[str]) -> Optional[str]:
    """
    Returns hit from response cache layer to completely bypass unnecessary LLM spend.
    """
    if not supabase:
        return None
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            query = """
                SELECT generated_text FROM public.explanations
                WHERE leaf_id = :lid 
                  AND json_template_id IS NOT DISTINCT FROM :tid
                  AND json_param_id IS NOT DISTINCT FROM :pid
                LIMIT 1
            """
            row = db.execute(text(query), {
                "lid": leaf_id,
                "tid": template_id,
                "pid": param_id
            }).mappings().first()
            return row["generated_text"] if row else None
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Cache checking layer malfunctioned: {e}")
        return None


def commit_explanation_to_cache(leaf_id: str, template_id: Optional[str], param_id: Optional[str], response_text: str):
    """
    Saves compiled text to persistent store.
    """
    if not supabase or not response_text.strip():
        return
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            db.execute(text("""
                INSERT INTO public.explanations (id, leaf_id, json_template_id, json_param_id, generated_text)
                VALUES (:id, :lid, :tid, :pid, :txt)
                ON CONFLICT (leaf_id, json_template_id, json_param_id) 
                DO UPDATE SET generated_text = EXCLUDED.generated_text, updated_at = NOW()
            """), {
                "id": str(uuid4()),
                "lid": leaf_id,
                "tid": template_id,
                "pid": param_id,
                "txt": response_text
            })
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Writing to persistent store failed: {e}")


# ── SEMANTIC CONTENT VECTOR SEARCH PIPELINE ───────────────────
def extract_text_embedding(text_query: str) -> Optional[list]:
    if not gemini_client or not text_query:
        return None
    try:
        res = gemini_client.models.embed_content(
            model="text-embedding-004",
            contents=text_query
        )
        if res.embeddings and len(res.embeddings) > 0:
            return res.embeddings[0].values
        return None
    except Exception as e:
        logger.error(f"Vector embedding failure: {e}")
        return None


def search_generated_content(embedding: list, content_type: str, match_count: int, threshold: float) -> list:
    if not supabase:
        return []
    try:
        res = supabase.rpc("match_generated_content", {
            "query_embedding": embedding,
            "match_type": content_type,
            "match_threshold": threshold,
            "match_count": match_count
        }).execute()
        return res.data if res and res.data else []
    except Exception as e:
        logger.error(f"match_generated_content error for {content_type}: {e}")
        return []


def search_questions(embedding: list, match_count: int, threshold: float) -> list:
    if not supabase:
        return []
    try:
        res = supabase.rpc("match_questions", {
            "query_embedding": embedding,
            "match_threshold": threshold,
            "match_count": match_count
        }).execute()
        return res.data if res and res.data else []
    except Exception as e:
        logger.error(f"match_questions error: {e}")
        return []


# ── PROMPT ASSEMBLERS ──────────────────────────────────────────
def format_list(item) -> str:
    if not item: return "None listed."
    if isinstance(item, list): return "\n".join([f"- {str(x)}" for x in item])
    return str(item)


def format_chunks(chunks: list) -> str:
    if not chunks: return "No structured reference blocks extracted."
    out = []
    for c in chunks:
        hdr = f"### Asset Source: {c.get('topic','')} ({c.get('subtopic','')})"
        out.append(f"{hdr}\n{c.get('content','')}")
    return "\n\n".join(out)


def format_questions(questions: list) -> str:
    if not questions: return "No past question items matched standard threshold levels."
    out = []
    for q in questions:
        meta = f"Question ID: {q.get('id','')} | Source: {q.get('source_file','')}"
        body = f"Question Body: {q.get('question_text','')}"
        sol  = f"Target Explanation Path:\n{q.get('explanation','')}"
        out.append(f"--- {meta} ---\n{body}\n{sol}")
    return "\n\n".join(out)


def build_prompt(ctx: dict, theory: list, formulae: list, examples: list, questions: list):
    """
    Resolves placeholders safely. Falls back to hardcoded text safely if DB row drops out.
    """
    topic     = ctx.get("gc_topic") or ctx.get("topic_title") or ctx.get("leaf_title") or "Physics Concept"
    unit      = ctx.get("gc_unit") or f"Unit Section {ctx.get('unit_number','')}"
    diff      = ctx.get("difficulty") or "IITJEE Standard"
    weightage = ctx.get("weightage") or "Not Specified"
    
    key_formulae    = ctx.get("key_formulae") or []
    common_mistakes = ctx.get("common_mistakes") or []

    system_prompt = ctx.get("system_prompt")
    template_text = ctx.get("template_text")

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
            return system_prompt, user_prompt
        except Exception as e:
            logger.error(f"Template parsing mismatch: {e}. Reverting to baseline prompt structures.")

    # ── HARDCODED CODE FALLBACKS ───────────────────────────────────
    logger.warning("Using hardcoded code fallback system prompt.")
    leaf_type = ctx.get("leaf_type", "concept")
    
    type_instructions = {
        "concept":           "Deliver an exhaustive, crystal-clear conceptual explanation. Break down the physical mechanics from ground principles to advanced analytical insights. Do not ask questions.",
        "solved_problems":   "Deconstruct each physics problem analytically. Provide full, unedited derivations and complete mathematical solutions from start to finish.",
        "unsolved_problems": "Provide a complete analytical blueprint detailing the step-by-step physics required to solve the scenario. Do not hide answers or leave variables isolated for the user to solve.",
        "concept_test":      "Provide an authoritative breakdown explaining why each option is conceptually valid or physically impossible.",
    }
    instruction = type_instructions.get(leaf_type, "Break down the target node material for an advanced IIT-JEE physics candidate.")

    user_prompt = (
        f"Topic focus: {topic}\n"
        f"Unit Cluster: {unit}\n"
        f"Difficulty: {diff} (Weightage: {weightage})\n\n"
        f"Core Task Instruction:\n{instruction}\n\n"
        f"--- RELEVANT TEXTBOOK EXCERPTS ---\n{format_chunks(theory)}\n\n"
        f"--- CONTEXT FORMULAE ---\n{format_chunks(formulae)}\n\n"
        f"--- CONTEXT WORKED EXAMPLES ---\n{format_chunks(examples)}\n\n"
        f"--- RELEVANT PAST YEAR QUESTIONS ---\n{format_questions(questions)}"
    )

    system_prompt = (
        "You are an expert female IIT JEE Physics professor. Give a comprehensive, continuous oral lecture breakdown "
        "of the topic material using the reference content as your source data. Do not stop to quiz the student, "
        "do not ask leading questions, and do not use chat check-ins."
    )

    return system_prompt, user_prompt


# ── STREAMING GENERATION ENGINES ──────────────────────────────
async def stream_gemini(system_prompt: str, user_prompt: str, leaf_id: str, template_id: Optional[str], param_id: Optional[str]) -> AsyncGenerator[str, None]:
    if not gemini_client:
        yield "AI Engine unavailable — missing API credentials."
        return

    compiled_text_chunks = []
    try:
        response = gemini_client.models.generate_content_stream(
            model=GEN_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt or None,
                temperature=0.3,             # Lowered slightly for more stable, professional cadence
                max_output_tokens=2000,
                
                # ── NATIVE VOICE PIPELINE ADDITIONS ───────────────────
                response_modalities=["TEXT", "AUDIO"],  # Requests both Markdown text and live audio streams
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name="Puck"  # "Puck" or "Fenrir" are high-quality female profiles
                        )
                    )
                )
            )
        )
        for chunk in response:
            if chunk.text:
                compiled_text_chunks.append(chunk.text)
                yield chunk.text

        # Background save to cache layer to bypass repeated LLM compute spend
        full_response = "".join(compiled_text_chunks)
        if full_response.strip():
            commit_explanation_to_cache(leaf_id, template_id, param_id, full_response)

    except Exception as e:
        logger.error(f"Gemini streaming transaction failure: {e}")
        yield f"\n\n[Streaming Session Interrupted: {str(e)}]"


# ── PRIMARY CONTROLLER ENDPOINT ────────────────────────────────
@router.post("/stream")
async def stream_explanation_endpoint(request: ExplanationRequest):
    """
    Orchestration Entrypoint: Validates node metadata token -> checks cache -> 
    embeds query -> runs semantic content match -> queries Gemini -> streams text + speech chunks.
    """
    leaf_id = request.leaf_id or request.leafId
    if not leaf_id:
        raise HTTPException(status_code=422, detail="Missing parameter: 'leaf_id' or 'leafId' required.")

    ctx = fetch_leaf_context(leaf_id.strip())
    if not ctx:
        raise HTTPException(status_code=404, detail="Requested conceptual leaf configuration node completely missing.")

    template_id = ctx.get("prompt_template_id")
    param_id    = ctx.get("prompt_param_id")

    # Step 2: Hit Cache Store to completely avoid redundant generation spending
    cached_hit = lookup_cached_explanation(leaf_id, template_id, param_id)
    if cached_hit:
        logger.info(f"Cache pipeline HIT for leaf node: {leaf_id}")
        async def stream_cached_text() -> AsyncGenerator[str, None]:
            yield cached_hit
        return StreamingResponse(
            stream_cached_text(),
            media_type="text/plain",
            headers={"X-Cache": "HIT", "Cache-Control": "no-cache"}
        )

    # Step 3: Run Vector Embedder mappings for structural semantic alignment
    topic     = ctx.get("gc_topic") or ctx.get("topic_title") or ctx.get("leaf_title") or "Physics"
    leaf_type = ctx.get("leaf_type") or "concept"
    
    embedding = extract_text_embedding(f"IIT JEE Physics: {topic} {leaf_type}")

    # Step 4: Extract semantic chunks from Supabase Vector Database
    threshold = 0.35
    top_k_theory = 3 if leaf_type == "concept" else 1
    top_k_examples = 3 if leaf_type == "solved_problems" else 1
    top_k_questions = 4 if leaf_type in ["unsolved_problems", "concept_test"] else 1

    theory   = search_generated_content(embedding, "theory",        top_k_theory,    threshold) if embedding else []
    formulae = search_generated_content(embedding, "formulae",      1,               threshold) if embedding else []
    examples = search_generated_content(embedding, "worked_example",top_k_examples,  threshold) if embedding else []
    questions= search_questions(embedding, top_k_questions, threshold)                           if embedding else []

    logger.info(f"Semantic search: theory={len(theory)} formulae={len(formulae)} "
                f"examples={len(examples)} questions={len(questions)}")

    # Step 5: Build system instruction prompt payload values
    system_prompt, user_prompt = build_prompt(ctx, theory, formulae, examples, questions)

    # Step 6: Stream mixed-modality package data back to target layouts
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


# ── HEALTH MONITOR CHECK ───────────────────────────────────────
@router.get("/health")
def health():
    return {
        "status":   "ok",
        "model":    GEN_MODEL,
        "gemini":   gemini_client is not None,
        "supabase": supabase is not None
    }