from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/admin/curriculum", tags=["curriculum"])

# --- GRADE ROUTES ---
@router.get("/grades", response_model=List[schemas.Grade])
def get_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

@router.post("/grades", response_model=schemas.Grade)
def create_grade(grade: schemas.GradeCreate, db: Session = Depends(get_db)):
    new_grade = models.Grade(
        level=grade.level,
        name=grade.name or grade.level,
        org_id=grade.org_id
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

# --- REGULAR CURRICULUM ROUTES ---
@router.get("/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()

@router.post("/regular/subjects", response_model=schemas.RegularSubject)
def create_regular_subject(sub: schemas.RegularSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(
        name=sub.name,
        subject_code=sub.subject_code,
        grade_id=sub.grade_id,
        discipline=sub.discipline
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.get("/regular/subject-areas", response_model=List[schemas.RegularSubjectArea])
def get_regular_subject_areas(db: Session = Depends(get_db)):
    return db.query(models.RegularSubjectArea).all()

@router.post("/regular/subject-areas", response_model=schemas.RegularSubjectArea)
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

# --- EXAM CURRICULUM ROUTES ---
@router.get("/exam/subjects", response_model=List[schemas.ExamSubject])
def get_exam_subjects(db: Session = Depends(get_db)):
    return db.query(models.ExamSubject).all()

@router.post("/exam/subjects", response_model=schemas.ExamSubject)
def create_exam_subject(sub: schemas.ExamSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.ExamSubject(
        name=sub.name,
        subject_code=sub.subject_code,
        organization_id=sub.organization_id,
        discipline=sub.discipline
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.get("/exam/subject-areas", response_model=List[schemas.ExamSubjectArea])
def get_exam_subject_areas(db: Session = Depends(get_db)):
    return db.query(models.ExamSubjectArea).all()