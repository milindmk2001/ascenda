from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
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


async def generate_explanation_stream(content_text: str, meta: dict):
    if not gemini_client:
        yield "AI configuration missing on server deploy backend."
        return

    # Socratic Prompting Framework tailored for IITJEE standards
    system_prompt = (
        "You are an expert Physics tutor specializing in preparation for competitive entry examinations like IITJEE.\n"
        "Your task is to guide the student using a Socratic dialectic approach based on the reference textbook context provided below.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Never give immediate declarative answers. Guide with concise, clarifying hints.\n"
        "2. Break mathematical concepts down to their fundamental dimensional equations.\n"
        "3. Incorporate rigorous conceptual checking milestones.\n"
        "4. Output format should be clean Markdown text syntax matching streaming chunk components.\n"
    )

    context_payload = (
        f"--- CURRENT CURRICULUM TOPIC AREA ---\n"
        f"Unit Framework: {meta['unit']}\n"
        f"Target Concept: {meta['topic']}\n"
        f"Academic Complexity Standard: {meta['difficulty']}\n\n"
        f"--- CORE TEXTBOOK EXCERPT ---\n"
        f"{content_text}"
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
    except Exception as stream_err:
        yield f"\n\n💥 AI Stream Interrupted: {str(stream_err)}"


@router.post("/stream")
async def stream_socratic_explanation(request: dict):
    """
    Accepts raw dynamic dictionary mapping configurations directly from CourseReader.jsx
    to prevent Pydantic 422 processing walls, translating structural nodes into text blocks.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase client connection missing.")

    # Accept fallback parameters directly matching CourseReader configurations
    target_leaf_id = request.get("leafId") or request.get("curriculum_tree_id")
    if not target_leaf_id:
        raise HTTPException(status_code=422, detail="Missing parameter payload identifier token: 'leafId'.")

    try:
        # Step 1: Query the structural node text string from your public tree table mapping topology
        from app.database import SessionLocal
        from sqlalchemy import text
        
        db_session = SessionLocal()
        tree_query = text("SELECT title, unit_number FROM public.curriculum_tree WHERE id = :tid LIMIT 1")
        tree_node = db_session.execute(tree_query, {"tid": target_leaf_id.strip()}).mappings().first()
        db_session.close()

        if not tree_node:
            raise HTTPException(status_code=404, detail="Structural conceptual node tracker lookup returned 0 mapping results.")

        concept_title = tree_node["title"]

        # Step 2: Grab the matching underlying textbook knowledge theory block using the topic string name
        content_query = supabase.table("generated_content") \
            .select("id, topic, unit, content, content_type, difficulty") \
            .ilike("topic", f"%{concept_title}%") \
            .eq("content_type", "theory") \
            .limit(1) \
            .execute()

        # Fallback sequence: if strict 'theory' content filters fail, relax parameters to any match for the topic area
        if not content_query or not content_query.data:
            content_query = supabase.table("generated_content") \
                .select("id, topic, unit, content, content_type, difficulty") \
                .ilike("topic", f"%{concept_title}%") \
                .limit(1) \
                .execute()

        if not content_query or not content_query.data:
            raise HTTPException(status_code=404, detail=f"No underlying textbook core files located matching: '{concept_title}'")

        db_record = content_query.data[0]
        raw_context_text = db_record.get("content") or ""

        # Step 3: Package up meta payload attributes for the LLM systemic prompt engine
        meta = {
            "topic": db_record.get("topic") or concept_title,
            "unit": db_record.get("unit") or f"Unit Group {tree_node.get('unit_number', 1)}",
            "difficulty": db_record.get("difficulty") or "IITJEE Examination Threshold",
        }

        return StreamingResponse(
            generate_explanation_stream(raw_context_text, meta),
            media_type="text/plain"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Core execution breakdown in streaming logic: {str(e)}")