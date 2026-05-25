from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional
from supabase import create_client, Client
import os
from google import genai
from google.genai import types

router = APIRouter(prefix="/api/ai_tutor", tags=["ai_tutor"])

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

if not GEMINI_API_KEY:
    gemini_client = None
else:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


class FlexibleExplanationRequest(BaseModel):
    """
    Elastic validation layer accepting camelCase or snake_case payload parameters.
    """
    leaf_id: Optional[str] = Field(None, alias="leaf_id")
    leafId: Optional[str] = Field(None, alias="leafId")
    subject_meta: Optional[str] = None

    class Config:
        populate_by_name = True


async def generate_explanation_stream(content_text: str, meta: dict):
    if not gemini_client:
        yield "AI Core engine client initialization configuration was missing."
        return

    system_prompt = (
        "You are an expert Physics tutor specializing in preparation for competitive entry examinations like IITJEE.\n"
        "Your task is to guide the student using a Socratic dialectic approach based on the reference textbook context provided below.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Never give immediate declarative answers. Guide with concise, clarifying hints.\n"
        "2. Break mathematical concepts down to their fundamental dimensional equations.\n"
        "3. Keep responses beautifully formatted using standard GitHub Flavored Markdown and LaTeX formulas."
    )

    context_payload = (
        f"--- ACTIVE OBJECTIVE ---\nTopic area: {meta['topic']}\nUnit: {meta['unit']}\n\n"
        f"--- TEXTBOOK KNOWLEDGE REFERENCE EXCERPT ---\n{content_text}"
    )

    try:
        response = gemini_client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents=context_payload,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.7
            )
        )
        for chunk in response:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n\n🚨 [Streaming Generation Error Encountered]: {str(e)}"


@router.post("/stream")
async def stream_socratic_explanation(request: FlexibleExplanationRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase framework layer offline.")

    # Extract whichever tracking token variable was populated
    target_id = request.leaf_id or request.leafId
    if not target_id:
        raise HTTPException(status_code=422, detail="Missing valid node identifier parameter field ('leaf_id' / 'leafId').")

    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        
        db_session = SessionLocal()
        tree_node = db_session.execute(
            text("SELECT title, unit_number FROM public.curriculum_tree WHERE id = :tid LIMIT 1"),
            {"tid": str(target_id).strip()}
        ).mappings().first()
        db_session.close()

        if not tree_node:
            raise HTTPException(status_code=404, detail="No matching conceptual leaf row present in curriculum data framework.")

        concept_title = tree_node["title"]

        # Pull textbook theory backing asset matching parsed title criteria
        content_query = supabase.table("generated_content") \
            .select("content, unit, topic, difficulty") \
            .ilike("topic", f"%{concept_title}%") \
            .execute()

        if not content_query or not content_query.data:
            raise HTTPException(status_code=404, detail=f"No underlying textbook assets found for: '{concept_title}'")

        db_record = content_query.data[0]
        
        meta = {
            "topic": db_record.get("topic") or concept_title,
            "unit": db_record.get("unit") or f"Unit Cluster {tree_node['unit_number']}",
            "difficulty": db_record.get("difficulty") or "IITJEE Standard",
        }

        return StreamingResponse(
            generate_explanation_stream(db_record.get("content") or "", meta),
            media_type="text/plain"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal system pipeline breakdown: {str(e)}")