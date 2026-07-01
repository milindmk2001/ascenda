from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any
from uuid import UUID

# Import your database session manager and models
from main import get_db # Adjust this import path to match your session utility placement
import models

router = APIRouter(prefix="/api/visual-lesson", tags=["Visual Lessons"])

class VisualLessonResponse(BaseModel):
    mode: str  # "visual" | "text"
    payload: Optional[Dict[str, Any]] = None

@router.get("/{curriculum_node_id}", response_model=VisualLessonResponse)
def get_visual_lesson(curriculum_node_id: str, db: Session = Depends(get_db)):
    """
    Retrieves a cached pre-constructed structured visual SVG lesson from storage.
    Degrades gracefully back to traditional text parsing modes if cache parameters are absent.
    """
    try:
        # Validate that incoming string is a well-formed UUID asset token
        node_uuid = UUID(curriculum_node_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided curriculum token is not a valid UUID format."
        )

    # Query matching validated records inside cache tables
    cache_record = db.query(models.VisualLessonCache).filter(
        models.VisualLessonCache.curriculum_node_id == node_uuid,
        models.VisualLessonCache.validation_status == "valid",
        models.VisualLessonCache.generation_status == "completed"
    ).first()
    
    if cache_record:
        return VisualLessonResponse(
            mode="visual", 
            payload=cache_record.lesson_json
        )
        
    # Standard Fallback Handler: Notify frontend canvas interface to trigger standard stream pipes
    return VisualLessonResponse(
        mode="text", 
        payload=None
    )