from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import create_client, Client
import os
from google import genai
from google.genai import types

router = APIRouter(prefix="/api/ai_tutor", tags=["ai_tutor"])

# Use .get() defensively to prevent fatal KeyErrors during container build/boot phases
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Initialize clients only if credentials exist, preventing startup crashes
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    print("⚠️ WARNING: SUPABASE_URL or SUPABASE_ANON_KEY is missing from environment variables.")
    supabase = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

if not GEMINI_API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY is missing from environment variables.")
    gemini_client = None
else:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)


class ExplanationRequest(BaseModel):
    curriculum_tree_id: str


async def generate_explanation_stream(content_text: str, meta: dict):
    if not gemini_client:
        yield "❌ [AI Tutor Error]: Gemini API client is not configured on the server."
        return

    system_instruction = f"""You are Ascenda's elite AI Physics Tutor, specializing in IIT JEE Main & Advanced preparation.
Your goal is to explain concepts intuitively, breaking down mathematical architectures into functional visualizations.

Topic: {meta.get('topic')}
Unit: {meta.get('unit')}
Difficulty Scale: {meta.get('difficulty')}

Prerequisites to mention: {', '.join(meta.get('prerequisites', [])) or 'None'}
Core Formula Notation: {', '.join(meta.get('key_formulae', [])) or 'None'}
JEE Exam Traps to Call Out: {', '.join(meta.get('common_mistakes', [])) or 'None'}

Format clean markdown layout headers. Use standard plain mathematical layout configurations.
"""

    prompt = f"Deconstruct and expand comprehensively on this underlying text:\n\n{content_text}"

    try:
        response_stream = gemini_client.models.generate_content_stream(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            )
        )
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n\n❌ [Streaming Context Disrupted]: {str(e)}"


@router.post("/explain")
async def explain_content(request: ExplanationRequest):
    if not supabase:
        raise HTTPException(
            status_code=500, 
            detail="Supabase client is not configured on the server. Check environment variables."
        )

    try:
        # Fetch content text column safely
        content_query = supabase.table("generated_content") \
            .select("content_text") \
            .eq("curriculum_tree_id", request.curriculum_tree_id) \
            .maybe_single() \
            .execute()
            
        if not content_query or not content_query.data:
            raise HTTPException(status_code=404, detail="Core lesson text not found.")
        
        raw_text = content_query.data["content_text"]

        # Fetch prompt parameters join row safely
        param_query = supabase.table("prompt_parameters") \
            .select("topic, unit, difficulty, key_formulae, common_mistakes, prerequisites") \
            .eq("curriculum_tree_id", request.curriculum_tree_id) \
            .maybe_single() \
            .execute()
            
        meta = param_query.data if (param_query and param_query.data) else {
            "topic": "Physics Concept",
            "unit": "General Physics",
            "difficulty": "Medium",
            "key_formulae": [],
            "common_mistakes": [],
            "prerequisites": []
        }

        return StreamingResponse(
            generate_explanation_stream(raw_text, meta), 
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal database transaction failure: {str(e)}")