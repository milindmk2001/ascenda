from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List
from uuid import UUID

router = APIRouter(prefix="/api/admin/curriculum", tags=["curriculum"])

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

@router.get("/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()

@router.post("/regular/subjects", response_model=schemas.RegularSubject)
def create_regular_subject(sub: schemas.RegularSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(
        name=sub.name,
        subject_code=sub.subject_code,
        grade_id=sub.grade_id,
        discipline=sub.discipline,
        video_url=sub.video_url # Comma fixed here
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.get("/regular/subject-areas", response_model=List[schemas.RegularSubjectArea])
def get_regular_subject_areas(db: Session = Depends(get_db)):
    return db.query(models.RegularSubjectArea).all()