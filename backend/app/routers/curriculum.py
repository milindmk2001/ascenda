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
        name=grade.name or grade.level
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

@router.put("/grades/{grade_id}", response_model=schemas.Grade)
def update_grade(grade_id: UUID, grade_update: schemas.GradeCreate, db: Session = Depends(get_db)):
    db_grade = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
    if not db_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    db_grade.level = grade_update.level
    db_grade.name = grade_update.name or grade_update.level
    db.commit()
    db.refresh(db_grade)
    return db_grade

@router.delete("/grades/{grade_id}")
def delete_grade(grade_id: UUID, db: Session = Depends(get_db)):
    db_grade = db.query(models.Grade).filter(models.Grade.id == grade_id).first()
    if not db_grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    db.delete(db_grade)
    db.commit()
    return {"message": "Grade deleted"}

@router.post("/subjects/regular", response_model=schemas.RegularSubject)
def create_regular_subject(sub: schemas.RegularSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(**sub.model_dump())
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

# For the Exam route, use the ExamSubject schema
@router.post("/subjects/exam", response_model=schemas.ExamSubject)
def create_exam_subject(sub: schemas.ExamSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.ExamSubject(**sub.model_dump())
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub