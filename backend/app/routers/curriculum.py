from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List
from uuid import UUID

# 1. Standard Router for the User/Reader view layout
router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])

# 2. Admin Router for system data ingestion management
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["admin-curriculum"])


# =====================================================================
# --- COURSE SIDEBAR TREE ENDPOINT ---
# =====================================================================

@router.get("/subjects/{subject_id}/tree", response_model=List[schemas.CurriculumNode])
def get_curriculum_tree(subject_id: UUID, db: Session = Depends(get_db)):
    """Query only top-level nodes; children nest automatically via models relationship."""
    nodes = db.query(models.CurriculumTree).filter(
        models.CurriculumTree.subject_id == subject_id,
        models.CurriculumTree.parent_id == None
    ).all()
    
    return nodes if nodes else []


# =====================================================================
# --- ADMIN: K-12 CONTAINER GRADES ---
# =====================================================================

@admin_router.get("/grades", response_model=List[schemas.Grade])
def get_grades(db: Session = Depends(get_db)):
    """Fetch core tracking educational grades."""
    return db.query(models.Grade).all()

@admin_router.post("/grades", response_model=schemas.Grade, status_code=201)
def create_grade(payload: schemas.GradeCreate, db: Session = Depends(get_db)):
    """Ingest a standard tier grade tracking row node."""
    new_grade = models.Grade(
        level=str(payload.level),
        name=payload.name if payload.name else f"Grade {payload.level}",
        org_id=payload.org_id
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade


# =====================================================================
# --- ADMIN: K-12 REGULAR CORE SUBJECTS ---
# =====================================================================

@admin_router.get("/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    """Query base K-12 institutional streams mapping to 'regular_subjects' table."""
    return db.query(models.RegularSubject).all()

@admin_router.post("/regular/subjects", response_model=schemas.RegularSubject, status_code=201)
def create_regular_subject(payload: schemas.AdminSubjectCreate, db: Session = Depends(get_db)):
    """Instantiate a new school stream subject container row."""
    grade = db.query(models.Grade).filter(models.Grade.id == payload.grade_id).first()
    if not grade:
        raise HTTPException(status_code=404, detail="Target container Grade level identifier missing.")

    new_sub = models.RegularSubject(
        name=payload.name,
        subject_code=payload.subject_code.upper(),
        grade_id=payload.grade_id,
        discipline=payload.discipline,
        video_url=payload.video_url
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@admin_router.put("/regular/subjects/{subject_id}", response_model=schemas.RegularSubject)
def update_regular_subject(subject_id: UUID, payload: schemas.AdminSubjectCreate, db: Session = Depends(get_db)):
    """Mutate properties on a standard K-12 subject asset tracking tier."""
    db_sub = db.query(models.RegularSubject).filter(models.RegularSubject.id == subject_id).first()
    if not db_sub:
        raise HTTPException(status_code=404, detail="Regular subject entity row missing in database.")
        
    db_sub.name = payload.name
    db_sub.subject_code = payload.subject_code.upper()
    db_sub.grade_id = payload.grade_id
    db_sub.discipline = payload.discipline
    db_sub.video_url = payload.video_url
    
    db.commit()
    db.refresh(db_sub)
    return db_sub

@admin_router.delete("/regular/subjects/{subject_id}", status_code=204)
def delete_regular_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """Purge a K-12 subject element structure node completely."""
    db_sub = db.query(models.RegularSubject).filter(models.RegularSubject.id == subject_id).first()
    if not db_sub:
        raise HTTPException(status_code=404, detail="Target regular subject node not found.")
    db.delete(db_sub)
    db.commit()
    return None


# =====================================================================
# --- ADMIN: EXAMS ROOT STREAM ---
# =====================================================================

@admin_router.get("/exams", response_model=List[schemas.ExamResponse])
def get_all_exams(db: Session = Depends(get_db)):
    """Fetch top level competitive tracking indices (e.g., IITJEE, NEET)."""
    return db.query(models.Exam).all()

@admin_router.post("/exams", response_model=schemas.ExamResponse, status_code=201)
def create_exam_stream(payload: schemas.ExamCreate, db: Session = Depends(get_db)):
    """Create a foundational tracking node stream entry."""
    new_exam = models.Exam(
        name=payload.name,
        code=payload.code.upper()
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return new_exam


# =====================================================================
# --- ADMIN: COMPETITIVE EXAM SUBJECTS ---
# =====================================================================

@admin_router.get("/exam/subjects", response_model=List[schemas.ExamSubjectResponse])
def get_exam_subjects(db: Session = Depends(get_db)):
    """Query exclusively from the dedicated exam_subjects database table."""
    return db.query(models.ExamSubject).all()

@admin_router.post("/exam/subjects", response_model=schemas.ExamSubjectResponse, status_code=201)
def create_exam_subject(payload: schemas.ExamSubjectCreate, db: Session = Depends(get_db)):
    """Commit a record entry directly into the exam_subjects matrix table."""
    exam_exists = db.query(models.Exam).filter(models.Exam.id == payload.exam_id).first()
    if not exam_exists:
        raise HTTPException(status_code=404, detail="Target tracking parent Exam reference missing.")
        
    new_sub = models.ExamSubject(
        name=payload.name,
        subject_code=payload.subject_code.upper(),
        exam_id=payload.exam_id,
        discipline=payload.discipline if payload.discipline else "Competitive Exam",
        video_url=payload.video_url
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@admin_router.put("/exam/subjects/{subject_id}", response_model=schemas.ExamSubjectResponse)
def update_exam_subject(subject_id: UUID, payload: schemas.ExamSubjectCreate, db: Session = Depends(get_db)):
    """Update tracking properties on an active exam subject entry node row."""
    db_sub = db.query(models.ExamSubject).filter(models.ExamSubject.id == subject_id).first()
    if not db_sub:
        raise HTTPException(status_code=404, detail="Exam subject record entry not found in database.")
        
    db_sub.name = payload.name
    db_sub.subject_code = payload.subject_code.upper()
    db_sub.exam_id = payload.exam_id
    db_sub.discipline = payload.discipline if payload.discipline else "Competitive Exam"
    db_sub.video_url = payload.video_url
    
    db.commit()
    db.refresh(db_sub)
    return db_sub

@admin_router.delete("/exam/subjects/{subject_id}", status_code=204)
def delete_exam_subject(subject_id: UUID, db: Session = Depends(get_db)):
    """Evict a competitive stream component from the system ecosystem mappings."""
    db_sub = db.query(models.ExamSubject).filter(models.ExamSubject.id == subject_id).first()
    if not db_sub:
        raise HTTPException(status_code=404, detail="Exam subject record entry not found.")
    db.delete(db_sub)
    db.commit()
    return None