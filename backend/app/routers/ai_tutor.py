import os
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Path
from fastapi.responses import StreamingResponse
from pydantic import UUID4
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from google import genai
from google.genai import types

router = APIRouter(prefix="/api/explain", tags=["Ascenda Pro AI Explanation Matrix"])

# ──────────────────────────────────────────────────────────────
# SYSTEM CLOUD PLATFORM INITIALIZATION
# ──────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([SUPABASE_URL, SUPABASE_SERVICE_KEY, GEMINI_API_KEY]):
    print("[SYSTEM WARNING] Critical environment cloud credential tokens are missing.")

# Establish Client Pools
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) if SUPABASE_URL else None
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# ──────────────────────────────────────────────────────────────
# HELPER CONTEXT PARSERS / FORMATTERS
# ──────────────────────────────────────────────────────────────
def format_list(item_list: Optional[List[str]]) -> str:
    if not item_list:
        return "None Specified"
    return ", ".join([f"'{str(x)}'" for x in item_list])

def format_chunks(chunks_response: Any) -> str:
    if not chunks_response or not hasattr(chunks_response, 'data') or not chunks_response.data:
        return "No specific source material context matches extracted reference threshold constraints."
    return "\n\n".join([f"--- Source Snippet ---\n{row.get('content', '')}" for row in chunks_response.data])

def format_questions(questions_response: Any) -> str:
    if not questions_response or not hasattr(questions_response, 'data') or not questions_response.data:
        return "No direct target year questions linked in matching parameters context pool."
    formatted = []
    for i, q in enumerate(questions_response.data, 1):
        opts = q.get('options', {})
        opt_str = " | ".join([f"{k}: {v}" for k, v in opts.items()]) if isinstance(opts, dict) else str(opts)
        formatted.append(
            f"Reference Item {i} [Year: {q.get('exam_year','Unknown')} - Difficulty: {q.get('difficulty','Medium')}]:\n"
            f"Question: {q.get('question_final','')}\n"
            f"Options: {opt_str}\n"
            f"Correct Answer Key: {q.get('correct_answer','')}\n"
            f"Database Explanation: {q.get('explanation','')}"
        )
    return "\n\n=================================\n\n".join(formatted)

