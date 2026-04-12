from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from typing import List

router = APIRouter(prefix="/api/admin/curriculum", tags=["curriculum"])

@router.post("/grades", response_model=schemas.Grade)
def create_grade(grade: schemas.GradeCreate, db: Session = Depends(get_db)):
    new_grade = models.Grade(level=grade.level)
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

@router.get("/grades", response_model=List[schemas.Grade])
def get_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

@router.post("/subjects/regular", response_model=schemas.Subject)
def create_regular_subject(sub: schemas.RegularSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(**sub.model_dump())
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

@router.post("/subjects/exam", response_model=schemas.Subject)
def create_exam_subject(sub: schemas.ExamSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.ExamSubject(**sub.model_dump())
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub