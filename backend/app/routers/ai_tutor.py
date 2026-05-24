from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from supabase import create_client, Client
import os
import json
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
    """
    Socratic generator engine that pipes chunked response streams 
    from the Gemini API directly back to CourseReader.jsx.
    """
    if not gemini_client:
        yield "⚠️ AI Tutor Engine configuration error: GEMINI_API_KEY is missing on the server host environment."
        return

    # Parse and extract metadata elements cleanly, supporting both raw JSON strings and standard lists
    def parse_meta_list(value):
        if not value:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                return parsed if isinstance(parsed, list) else [value]
            except Exception:
                return [value]
        return []

    formulae_list = parse_meta_list(meta.get("key_formulae"))
    mistakes_list = parse_meta_list(meta.get("common_mistakes"))
    prereqs_list = parse_meta_list(meta.get("prerequisites"))

    # Construct the Socratic curriculum directive layout
    socratic_prompt = f"""
    You are the Ascenda AI Socratic Tutor, an elite competitive exam specialist for IITJEE and NEET physics.
    Your mission is to provide an immersive, deeply conceptual, and intuitive breakdown of the provided core lesson content.

    === TARGET TOPIC META ===
    - Unit Context: {meta.get("unit", "General Core Unit")}
    - Topic Focus: {meta.get("topic", "Physics Concept Definition")}
    - Target Difficulty Level: {meta.get("difficulty", "Medium / Advanced Assessment")}
    - Core Core Equations: {', '.join(formulae_list) if formulae_list else "Apply standard derived dimensional principles."}
    - Critical Trap Warning Zones: {', '.join(mistakes_list) if mistakes_list else "Confusing base structural variables, signs, and algebraic conversions."}
    - Prerequisite Dependencies: {', '.join(prereqs_list) if prereqs_list else "Basic physical intuition and algebraic expressions."}

    === CORE INSTRUCTIONAL CONTENT TO ELABORATE ===
    {content_text}

    === RENDER FORMAT RULES ===
    1. Adopt a rigorous yet hyper-intuitive tone (analogies are highly encouraged to ground complex physical abstractions).
    2. Format using crisp, clean Markdown layouts with explicit bullet structures.
    3. Use standard LaTeX block equations ($$ ... $$) and inline elements ($ ... $) for all physical expressions and dimensions to ensure the math canvas elements render cleanly in CourseReader.jsx.
    4. Structure your response into exactly three concise Socratic headers:
       - ## Conceptual Intuition & Core Mechanics (Deep dive into *why* this works fundamentally)
       - ## Strategic Exam Application (How IITJEE/NEET questions frame this topic, highlighting traps and conversion limits)
       - ## Socratic Inquiry (Leave the student with 1 high-yield, open-ended thought challenge to solidify their logic)

    Generate the Socratic explanation stream directly now:
    """

    try:
        # Request stream generation via the official Google GenAI model pipeline
        response_stream = gemini_client.models.generate_content_stream(
            model='gemini-2.5-flash',
            contents=socratic_prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                top_p=0.95
            )
        )
        
        for chunk in response_stream:
            if chunk.text:
                yield chunk.text
                
    except Exception as e:
        yield f"\n\n⚠️ [Streaming Pipeline Error: Failed to generate continuous token blocks from Gemini API - {str(e)}]"


@router.post("/stream")
async def stream_socratic_explanation(request: ExplanationRequest):
    """
    Targets interactive layout triggers from CourseReader.jsx.
    Fetches context parameters from your Supabase data schema and pushes a streaming response.
    """
    if not supabase:
        raise HTTPException(
            status_code=500, 
            detail="Supabase infrastructure connection variables are not configured on the deployment backend."
        )

    try:
        # Fetching content directly based on your real database table layout
        # (Where the structural ID acts as the main reference lookup key)
        content_query = supabase.table("generated_content") \
            .select("id, topic, unit, content, difficulty, formulae") \
            .eq("id", request.curriculum_tree_id) \
            .maybe_single() \
            .execute()
            
        if not content_query or not content_query.data:
            raise HTTPException(
                status_code=404, 
                detail=f"Target lesson content reference '{request.curriculum_tree_id}' could not be located in your database cluster."
            )
        
        db_record = content_query.data
        
        # Pull text from your true text data column ('content')
        raw_text = db_record.get("content") or ""
        if not raw_text.strip():
            raise HTTPException(
                status_code=400,
                detail="The matching database record exists, but its core content text parameter is empty."
            )
        
        # Build prompt metadata dictionary elements on the fly out of your real row variables
        meta = {
            "topic": db_record.get("topic") or "Physics Concept",
            "unit": db_record.get("unit") or "Units and Measurements",
            "difficulty": db_record.get("difficulty") or "Medium",
            "key_formulae": db_record.get("formulae") or [],
            "common_mistakes": [], # Optional placeholder fields for future enhancements
            "prerequisites": []
        }

        # Return a continuous StreamingResponse stream back to the UI markdown panel
        return StreamingResponse(
            generate_explanation_stream(raw_text, meta), 
            media_type="text/plain"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database concept processing transaction dropped inside AI Tutor layer: {str(e)}"
        )