# ──────────────────────────────────────────────────────────────
# MAIN STREAM ENGINE ENDPOINT
# ──────────────────────────────────────────────────────────────
@router.post("/{leaf_node_id}")
async def explain_leaf_node(leaf_node_id: UUID4 = Path(..., description="Target leaf structural block node link")):
    """
    RAG Orchestration streaming engine with active state synchronization caching.
    Streams structured Server-Sent Events (SSE).
    """
    if not supabase or not ai_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Cloud data pipelines or AI client engines are uninitialized."
        )

    # 1. Fetch Leaf Node, Active Template text, and Parameters context via Unified Join Extraction
    try:
        node_res = supabase.table("curriculum_tree")\
            .select(
                "id, title, content_type, content_id, exam_type, unit_number, "
                "prompt_templates(id, template_text, system_prompt), "
                "prompt_parameters(topic, unit, difficulty, weightage, key_formulae, common_mistakes, "
                "top_k_theory, top_k_examples, top_k_questions, similarity_threshold)"
            )\
            .eq("id", str(leaf_node_id))\
            .eq("is_leaf", True)\
            .single()\
            .execute()
    except Exception as err:
        raise HTTPException(status_code=404, detail=f"Leaf structural node index parameter lookup failed: {str(err)}")

    node_data = node_res.data
    if not node_data:
        raise HTTPException(status_code=404, detail="Target processing record is not registered as an active leaf.")

    # Destructure parameters cleanly out of joined relations
    template_obj = node_data.get("prompt_templates", {})
    params_obj = node_data.get("prompt_parameters") or {}
    
    if not template_obj:
        raise HTTPException(status_code=500, detail="No prompt template matrix configuration linked to this leaf node.")

    system_prompt = template_obj.get("system_prompt", "")
    template_text = template_obj.get("template_text", "")

    # Hydrate parameters fallback context values maps
    topic = params_obj.get("topic") or node_data.get("title", "Unknown Topic")
    # Gracefully intercept structural text mapping variations
    unit = params_obj.get("unit") or f"Unit {node_data.get('unit_number', 1)}"
    difficulty = params_obj.get("difficulty", "Medium")
    weightage = params_obj.get("weightage", "Medium")
    key_formulae = params_obj.get("key_formulae", [])
    common_mistakes = params_obj.get("common_mistakes", [])
    
    top_k_theory = params_obj.get("top_k_theory", 3)
    top_k_examples = params_obj.get("top_k_examples", 3)
    top_k_questions = params_obj.get("top_k_questions", 4)
    similarity_threshold = params_obj.get("similarity_threshold", 0.25)

    # 2. Check Explanations Cache Layer
    try:
        cache_res = supabase.table("explanations")\
            .select("explanation_text")\
            .eq("curriculum_tree_id", str(leaf_node_id))\
            .eq("is_cached", True)\
            .eq("cache_version", 1)\
            .maybe_single()\
            .execute()
        
        if cache_res and cache_res.data:
            cached_text = cache_res.data.get("explanation_text")
            if cached_text:
                async def stream_cached_payload():
                    # Stream cached text back in structured chunks to preserve frontend layout cadence
                    for block in [cached_text[i:i+120] for i in range(0, len(cached_text), 120)]:
                        yield f"data: {block}\n\n"
                        await asyncio.sleep(0.01)
                    yield "data: [DONE]\n\n"
                return StreamingResponse(stream_cached_payload(), media_type="text/event-stream")
    except Exception as cache_err:
        print(f"[Cache Diagnostics Alert] Bypass non-fatal read: {cache_err}")

    # 3. Embed the Topic Query Vector Space via Gemini
    try:
        query_text = f"{topic} {unit} IITJEE Physics"
        embed_response = ai_client.models.embed_content(
            model='models/gemini-embedding-2',
            contents=query_text,
            config=types.EmbedContentConfig(
                task_type='RETRIEVAL_QUERY', 
                output_dimensionality=3072
            )
        )
        query_vector = embed_response.embeddings[0].values
    except Exception as em_err:
        raise HTTPException(status_code=500, detail=f"Gemini multi-dimensional vector encoding interface failed: {em_err}")

    # 4. Semantic Search Vector Matrix Cross Execution via Supabase RPC Channels
    try:
        theory_res = supabase.rpc('match_generated_content', {
            'query_embedding': query_vector,
            'match_count': int(top_k_theory),
            'filter_unit': unit,
            'filter_topic': topic,
            'filter_content_type': 'theory',
            'similarity_threshold': float(similarity_threshold)
        }).execute()

        formulae_res = supabase.rpc('match_generated_content', {
            'query_embedding': query_vector,
            'match_count': 1,
            'filter_unit': unit,
            'filter_topic': topic,
            'filter_content_type': 'formulae',
            'similarity_threshold': float(similarity_threshold)
        }).execute()

        examples_res = supabase.rpc('match_generated_content', {
            'query_embedding': query_vector,
            'match_count': int(top_k_examples),
            'filter_unit': unit,
            'filter_topic': topic,
            'filter_content_type': 'worked_example',
            'similarity_threshold': float(similarity_threshold)
        }).execute()

        questions_res = supabase.rpc('match_questions', {
            'query_embedding': query_vector,
            'match_count': int(top_k_questions),
            'filter_subject': 'Physics',
            'filter_exam_type': 'JEE',
            'filter_difficulty': difficulty,
            'similarity_threshold': float(similarity_threshold)
        }).execute()
    except Exception as rpc_err:
        raise HTTPException(status_code=500, detail=f"Database knowledge extraction RPC routing failure: {rpc_err}")

    # 5. Hydrate Prompt Templates Engine Context
    hydrated_user_prompt = template_text.format(
        topic=topic,
        unit=unit,
        difficulty=difficulty,
        weightage=weightage,
        key_formulae=format_list(key_formulae),
        common_mistakes=format_list(common_mistakes),
        theory_chunks=format_chunks(theory_res),
        formulae_chunks=format_chunks(formulae_res),
        worked_example_chunks=format_chunks(examples_res),
        jee_questions=format_questions(questions_res)
    )

    # Collect source asset IDs tracking context lineage mapping for accounting fields
    source_chunk_ids = []
    for r in (theory_res.data or []) + (formulae_res.data or []) + (examples_res.data or []):
        if 'content_id' in r: source_chunk_ids.append(r['content_id'])
        elif 'id' in r: source_chunk_ids.append(r['id'])
        
    source_question_ids = [q['id'] for q in (questions_res.data or []) if 'id' in q]

    # 6 & 7. Call Gemini Live Core Generation & Output Generator Stream Engine
    async def sse_response_generator():
        full_output_accumulator = ""
        try:
            response_stream = ai_client.models.generate_content_stream(
                model='gemini-2.0-flash',
                contents=hydrated_user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=3000,
                    temperature=0.6
                )
            )
            
            for chunk in response_stream:
                if chunk.text:
                    text_delta = chunk.text
                    full_output_accumulator += text_delta
                    # Format as precise SSE compliant message payload block
                    yield f"data: {text_delta}\n\n"
                    await asyncio.sleep(0.001) # Yield core pipeline execution context cleanly

        except Exception as gen_err:
            yield f"data: [ERROR]: Content Generation Pipeline Interrupted: {str(gen_err)}\n\n"
            return

        # 8. Commit newly minted raw explanation string to Cache Layer safely asynchronously
        if full_output_accumulator.strip():
            try:
                supabase.table("explanations").insert({
                    "curriculum_tree_id": str(leaf_node_id),
                    "prompt_template_id": template_obj.get("id"),
                    "prompt_parameter_id": params_obj.get("id") if hasattr(params_obj, 'get') else None,
                    "explanation_text": full_output_accumulator,
                    "source_chunk_ids": source_chunk_ids,
                    "source_question_ids": source_question_ids,
                    "generated_by": "gemini-2.0-flash",
                    "is_cached": True,
                    "cache_version": 1
                }).execute()
            except Exception as commit_cache_err:
                print(f"[Cache Layer Alert] Critical write-back commitment slipped execution cycle: {commit_cache_err}")

        yield "data: [DONE]\n\n"

    return StreamingResponse(sse_response_generator(), media_type="text/event-stream")

# ──────────────────────────────────────────────────────────────
# ADMIN CACHE RESET ROUTE
# ──────────────────────────────────────────────────────────────
@router.delete("/{leaf_node_id}/cache", status_code=status.HTTP_200_OK)
def purge_cached_explanation(leaf_node_id: UUID4 = Path(..., description="Target leaf context node")):
    """
    Purges cache records, forcing clean generation cycles on the next customer click.
    """
    try:
        supabase.table("explanations")\
            .delete()\
            .eq("curriculum_tree_id", str(leaf_node_id))\
            .execute()
        return {"status": "purged", "node_id": leaf_node_id, "message": "Cache matrix forced initialization complete."}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Targeted purging engine failure: {str(err)}")