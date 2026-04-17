from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
import google.generativeai as genai
import os

router = APIRouter(prefix="/api/ai", tags=["AI Tutor"])

# Configure Gemini (Ensure your API Key is in environment variables)
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

@router.post("/ask")
async def ask_tutor(request: schemas.AIQueryRequest, db: Session = Depends(get_db)):
    # 1. Get the Persona Template for this subject
    template = db.query(models.PromptTemplate).filter(
        models.PromptTemplate.subject_id == request.subject_id
    ).first()

    if not template:
        system_instruction = "You are a helpful academic tutor."
    else:
        system_instruction = template.system_instruction

    # 2. Build the context-aware prompt
    model = genai.GenerativeModel(
        model_name=template.model_name if template else "gemini-1.5-flash",
        system_instruction=system_instruction
    )

    user_context = f"Student is studying {request.board} {request.grade}. Question: {request.user_query}"
    
    try:
        response = model.generate_content(user_context)
        return {"answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))