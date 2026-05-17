import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

# Declare separate routers for public and administrative domains
router = APIRouter(prefix="/api/curriculum", tags=["Curriculum Framework"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Curriculum Console"])


# ==========================================
# 1. PYDANTIC DATA TRANSFER SCHEMAS
# ==========================================

class ExamCreate(BaseModel):
    name: str
    code: str

class ExamResponse(BaseModel):
    id: UUID4
    name: str
    code: str
    organisation_id: Optional[UUID4] = None

    class Config:
        from_attributes = True


class ExamSubjectCreate(BaseModel):
    exam_id: UUID4
    name: str
    subject_code: str
    discipline: str = "Competitive Exam"
    video_url: Optional[str] = ""  # Safe fallback for the frontend's empty string payload

class ExamSubjectResponse(BaseModel):
    id: UUID4
    exam_id: UUID4
    name: str
    subject_code: str
    discipline: str
    
    class Config:
        from_attributes = True


# ==========================================
# 2. PUBLIC USER CHANNELS
# ==========================================

@router.get("/exams", response_model=List[ExamResponse])
def get_public_exams(db: Session = Depends(get_db)):
    """Returns all active testing tracks available in the public vector directories."""
    return db.query(models.Exam).all()


# ==========================================
# 3. ADMINISTRATIVE ENGINE CHANNELS (ADMIN)
# ==========================================

# --- EXAM BLUEPRINTS ---

@admin_router.get("/exams", response_model=List[ExamResponse])
def get_admin_exams(db: Session = Depends(get_db)):
    """Fetches track configurations to populate ingestion control panels."""
    return db.query(models.Exam).all()


@admin_router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam_track(payload: ExamCreate, db: Session = Depends(get_db)):
    """Registers a unique testing benchmark archetype code (e.g., IITJEE, NEET)."""
    # Prevent duplicate code tracking footprints
    existing = db.query(models.Exam).filter(models.Exam.code == payload.code.upper().strip()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Testing blueprint layout mapping with system identifier '{payload.code}' already exists."
        )
    
    try:
        new_exam = models.Exam(
            name=payload.name.strip(),
            code=payload.code.upper().strip()
        )
        db.add(new_exam)
        db.commit()
        db.refresh(new_exam)
        return new_exam
    except Exception as err:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database initialization mismatch while updating track configuration: {str(err)}"
        )


# --- EXAM SUBJECT PARTITIONS ---

@admin_router.get("/exam/subjects", response_model=List[ExamSubjectResponse])
def get_admin_exam_subjects(db: Session = Depends(get_db)):
    """Lists all subjects registered across active competitive tracking bounds."""
    return db.query(models.ExamSubject).all()


@admin_router.post("/exam/subjects", response_model=ExamSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_exam_subject_node(payload: ExamSubjectCreate, db: Session = Depends(get_db)):
    """Injects a structured subject partition node directly under a parent track scope."""
    # 1. Verify the parent tracking profile exists
    parent_exam = db.query(models.Exam).filter(models.Exam.id == payload.exam_id).first()
    if not parent_exam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target tracking track link profile identifier '{payload.exam_id}' was not found inside active clusters."
        )

    try:
        # 2. Instantiate and connect the node schema mapping profile
        new_subject = models.ExamSubject(
            exam_id=payload.exam_id,
            name=payload.name.strip(),
            subject_code=payload.subject_code.upper().strip(),
            discipline=payload.discipline.strip()
            # Note: video_url is safely parsed out here since the database model drops it in favor of content tree linkages
        )
        
        db.add(new_subject)
        db.commit()          # Safely write schema elements out to Supabase
        db.refresh(new_subject) # Refresh instance context attributes
        
        return new_subject
        
    except Exception as db_err:
        db.rollback()  # Instantly release pool connection hooks to protect performance cycles
        print(f"CRITICAL ENGINE INGESTION ROLLBACK TRACE: {str(db_err)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanly commit structural matrix mapping to the database partition: {str(db_err)}"
        )