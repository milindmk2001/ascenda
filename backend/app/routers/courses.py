from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from .. import models, schemas, database

router = APIRouter(
    prefix="/api/admin/courses",
    tags=["Admin: Courses"]
)

@router.get("/", response_model=List[schemas.RegularSubject])
def list_courses(db: Session = Depends(database.get_db)):
    # Changed from models.Course to models.RegularSubject to match your models.py
    return db.query(models.RegularSubject).all()

@router.post("/", status_code=201, response_model=schemas.RegularSubject)
def create_course(course: schemas.RegularSubjectCreate, db: Session = Depends(database.get_db)):
    # Maps the incoming data to the RegularSubject model
    db_course = models.RegularSubject(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.put("/{course_id}", response_model=schemas.RegularSubject)
def update_course(course_id: UUID, course_data: schemas.RegularSubjectCreate, db: Session = Depends(database.get_db)):
    db_course = db.query(models.RegularSubject).filter(models.RegularSubject.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    for key, value in course_data.model_dump().items():
        setattr(db_course, key, value)
    
    db.commit()
    db.refresh(db_course)
    return db_course

@router.delete("/{course_id}", status_code=204)
def delete_course(course_id: UUID, db: Session = Depends(database.get_db)):
    db_course = db.query(models.RegularSubject).filter(models.RegularSubject.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    db.delete(db_course)
    db.commit()
    return None