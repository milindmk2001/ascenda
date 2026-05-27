"""
ai_tutor.py
Streams Gemini AI explanations for curriculum leaf nodes.

Flow:
  1. Receive leaf_id from frontend
  2. Look up curriculum_tree to get content_id + parent topic title
  3. Fetch generated_content using content_id directly
  4. Stream Gemini explanation using content as context
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, AsyncGenerator
from sqlalchemy import text
import os
import logging

from google import genai
from google.genai import types

router = APIRouter(prefix="/api/ai_tutor", tags=["ai_tutor"])
logger = logging.getLogger(__name__)

# ── CONFIG ────────────────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEN_MODEL      = "gemini-2.0-flash"   # confirmed available

gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None


# ── REQUEST SCHEMA ────────────────────────────────────────────
class ExplanationRequest(BaseModel):
    """
    Accepts leaf_id in either camelCase or snake_case.
    Frontend may send either format.
    """
    leaf_id: Optional[str] = Field(None, alias="leaf_id")
    leafId:  Optional[str] = Field(None, alias="leafId")

    class Config:
        populate_by_name = True


# ── HELPERS ───────────────────────────────────────────────────
def get_leaf_data(leaf_id: str) -> dict:
    """
    Fetches leaf node metadata and its generated content from DB.
    Uses SQLAlchemy session (same connection as curriculum.py).
    Returns dict with content, topic, unit, content_type.
    """
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        # Get leaf node + parent topic title + generated content in one query
        row = db.execute(text("""
            SELECT
                ct.id               AS leaf_id,
                ct.title            AS leaf_title,
                ct.content_type     AS leaf_type,
                ct.unit_number,
                ct.content_id,
                parent.title        AS topic_title,
                gc.content          AS content_text,
                gc.topic            AS gc_topic,
                gc.unit             AS gc_unit,
                gc.difficulty
            FROM public.curriculum_tree ct
            LEFT JOIN public.curriculum_tree parent
              ON parent.id = ct.parent_id
            LEFT JOIN public.generated_content gc
              ON gc.id = ct.content_id
            WHERE ct.id = :leaf_id
              AND ct.is_leaf = true
            LIMIT 1
        """), {"leaf_id": leaf_id}).mappings().first()

        if not row:
            return None

        return dict(row)

    finally:
        db.close()


def build_system_prompt(leaf_type: str) -> str:
    """Returns system prompt appropriate for the leaf content type."""
    base = (
        "You are an expert IIT JEE Physics tutor. "
        "Use the reference content below as your knowledge source. "
        "Format responses in clean Markdown. "
        "Use plain text for formulae (e.g. F = ma, not LaTeX \\frac).\n\n"
    )

    prompts = {
        "concept": (
            base +
            "Explain this concept clearly for a JEE student. "
            "Build physical intuition first, then state the mathematics. "
            "End with 3 key points to remember."
        ),
        "solved_problems": (
            base +
            "Walk through each solved problem step by step. "
            "State the formula before applying it. "
            "Highlight where JEE questions typically add difficulty."
        ),
        "unsolved_problems": (
            base +
            "For each problem, give only a hint — not the full solution. "
            "Guide the student to think, not just compute."
        ),
        "concept_test": (
            base +
            "For each MCQ, explain why the correct answer is right "
            "and why each wrong option is a common misconception."
        ),
    }
    return prompts.get(leaf_type, base + "Explain this content for a JEE student.")


async def stream_explanation(
    content_text: str,
    topic: str,
    unit: str,
    leaf_type: str,
    difficulty: str,
) -> AsyncGenerator[str, None]:
    """Streams Gemini response token by token."""

    if not gemini_client:
        yield "AI engine not configured — GEMINI_API_KEY missing."
        return

    if not content_text:
        yield "No content available for this topic yet."
        return

    system_prompt = build_system_prompt(leaf_type)

    user_prompt = (
        f"Topic: {topic}\n"
        f"Unit: {unit}\n"
        f"Difficulty: {difficulty or 'JEE Standard'}\n"
        f"Content type: {leaf_type}\n\n"
        f"--- REFERENCE CONTENT ---\n"
        f"{content_text[:4000]}"  # cap to avoid token overflow
    )

    try:
        response = gemini_client.models.generate_content_stream(
            model=GEN_MODEL,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.5,
                max_output_tokens=2000,
            )
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text

    except Exception as e:
        logger.error(f"Gemini stream error: {e}")
        yield f"\n\n**Error generating explanation:** {str(e)}"


# ── ENDPOINT ──────────────────────────────────────────────────
@router.post("/stream")
async def stream_explanation_endpoint(request: ExplanationRequest):
    """
    Streams AI explanation for a curriculum leaf node.
    Frontend sends leaf_id → backend fetches content → streams Gemini response.
    """
    # Accept either camelCase or snake_case
    leaf_id = request.leaf_id or request.leafId
    if not leaf_id:
        raise HTTPException(
            status_code=422,
            detail="Missing leaf_id or leafId in request body."
        )

    # Fetch leaf data from DB
    data = get_leaf_data(leaf_id.strip())
    if not data:
        raise HTTPException(
            status_code=404,
            detail=f"Leaf node {leaf_id} not found in curriculum tree."
        )

    topic     = data.get("gc_topic")    or data.get("topic_title") or data.get("leaf_title") or "Unknown Topic"
    unit      = data.get("gc_unit")     or f"Unit {data.get('unit_number', '')}"
    leaf_type = data.get("leaf_type")   or "concept"
    difficulty= data.get("difficulty")  or "Medium"
    content   = data.get("content_text") or ""

    logger.info(f"Streaming explanation: topic={topic} type={leaf_type} content_len={len(content)}")

    return StreamingResponse(
        stream_explanation(content, topic, unit, leaf_type, difficulty),
        media_type="text/plain",
        headers={
            "X-Topic":     topic,
            "X-Leaf-Type": leaf_type,
            "Cache-Control": "no-cache",
        }
    )


# ── HEALTH CHECK ──────────────────────────────────────────────
@router.get("/health")
def ai_tutor_health():
    return {
        "status":  "ok",
        "model":   GEN_MODEL,
        "gemini":  gemini_client is not None,
    }
