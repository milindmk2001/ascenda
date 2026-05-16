from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/api/curriculum", tags=["curriculum"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["admin-curriculum"])

# --- COURSE SIDEBAR TREE ENDPOINT ---
@router.get("/subjects/{subject_id}/tree", response_model=List[schemas.CurriculumNode])
def get_curriculum_tree(subject_id: UUID, db: Session = Depends(get_db)):
    nodes = db.query(models.CurriculumTree).filter(
        models.CurriculumTree.subject_id == subject_id,
        models.CurriculumTree.parent_id == None
    ).all()
    return nodes if nodes else []

# --- ADMIN: K-12 CONTAINER GRADES ---
@admin_router.get("/grades", response_model=List[schemas.Grade])
def get_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

@admin_router.post("/grades", response_model=schemas.Grade, status_code=201)
def create_grade(payload: schemas.GradeCreate, db: Session = Depends(get_db)):
    new_grade = models.Grade(
        level=str(payload.level),
        name=payload.name if payload.name else f"Grade {payload.level}",
        org_id=payload.org_id
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

# --- ADMIN: REGULAR K-12 SUBJECTS ---
@admin_router.get("/regular/subjects", response_model=List[schemas.RegularSubject])
def get_regular_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()

@admin_router.post("/regular/subjects", response_model=schemas.RegularSubject, status_code=201)
def create_regular_subject(payload: schemas.AdminSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(
        name=payload.name,
        subject_code=payload.subject_code,
        grade_id=payload.grade_id,
        discipline=payload.discipline if payload.discipline else "General",
        video_url=payload.video_url
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

# --- ADMIN: COMPETITIVE EXAMS ---
@admin_router.get("/exams", response_model=List[schemas.ExamResponse])
def get_exams(db: Session = Depends(get_db)):
    return db.query(models.Exam).all()

@admin_router.post("/exams", response_model=schemas.ExamResponse, status_code=201)
def create_exam(exam: schemas.ExamCreate, db: Session = Depends(get_db)):
    new_exam = models.Exam(name=exam.name, code=exam.code)
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return new_exam

# --- ADMIN: COMPETITIVE EXAMS SUBJECTS ---
@admin_router.get("/exam/subjects", response_model=List[schemas.ExamSubjectResponse])
def get_exam_subjects(db: Session = Depends(get_db)):
    return db.query(models.ExamSubject).all()

@admin_router.post("/exam/subjects", response_model=schemas.ExamSubjectResponse, status_code=201)
def create_exam_subject(payload: schemas.ExamSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.ExamSubject(
        exam_id=payload.exam_id,
        name=payload.name,
        subject_code=payload.subject_code,
        discipline=payload.discipline if payload.discipline else "Competitive Exam",
        video_url=payload.video_url
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub

# --- ADMIN: K-12 SUBJECT STRUCTURAL AREAS ---
@admin_router.get("/regular/subject-areas", response_model=List[schemas.RegularSubjectArea])
def get_regular_subject_areas(db: Session = Depends(get_db)):
    return db.query(models.RegularSubjectArea).all()

@admin_router.post("/regular/subject-areas", response_model=schemas.RegularSubjectArea)
def create_regular_subject_area(area: schemas.RegularSubjectAreaCreate, db: Session = Depends(get_db)):
    new_area = models.RegularSubjectArea(
        title=area.title,
        sequence_order=area.sequence_order,
        subject_id=area.subject_id
    )
    db.add(new_area)
    db.commit()
    db.refresh(new_area)
    return new_area

# --- ADMIN: K-12 CHAPTER TRACKS ---
@admin_router.get("/regular/chapters", response_model=List[schemas.RegularChapter])
def get_regular_chapters(db: Session = Depends(get_db)):
    return db.query(models.RegularChapter).all()

@admin_router.post("/regular/chapters", response_model=schemas.RegularChapter)
def create_regular_chapter(chap: schemas.RegularChapterCreate, db: Session = Depends(get_db)):
    new_chap = models.RegularChapter(
        title=chap.title,
        sequence_order=chap.sequence_order,
        subject_area_id=chap.subject_area_id
    )
    db.add(new_chap)
    db.commit()
    db.refresh(new_chap)
    return new_chap

# --- ADMIN: GENERATIVE PROMPT AGENTS TEMPLATES ---
@admin_router.get("/prompt-templates", response_model=List[schemas.PromptTemplate])
def get_prompt_templates(db: Session = Depends(get_db)):
    return db.query(models.PromptTemplate).all()

@admin_router.post("/prompt-templates", response_model=schemas.PromptTemplate)
def create_prompt_template(template: schemas.PromptTemplateCreate, db: Session = Depends(get_db)):
    new_template = models.PromptTemplate(
        name=template.name,
        system_prompt=template.system_prompt,
        user_template=template.user_template,
        description=template.description
    )
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    return new_template