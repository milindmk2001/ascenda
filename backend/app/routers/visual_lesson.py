import logging
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.database import get_db

router = APIRouter(prefix="/api/visual-lesson", tags=["Visual Lesson Engine"])
logger = logging.getLogger(__name__)

# ── PYDANTIC APIDOC CONTRACT SCHEMAS ──────────────────────────

class StateSnapshot(BaseModel):
    visibleElements: List[str] = Field(default_factory=list)
    currentAnimationStep: int = 0
    studentAnswer: Optional[str] = None

class TutorActionRequest(BaseModel):
    lessonId: str
    slideId: str
    curriculumNodeId: str
    studentQuestion: str
    currentState: StateSnapshot

class TutorActionResponse(BaseModel):
    action: str  # highlight_existing_elements | replay_animation | explain_with_voice_only | create_new_svg_slide | ask_student_question | give_hint
    targets: List[str] = Field(default_factory=list)
    narration: str
    newSlide: Optional[Dict[str, Any]] = None

# ── ROUTES ───────────────────────────────────────────────────

@router.get("/{curriculum_node_id}")
def get_visual_lesson(curriculum_node_id: str, db: Session = Depends(get_db)):
    """
    Retrieves an orchestrated visual lesson node object from cache.
    Applies the validation criteria: validation_status != 'invalid'
    """
    try:
        query = text("""
            SELECT lesson_id, lesson_json, schema_version, generation_status, validation_status
            FROM public.visual_lesson_cache
            WHERE curriculum_node_id = :node_id 
              AND generation_status = 'complete'
              AND validation_status != 'invalid'
            LIMIT 1
        """)
        
        record = db.execute(query, {"node_id": curriculum_node_id}).mappings().first()
        
        if record:
            return {
                "mode": "visual",
                "source": "cache",
                "payload": record["lesson_json"]
            }
            
        return {
            "mode": "text",
            "reason": "visual_lesson_not_found",
            "fallbackExplanation": "No verified interactive slide layers are cached for this concept node yet. Continuing in classic voice instruction mode."
        }
        
    except Exception as e:
        logger.error(f"Failed to query visual lesson cache for node {curriculum_node_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error scanning storage cache layers."
        )

@router.post("/tutor-action", response_model=TutorActionResponse)
def post_tutor_action(payload: TutorActionRequest, db: Session = Depends(get_db)):
    """
    Accepts contextual analytics state loops to dictate adaptive tutoring behaviors.
    """
    try:
        # Log entry inside public.tutor_interaction_logs via standard execute threads
        log_query = text("""
            INSERT INTO public.tutor_interaction_logs (
                lesson_id, slide_id, student_question, student_answer, interaction_type
            ) VALUES (
                (SELECT lesson_id FROM public.visual_lesson_cache WHERE curriculum_node_id = :node_id LIMIT 1),
                :slide_id, :question, :answer, 'question_asked'
            )
        """)
        db.execute(log_query, {
            "node_id": payload.curriculumNodeId,
            "slide_id": payload.slideId,
            "question": payload.studentQuestion,
            "answer": payload.currentState.studentAnswer
        })
        db.commit()

        return TutorActionResponse(
            action="highlight_existing_elements",
            targets=["question_mark"],
            narration="Let's look closely at the step before this. Do you notice how the terms keep growing?",
            newSlide=None
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Error compiling socratic fallback intercept action: {str(e)}")
        raise HTTPException(status_code=500, detail="Socratic engine routing execution failure.")