from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List
from uuid import UUID

# 1. Standard Router for the User/Reader view
router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])

# 2. Admin Router for management (The one main.py is looking for)
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
@admin_router.get("/grades", response_model=List[schemas.Grade])
def get_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

@admin_router.post("/grades", response_model=schemas.Grade)
def create_grade(grade: schemas.GradeCreate, db: Session = Depends(get_db)):
    new_grade = models.Grade(
        level=grade.level,
        name=grade.name or f"Grade {grade.level}",
        org_id=grade.org_id
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

# --- ADMIN: SUBJECTS ---
@admin_router.get("/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()

@admin_router.post("/regular/subjects", response_model=schemas.RegularSubject)
def create_regular_subject(sub: schemas.RegularSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(
        name=sub.name,
        subject_code=sub.subject_code,
        grade_id=sub.grade_id,
        discipline=sub.discipline,
        video_url=sub.video_url
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
        name=area.name,
        area_code=area.area_code,
        subject_id=area.subject_id
    )
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area

# --- NEW: EXAMS TABLE ROUTE ---
@admin_router.post("/exams", response_model=schemas.ExamResponse, status_code=201)
def create_exam_node(payload: schemas.ExamCreate, db: Session = Depends(get_db)):
    # Check if the exam code identifier is unique
    existing = db.query(models.Exam).filter(models.Exam.code == payload.code.upper()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An exam with this system code identifier already exists.")
        
    db_exam = models.Exam(name=payload.name, code=payload.code.upper())
    db.add(db_exam)
    db.commit()
    db.refresh(db_exam)
    return db_exam

# --- FIXED: GRADES MANAGEMENT ROUTE ---
@admin_router.post("/curriculum/grades", response_model=schemas.Grade, status_code=201)
def create_grade_node(payload: schemas.AdminGradeCreate, db: Session = Depends(get_db)):
    # Verify the target organization structure element is accurate
    org = db.query(models.Organization).filter(models.Organization.id == payload.org_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Target tracking organization border entry not found.")
        
    new_grade = models.Grade(
        level=str(payload.level), # Explicit string cast matching models.py string tracking format
        name=payload.name if payload.name else f"Grade {payload.level}",
        org_id=payload.org_id
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

# --- FIXED: SUBJECTS LINK ROUTE ---
@admin_router.post("/curriculum/subjects", response_model=schemas.RegularSubject, status_code=201)
def create_subject_node(payload: schemas.AdminSubjectCreate, db: Session = Depends(get_db)):
    # Enforce parent structural tree boundary validation checks
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

# Retain original matching fetch arrays down here for the architecture layout trees
@admin_router.get("/curriculum/grades", response_model=List[schemas.Grade])
def get_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

@admin_router.get("/curriculum/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()