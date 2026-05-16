from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List
from uuid import UUID

# 1. Standard Router for the User/Reader view
router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])

# 2. Admin Router for management
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["admin-curriculum"])

# --- TREE ENDPOINT (For the Course Reader Sidebar) ---
@router.get("/subjects/{subject_id}/tree", response_model=List[schemas.CurriculumNode])
def get_curriculum_tree(subject_id: UUID, db: Session = Depends(get_db)):
    # Query only top-level nodes; 'children' will be nested automatically via models.py
    nodes = db.query(models.CurriculumTree).filter(
        models.CurriculumTree.subject_id == subject_id,
        models.CurriculumTree.parent_id == None
    ).all()
    
    return nodes if nodes else []

# --- ADMIN: GRADES ---
# Frontend fetches from: GET /api/admin/curriculum/grades
@admin_router.get("/grades", response_model=List[schemas.Grade])
def get_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

# Frontend posts to: POST /api/admin/curriculum/grades
@admin_router.post("/grades", response_model=schemas.Grade, status_code=201)
def create_grade(payload: schemas.AdminGradeCreate, db: Session = Depends(get_db)):
    string_level = str(payload.level)
    
    new_grade = models.Grade(
        level=string_level,
        name=payload.name if payload.name else f"Grade {string_level}",
        org_id=payload.org_id
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

# --- ADMIN: SUBJECTS ---
# FIXED: Frontend fetches from: GET /api/admin/curriculum/regular/subjects
@admin_router.get("/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()

# FIXED: Frontend posts to: POST /api/admin/curriculum/subjects
@admin_router.post("/subjects", response_model=schemas.RegularSubject, status_code=201)
def create_regular_subject(payload: schemas.AdminSubjectCreate, db: Session = Depends(get_db)):
    # Enforce parent structural tree boundary validation checks
    grade = db.query(models.Grade).filter(models.Grade.id == payload.grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Target container Grade level identifier missing.")

    new_sub = models.RegularSubject(
        name=payload.name,
        subject_code=payload.subject_code.upper(),
        grade_id=payload.grade_id,
        discipline=payload.discipline if payload.discipline else "General",
        video_url=payload.video_url if payload.video_url else ""
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

# --- ADMIN: SUBJECT AREAS (Units) ---
@admin_router.get("/regular/subject-areas", response_model=List[schemas.RegularSubjectArea])
def get_regular_subject_areas(db: Session = Depends(get_db)):
    return db.query(models.RegularSubjectArea).all()

@admin_router.post("/regular/subject-areas", response_model=schemas.RegularSubjectArea)
def create_regular_subject_area(area: schemas.RegularSubjectAreaCreate, db: Session = Depends(get_db)):
    new_area = models.RegularSubjectArea(
        title=area.title,
        sequence_order=area.sequence_order,
        subject_id=area.subject_id
    )
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area

# --- ADMIN: CHAPTERS ---
@admin_router.get("/regular/chapters", response_model=List[schemas.RegularChapter])
def get_regular_chapters(db: Session = Depends(get_db)):
    return db.query(models.RegularChapter).all()

@admin_router.post("/regular/chapters", response_model=schemas.RegularChapter)
def create_regular_chapter(chap: schemas.RegularChapterCreate, db: Session = Depends(get_db)):
    new_chap = models.RegularChapter(
        title=chap.title,
        sequence_order=chap.sequence_order,
        subject_area_id=chap.subject_area_id
    )
    db.add(new_chap)
    db.commit()
    db.refresh(new_chap)
    return new_chap

# --- ADMIN: PROMPT TEMPLATES ---
@admin_router.get("/prompt-templates", response_model=List[schemas.PromptTemplate])
def get_prompt_templates(db: Session = Depends(get_db)):
    return db.query(models.PromptTemplate).all()

@admin_router.post("/prompt-templates", response_model=schemas.PromptTemplate)
def create_prompt_template(template: schemas.PromptTemplateCreate, db: Session = Depends(get_db)):
    new_template = models.PromptTemplate(
        subject_id=template.subject_id,
        model_name=template.model_name,
        system_instruction=template.system_instruction
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template

# --- ADMIN: EXAM SUBJECTS ---
@admin_router.get("/exam/subjects", response_model=List[schemas.RegularSubject])
def get_exam_subjects(db: Session = Depends(get_db)):
    # You can filter by discipline/type later if you want to isolate them!
    return db.query(models.RegularSubject).all()

@admin_router.post("/exam/subjects", response_model=schemas.RegularSubject, status_code=201)
def create_exam_subject(payload: schemas.AdminSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(
        name=payload.name,
        subject_code=payload.subject_code.upper(),
        grade_id=payload.grade_id,
        discipline="Exam Stream", # Explicitly tagging it as an exam resource
        video_url=payload.video_url
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

# --- ADMIN: EXAM SPECIALTIES (Subject Areas / Units) ---
@admin_router.get("/exam/subject-areas", response_model=List[schemas.RegularSubjectArea])
def get_exam_subject_areas(db: Session = Depends(get_db)):
    return db.query(models.RegularSubjectArea).all()

@admin_router.post("/exam/subject-areas", response_model=schemas.RegularSubjectArea, status_code=201)
def create_exam_subject_area(area: schemas.RegularSubjectAreaCreate, db: Session = Depends(get_db)):
    new_area = models.RegularSubjectArea(
        name=area.name,
        sequence_order=area.sequence_order,
        subject_id=area.subject_id
    )
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area

# ==========================================
# --- ADMIN: EXAM STREAMS MANAGEMENT ---
# ==========================================

@admin_router.get("/exam/subjects", response_model=List[schemas.RegularSubject])
def get_exam_subjects(db: Session = Depends(get_db)):
    """Fetch only subjects belonging to competitive exam streams."""
    return db.query(models.RegularSubject).filter(models.RegularSubject.discipline == "Exam").all()

@admin_router.post("/exam/subjects", response_model=schemas.RegularSubject, status_code=201)
def create_exam_subject(payload: schemas.AdminSubjectCreate, db: Session = Depends(get_db)):
    """Create a subject explicitly tagged for competitive exam architecture."""
    # Safety boundary validation check
    grade = db.query(models.Grade).filter(models.Grade.id == payload.grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Target container Grade level identifier missing.")

    new_sub = models.RegularSubject(
        name=payload.name,
        subject_code=payload.subject_code.upper(),
        grade_id=payload.grade_id,
        discipline="Exam",  # Force set to separate from standard K-12 core classes
        video_url=payload.video_url
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

# --- ADMIN: EXAM SPECIALTIES (Subject Areas) ---

@admin_router.get("/exam/subject-areas", response_model=List[schemas.RegularSubjectArea])
def get_exam_subject_areas(db: Session = Depends(get_db)):
    """List out unit modules associated with exam paths."""
    return db.query(models.RegularSubjectArea).all()

@admin_router.post("/exam/subject-areas", response_model=schemas.RegularSubjectArea, status_code=201)
def create_exam_subject_area(area: schemas.RegularSubjectAreaCreate, db: Session = Depends(get_db)):
    """Bind a structural unit/specialty topic area to a subject node."""
    new_area = models.RegularSubjectArea(
        name=area.name,
        sequence_order=area.sequence_order,
        subject_id=area.subject_id
    )
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area