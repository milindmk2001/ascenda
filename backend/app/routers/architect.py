from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from uuid import UUID

router = APIRouter(prefix="/api/architect", tags=["Academic Architect"])

@router.post("/article")
def save_text_lesson(
    unit: str,
    subject: str,
    exam_type: str,
    topic: str,
    content: str,
    content_type: str = "article",
    db: Session = Depends(get_db)
):
    db_article = models.GeneratedContentPayload(
        unit=unit,
        subject=subject,
        exam_type=exam_type,
        topic=topic,
        content_type=content_type,
        content=content
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return {
        "id": str(db_article.id),
        "topic": db_article.topic,
        "status": "saved"
    }