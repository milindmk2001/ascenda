from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from google import genai
from google.genai import types
import os

router = APIRouter(prefix="/api/ai", tags=["AI Tutor"])

# Initialize the modern standard Gemini Client
# It automatically reads the GEMINI_API_KEY environment variable from Railway
client = genai.Client()

@router.post("/ask")
async def ask_tutor(request: schemas.AIQueryRequest, db: Session = Depends(get_db)):
    # 1. Get the Persona Template for this subject
    template = db.query(models.PromptTemplate).filter(
        models.PromptTemplate.subject_id == request.subject_id
    ).first()

    # Determine fallback configurations
    system_instruction = "You are a helpful academic tutor." if not template else template.system_instruction
    model_name = "gemini-2.5-flash" if not template else template.model_name

    user_context = f"Student is studying {request.board} {request.grade}. Question: {request.user_query}"
    
    try:
        # Generate content using the new client syntax structure
        response = client.models.generate_content(
            model=model_name,
            contents=user_context,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )
        return {"answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {str(e)}")