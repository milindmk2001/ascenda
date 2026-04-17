from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/studio", tags=["studio"])

@router.post("/lesson", response_model=schemas.ModularLesson)
def sync_lesson_to_db(lesson: schemas.ModularLessonCreate, db: Session = Depends(get_db)):
    db_lesson = models.ModularLesson(
        title=lesson.title,
        physics_params=lesson.variables,
        latex_formula=lesson.formula,
        video_asset_id=lesson.videoAssetId
    )
    db.add(db_lesson)
    db.commit()
    db.refresh(db_lesson)
    return db_lesson

# Remotion uses this to fetch data during the render process
@router.get("/lesson/{lesson_id}", response_model=schemas.ModularLesson)
def get_render_data(lesson_id: UUID, db: Session = Depends(get_db)):
    lesson = db.query(models.ModularLesson).filter(models.ModularLesson.id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson data not found")
    return lesson