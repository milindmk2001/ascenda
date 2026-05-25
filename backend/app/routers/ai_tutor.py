from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from supabase import create_client, Client
import os
from google import genai
from google.genai import types

router = APIRouter(prefix="/api/ai_tutor", tags=["ai_tutor"])

# Defensive environment parameter reads
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
        yield "AI streaming engine client configuration missing on backend container deployment node."
        return

    # Socratic Dialog System Prompt Blueprint for structural IITJEE Coaching
    system_prompt = (
        "You are an expert Physics tutor specializing in preparation for competitive entry examinations like IITJEE.\n"
        "Your task is to guide the student using a Socratic dialectic approach based on the reference textbook context provided below.\n\n"
        "CRITICAL INSTRUCTIONS:\n"
        "1. Never give immediate declarative answers or solve full calculations right away. Guide with concise, clarifying hints.\n"
        "2. Break mathematical concepts down to their fundamental dimensional equations, units, or primary vector frameworks.\n"
        "3. Address logical fallacies or common conceptual traps associated with this specific topic area if the user seems confused.\n"
        "4. Keep your responses crisp, professional, and targeted toward competitive exam logic strategy.\n"
        "5. Respond using clean, beautifully formatted standard GitHub Flavored Markdown. Use standard LaTeX syntax for formulas ($...$ or $$...$$)."
    )

    context_payload = (
        f"--- CURRENT TARGET CURRICULUM CONTEXT ---\n"
        f"Unit Context Category: {meta.get('unit')}\n"
        f"Target Concept Core Topic: {meta.get('topic')}\n"
        f"Target Benchmarked Rigor Level: {meta.get('difficulty')}\n\n"
        f"--- INGESTED SEED MATERIAL TEXTBOOK EXCERPT ---\n"
        f"{content_text}\n\n"
        f"Dialogue Task: Initiate a supportive, highly strategic conversational engagement with the student regarding this core concept block using your Socratic directives."
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
        yield f"\n\n🚨 [Internal Token Generation Error inside Streaming Pipeline]: {str(e)}"


@router.post("/stream")
async def stream_socratic_explanation(request: dict):
    """
    Streams a tailored conversational response utilizing a relational context bridge 
    built around the selected tree concept leaf element.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase context client layer connection is uninitialized.")

    # FIX: Robust defensive unpacking mapping pattern to completely neutralize all HTTP 422 payload mismatches
    target_leaf_id = request.get("leaf_id") or request.get("leafId") or request.get("curriculum_tree_id")
    
    if not target_leaf_id:
        raise HTTPException(
            status_code=422, 
            detail="Missing parameter payload identifier token field. Expected key variants: 'leaf_id' or 'leafId'."
        )

    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        
        # Open up connection context pool session securely
        db_session = SessionLocal()
        tree_query = text("SELECT title, unit_number FROM public.curriculum_tree WHERE id = :tid LIMIT 1")
        tree_node = db_session.execute(tree_query, {"tid": str(target_leaf_id).strip()}).mappings().first()
        db_session.close()

        if not tree_node:
            raise HTTPException(
                status_code=404, 
                detail="Structural conceptual node tracking index query returned 0 database record matches."
            )

        concept_title = tree_node["title"]

        # Step 2: Query structured ingestion textbook blocks using the resolved title string
        content_query = supabase.table("generated_content") \
            .select("content, unit, topic, difficulty") \
            .ilike("topic", f"%{concept_title}%") \
            .eq("content_type", "theory") \
            .execute()

        # Relax filtering parameters to find alternative rows if no explicit 'theory' type match is returned
        if not content_query or not content_query.data:
            content_query = supabase.table("generated_content") \
                .select("content, unit, topic, difficulty") \
                .ilike("topic", f"%{concept_title}%") \
                .limit(1) \
                .execute()

        if not content_query or not content_query.data:
            raise HTTPException(
                status_code=404, 
                detail=f"No underlying core textbook knowledge assets located inside cluster matches for: '{concept_title}'"
            )

        db_record = content_query.data[0]
        raw_context_text = db_record.get("content") or ""

        # Step 3: Bundle metadata parameters smoothly
        meta = {
            "topic": db_record.get("topic") or concept_title,
            "unit": db_record.get("unit") or f"Unit Cluster Group {tree_node.get('unit_number', 1)}",
            "difficulty": db_record.get("difficulty") or "IITJEE Standard Core Threshold",
        }

        return StreamingResponse(
            generate_explanation_stream(raw_context_text, meta),
            media_type="text/plain"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Fatal core functional pipeline break inside target tutor streaming router: {str(e)}"
        )