from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from .. import models, schemas, database

router = APIRouter(
    prefix="/api/admin/courses",
    tags=["Admin: Courses"]
)

@router.get("/", response_model=List[schemas.Course])
def list_courses(db: Session = Depends(database.get_db)):
    return db.query(models.Course).all()

@router.post("/", status_code=201, response_model=schemas.Course)
def create_course(course: schemas.CourseCreate, db: Session = Depends(database.get_db)):
    db_course = models.Course(**course.model_dump())
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.put("/{course_id}", response_model=schemas.Course)
def update_course(course_id: UUID, course_data: schemas.CourseCreate, db: Session = Depends(database.get_db)):
    db_course = db.query(models.Course).filter(models.Course.id == course_id).first()
    if not db_course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    for key, value in course_data.model_dump().items():
        setattr(db_course, key, value)
    
    db.commit()
    db.refresh(db_course)
    return db_course