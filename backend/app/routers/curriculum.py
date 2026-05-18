import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session

from app import models
from app.database import get_db

router = APIRouter(prefix="/api/curriculum", tags=["Curriculum Public Framework"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Curriculum Ingestion Console"])


# ==========================================
# 1. PYDANTIC DATA TRANSFER SCHEMAS
# ==========================================

# --- K-12 Schema Matrix ---
class GradeCreate(BaseModel):
    name: str
    level: Optional[str] = None
    org_id: Optional[UUID4] = None

class GradeResponse(BaseModel):
    id: UUID4
    name: Optional[str]
    level: Optional[str]
    org_id: Optional[UUID4] = None

    class Config:
        from_attributes = True

class RegularSubjectCreate(BaseModel):
    name: str
    subject_code: str
    discipline: str = "Science"
    grade_id: UUID4
    video_url: Optional[str] = ""

class RegularSubjectResponse(BaseModel):
    id: UUID4
    name: str
    subject_code: str
    discipline: str
    grade_id: Optional[UUID4] = None
    video_url: Optional[str] = None

    class Config:
        from_attributes = True

# --- Competitive Exam Schema Matrix ---
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
    video_url: Optional[str] = ""

class ExamSubjectResponse(BaseModel):
    id: UUID4
    exam_id: UUID4
    name: str
    subject_code: str
    discipline: str
    
    class Config:
        from_attributes = True

# --- Hub View Resolution Schema ---
class HubCourseCardResponse(BaseModel):
    id: UUID4
    name: str
    subject_code: str
    discipline: str
    track_type: str  # "K12" or "COMPETITIVE"
    meta_tag: str    # e.g., "CBSE-11" or "IITJEE"

    class Config:
        from_attributes = True


# ==========================================
# 2. PUBLIC CORE UNIFIED CHANNELS
# ==========================================

@router.get("/exams", response_model=List[ExamResponse])
def get_public_exams(db: Session = Depends(get_db)):
    """Returns active test blueprints in the public directory."""
    return db.query(models.Exam).all()


@router.get("/resolve-hub", response_model=List[HubCourseCardResponse])
def resolve_hub_view_content(
    track_code: str, 
    grade_name: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Unified public content engine.
    If track_code matches a competitive exam, ignore grade and return exam subjects.
    Otherwise, filter standard K-12 modules by both track/board and grade tier.
    """
    # 1. Standardize text layout input keys
    cleaned_track = track_code.upper().strip().replace("-", "") # "IIT-JEE" -> "IITJEE"
    
    # 2. Check if track_code points to a Competitive Exam Track (IITJEE / NEET)
    exam_track = db.query(models.Exam).filter(models.Exam.code == cleaned_track).first()
    
    if exam_track:
        # Competitive track matched -> fetch directly from exam_subjects, skip grade constraints
        subjects = db.query(models.ExamSubject).filter(models.ExamSubject.exam_id == exam_track.id).all()
        return [
            HubCourseCardResponse(
                id=s.id,
                name=s.name,
                subject_code=s.subject_code,
                discipline=s.discipline,
                track_type="COMPETITIVE",
                meta_tag=exam_track.code
            ) for s in subjects
        ]
        
    # 3. Fallback: Assume standard K-12 track (CBSE, ICSE) requiring Grade specificity
    if not grade_name:
        return []
        
    # Locate the target grade entry matching name constraint criteria (e.g., "11", "12", "Class 11")
    cleaned_grade = grade_name.lower().replace("class", "").strip() # normalize inputs
    grade_node = db.query(models.Grade).filter(models.Grade.name.like(f"%{cleaned_grade}%")).first()
    
    if not grade_node:
        return []
        
    k12_subjects = db.query(models.RegularSubject).filter(models.RegularSubject.grade_id == grade_node.id).all()
    return [
        HubCourseCardResponse(
            id=s.id,
            name=s.name,
            subject_code=s.subject_code,
            discipline=s.discipline,
            track_type="K12",
            meta_tag=f"{track_code.upper().strip()}-{grade_node.name}"
        ) for s in k12_subjects
    ]


# ==========================================
# 3. ADMINISTRATIVE DATA MANAGEMENT (ADMIN)
# ==========================================

# --- PARTITION A: K-12 TRACK ARCHITECTURE ---

@admin_router.get("/grades", response_model=List[GradeResponse])
def get_admin_grades(db: Session = Depends(get_db)):
    """Fetches all active grade levels to satisfy frontend application dashboard synchronizations."""
    return db.query(models.Grade).all()

@admin_router.post("/grades", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
def create_admin_grade(payload: GradeCreate, db: Session = Depends(get_db)):
    """Registers a grade level node context."""
    try:
        new_grade = models.Grade(
            name=payload.name.strip(),
            level=payload.level.strip() if payload.level else None,
            org_id=payload.org_id
        )
        db.add(new_grade)
        db.commit()
        db.refresh(new_grade)
        return new_grade
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(err))


@admin_router.get("/regular/subjects", response_model=List[RegularSubjectResponse])
def get_admin_regular_subjects(db: Session = Depends(get_db)):
    """Resolves standard K-12 regular subjects to prevent schema initialization 404 crashes."""
    return db.query(models.RegularSubject).all()

@admin_router.post("/regular/subjects", response_model=RegularSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_admin_regular_subject(payload: RegularSubjectCreate, db: Session = Depends(get_db)):
    """Injects a standardized K-12 program subject structural baseline mapping."""
    try:
        new_sub = models.RegularSubject(
            name=payload.name.strip(),
            subject_code=payload.subject_code.upper().strip(),
            discipline=payload.discipline.strip(),
            grade_id=payload.grade_id,
            video_url=payload.video_url
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)
        return new_sub
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(err))


# --- PARTITION B: COMPETITIVE EXAM TRACKS ---

@admin_router.get("/exams", response_model=List[ExamResponse])
def get_admin_exams(db: Session = Depends(get_db)):
    """Fetches testing tracks for ingestion panels."""
    return db.query(models.Exam).all()

@admin_router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_exam_track(payload: ExamCreate, db: Session = Depends(get_db)):
    """Registers a unique testing track footprint identifier."""
    existing = db.query(models.Exam).filter(models.Exam.code == payload.code.upper().strip()).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Blueprint configuration code mapping targeting '{payload.code}' already exists."
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
        raise HTTPException(status_code=500, detail=f"Database update rollback: {str(err)}")


# --- PARTITION C: COMPETITIVE EXAM SUBJECT MAPS ---

@admin_router.get("/exam/subjects", response_model=List[ExamSubjectResponse])
def get_admin_exam_subjects(db: Session = Depends(get_db)):
    """Lists registered exam domain components."""
    return db.query(models.ExamSubject).all()

@admin_router.post("/exam/subjects", response_model=ExamSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_exam_subject_node(payload: ExamSubjectCreate, db: Session = Depends(get_db)):
    """Safely handles dashboard payloads to build data objects without column matching crashes."""
    parent_exam = db.query(models.Exam).filter(models.Exam.id == payload.exam_id).first()
    if not parent_exam:
        raise HTTPException(
            status_code=404,
            detail=f"Target tracking track profile code link '{payload.exam_id}' missing."
        )
    try:
        new_subject = models.ExamSubject(
            exam_id=payload.exam_id,
            name=payload.name.strip(),
            subject_code=payload.subject_code.upper().strip(),
            discipline=payload.discipline.strip()
        )
        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)
        return new_subject
    except Exception as db_err:
        db.rollback()
        print(f"CRITICAL BACKEND OPERATION ROLLBACK: {str(db_err)}")
        raise HTTPException(status_code=500, detail=str(db_err))