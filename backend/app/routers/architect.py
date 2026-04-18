from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from uuid import UUID

router = APIRouter(prefix="/api/architect", tags=["Academic Architect"])

@router.post("/article", response_model=schemas.Article)
def save_text_lesson(article: schemas.ArticleCreate, db: Session = Depends(get_db)):
    db_article = models.LessonArticle(
        title=article.title,
        content=article.content_markdown,
        subject_id=article.subject_id
    )
    db.add(db_article)
    db.commit()
    db.refresh(db_article)
    return db_article