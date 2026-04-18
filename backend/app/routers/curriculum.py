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