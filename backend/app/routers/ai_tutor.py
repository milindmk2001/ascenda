from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import create_client, Client
import os
from google import genai
from google.genai import types

router = APIRouter(prefix="/api/ai_tutor", tags=["ai_tutor"])

supabase: Client = create_client(
    os.environ["SUPABASE_URL"], 
    os.environ["SUPABASE_ANON_KEY"]
)
gemini_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

class ExplanationRequest(BaseModel):
    curriculum_tree_id: str

async def generate_explanation_stream(content_text: str, meta: dict):
    system_instruction = f"""You are Ascenda's elite AI Physics Tutor, specializing in IIT JEE Main & Advanced preparation.
Your goal is to explain concepts intuitively, breaking down mathematical architectures into functional visualizations.

Topic: {meta.get('topic')}
Unit: {meta.get('unit')}
Difficulty Scale: {meta.get('difficulty')}

Prerequisites to mention: {', '.join(meta.get('prerequisites', []))}
Core Formula Notation: {', '.join(meta.get('key_formulae', []))}
JEE Exam Traps to Call Out: {', '.join(meta.get('common_mistakes', []))}

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
    # Fetch content text column safely
    content_query = supabase.table("generated_content") \
        .select("content_text") \
        .eq("curriculum_tree_id", request.curriculum_tree_id) \
        .maybe_single() \
        .execute()
        
    if not content_query.data:
        raise HTTPException(status_code=404, detail="Core lesson text not found.")
    
    raw_text = content_query.data["content_text"]

    # Fetch prompt parameters join row safely
    param_query = supabase.table("prompt_parameters") \
        .select("topic, unit, difficulty, key_formulae, common_mistakes, prerequisites") \
        .eq("curriculum_tree_id", request.curriculum_tree_id) \
        .maybe_single() \
        .execute()
        
    meta = param_query.data if param_query.data else {
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