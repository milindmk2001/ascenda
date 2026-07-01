from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID
from app.database import SessionLocal

router = APIRouter(prefix="/api/visual-lesson", tags=["Visual Lessons"])

class VisualLessonResponse(BaseModel):
    mode: str  # "visual" | "text"
    payload: Optional[Dict[str, Any]] = None
    lesson_id: Optional[str] = None
    curriculum_node_id: Optional[str] = None
    slide_count: Optional[int] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/{curriculum_node_id}", response_model=VisualLessonResponse)
def get_visual_lesson(curriculum_node_id: str, db: Session = Depends(get_db)):
    try:
        node_uuid = UUID(curriculum_node_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided curriculum token is not a valid UUID format."
        )

    # ✅ Fixed: Added explicit ::uuid typecasting to the bind parameter
    query = text("""
        SELECT lesson_id, curriculum_node_id, lesson_json, slide_count
        FROM public.visual_lesson_cache
        WHERE curriculum_node_id = :node_id::uuid
        AND generation_status = 'complete'
        AND validation_status != 'invalid'
        LIMIT 1
    """)
    
    try:
        result = db.execute(query, {"node_id": str(node_uuid)}).mappings().first()
    except Exception as e:
        print(f"Database execution error: {e}")
        raise HTTPException(status_code=500, detail="Database operation failed")
    
    if result:
        return VisualLessonResponse(
            mode="visual",
            payload=result["lesson_json"],
            lesson_id=str(result["lesson_id"]),
            curriculum_node_id=str(result["curriculum_node_id"]),
            slide_count=result["slide_count"]
        )
        
    return VisualLessonResponse(
        mode="text",
        payload=None,
        lesson_id=None,
        curriculum_node_id=None,
        slide_count=None
    )