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
    """Fetch all grade levels (e.g., 11, 12).
    This endpoint is used by UserLearningHub to populate the Grade dropdown.
    """
    return db.query(models.Grade).all()

@router.post("/grades", response_model=schemas.Grade)
def create_grade(grade: schemas.GradeCreate, db: Session = Depends(get_db)):
    """Create a new grade level linked to an organization."""
    new_grade = models.Grade(
        level=grade.level,
        name=grade.name or grade.level,
        org_id=grade.org_id  # Ensures grade is linked to a Board for frontend filtering
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
    db_grade.org_id = grade_update.org_id
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


# --- REGULAR CURRICULUM ROUTES (K-12) ---

@router.get("/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    """Fetches all regular subjects. 
    Frontend uses this to display Physics, Chemistry, etc., after filtering by grade_id.
    """
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
    """Fetches all units/chapters for the Learning Hub."""
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


# --- EXAM CURRICULUM ROUTES (Competitive) ---

@router.get("/exam/subjects", response_model=List[schemas.ExamSubject])
def get_exam_subjects(db: Session = Depends(get_db)):
    """Fetch all competitive subjects linked to Organizations."""
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
    """Fetch all exam units for the Learning Hub."""
    return db.query(models.ExamSubjectArea).all()

@router.post("/exam/subject-areas", response_model=schemas.ExamSubjectArea)
def create_exam_subject_area(area: schemas.ExamSubjectAreaCreate, db: Session = Depends(get_db)):
    new_area = models.ExamSubjectArea(
        name=area.name,
        area_code=area.area_code,
        exam_subject_id=area.exam_subject_id
    )
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area