import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models
from app.database import get_db

router = APIRouter(prefix="/api/curriculum", tags=["Curriculum Public Framework"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Curriculum Ingestion Console"])


# ==========================================
# 1. PYDANTIC DATA TRANSFER SCHEMAS
# ==========================================

class GradeCreate(BaseModel):
    name: str
    level: Optional[str] = None
    org_id: Optional[UUID4] = None

class GradeResponse(BaseModel):
    id: UUID4
    name: Optional[str]
    level: Optional[str]
    org_id: Optional[UUID4] = None

    class Config:
        from_attributes = True

class RegularSubjectCreate(BaseModel):
    name: str
    subject_code: str
    discipline: str = "Science"
    grade_id: UUID4
    video_url: Optional[str] = ""

class RegularSubjectResponse(BaseModel):
    id: UUID4
    name: str
    subject_code: str
    discipline: str
    grade_id: Optional[UUID4] = None
    video_url: Optional[str] = ""

    class Config:
        from_attributes = True

class ExamCreate(BaseModel):
    name: str
    exam_code: str

class ExamResponse(BaseModel):
    id: UUID4
    name: str
    exam_code: str

    class Config:
        from_attributes = True

class ExamSubjectCreate(BaseModel):
    exam_id: UUID4
    name: str
    subject_code: str
    discipline: str

class ExamSubjectResponse(BaseModel):
    id: UUID4
    exam_id: UUID4
    name: str
    subject_code: str
    discipline: str

    class Config:
        from_attributes = True

class LeafNode(BaseModel):
    id: UUID4
    title: str
    content_type: str
    content_id: Optional[UUID4] = None
    is_leaf: bool = True

class TopicNode(BaseModel):
    id: UUID4
    title: str
    content_type: str = "topic"
    leaves: List[LeafNode] = []

class UnitNode(BaseModel):
    id: UUID4
    title: str
    unit_number: int
    content_type: str = "unit"
    topics: List[TopicNode] = []

class CurriculumTreeResponse(BaseModel):
    exam_type: str
    subject: str
    units: List[UnitNode]

class ContentPayloadResponse(BaseModel):
    content: str
    content_type: str
    topic: str
    unit: str


# ==========================================
# 2. CORE HUB LOOKUP ENGINE (HOMEPAGE RESOLVER)
# ==========================================

@router.get("/resolve-hub")
def resolve_hub_fallback(
    track_code: Optional[str] = None, 
    grade_name: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Unified Dashboard Subject Card Resolution Framework.
    Queries structural courses out of public.courses cleanly.
    """
    if not track_code:
        return []

    clean_track = track_code.strip().upper().replace("-", "").replace("_", "")

    # ──────────────────────────────────────────────────────────────
    # CASE A: COMPETITIVE EXTRACTION TRACK (IIT-JEE / NEET)
    # ──────────────────────────────────────────────────────────────
    if clean_track in ["IITJEE", "NEET"]:
        prefix_pattern = f"{clean_track}_%"
        
        sql_query = text("""
            SELECT 
                c.id               AS course_id,
                c.title            AS course_title,
                c.description      AS description,
                es.id              AS exam_subject_id,
                es.name            AS subject_name,
                es.subject_code    AS subject_code
            FROM public.courses c
            JOIN public.exam_subjects es ON es.id = c.exam_subject_id
            WHERE es.subject_code LIKE :pattern
            ORDER BY es.name ASC;
        """)
        try:
            rows = db.execute(sql_query, {"pattern": prefix_pattern}).fetchall()
            return [
                {
                    "id": str(row.course_id),
                    "name": row.subject_name,
                    "course_title": row.course_title,
                    "subject_code": row.subject_code.lower(), 
                    "description": row.description or ""
                }
                for row in rows
            ]
        except Exception as err:
            print(f"[Hub Error] Competitive lookup failed: {err}")
            return []

    # ──────────────────────────────────────────────────────────────
    # CASE B: TRADITIONAL ACADEMIC K-12 BOARDS (CBSE / ICSE)
    # ──────────────────────────────────────────────────────────────
    if grade_name:
        clean_grade = grade_name.strip()
        match_pattern = f"%{clean_track}%Class {clean_grade}%"

        sql_query = text("""
            SELECT 
                c.id           AS course_id,
                c.title        AS course_title,
                c.description  AS description,
                s.id           AS regular_subject_id,
                s.name         AS subject_name,
                s.subject_code AS subject_code
            FROM public.courses c
            JOIN public.subjects s ON s.id = c.regular_subject_id
            JOIN public.grades g ON s.grade_id = g.id
            WHERE LOWER(c.title) LIKE LOWER(:pattern) 
               OR (LOWER(g.name) = LOWER(:grade_name) AND LOWER(c.title) LIKE LOWER(:track_clause))
            ORDER BY s.name ASC;
        """)
        try:
            rows = db.execute(sql_query, {
                "pattern": match_pattern,
                "grade_name": clean_grade,
                "track_clause": f"%{clean_track}%"
            }).fetchall()
            
            return [
                {
                    "id": str(row.course_id),
                    "name": row.subject_name,
                    "course_title": row.course_title,
                    "subject_code": row.subject_code.lower(),
                    "description": row.description or ""
                }
                for row in rows
            ]
        except Exception as err:
            print(f"[Hub Error] Board course lookup failure: {err}")
            return []

    return []


# ==========================================
# 3. CONTENT CANVAS ROUTERS
# ==========================================

@router.get("/content/{content_id}", response_model=ContentPayloadResponse)
def get_content_payload(content_id: UUID4 = Path(..., description="Target asset code"), db: Session = Depends(get_db)):
    query = text("""
        SELECT content, content_type, topic, unit
        FROM public.generated_content
        WHERE id = :content_id
        LIMIT 1;
    """)
    result = db.execute(query, {"content_id": str(content_id)}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Asset metadata not found.")
    return {
        "content": result.content,
        "content_type": result.content_type,
        "topic": result.topic,
        "unit": result.unit
    }

@router.get("/{exam_type}/{subject_code}", response_model=CurriculumTreeResponse)
def get_curriculum_tree(
    exam_type: str = Path(..., description="e.g., CBSE, IIT-JEE or NEET"),
    subject_code: str = Path(..., description="e.g., physics, chemistry, maths"),
    db: Session = Depends(get_db)
):
    """
    Curriculum Tree Fetcher Engine.
    Uses a Hierarchical CTE lookup query structure to extract units and branches 
    belonging exclusively to the targeted subject.
    """
    clean_exam = exam_type.strip().lower().replace("-", "").replace("_", "")
    clean_subject = subject_code.strip().lower()

    # Exact matching values for specialized entries
    exact_combined = f"{clean_exam}_{clean_subject}"
    pattern_combined = f"%{clean_exam}%{clean_subject}%"

    # Recursive hierarchical CTE ensures that if nodes are just grouped under a generic 'iitjee' exam_type,
    # we only fetch elements whose branch tree starts with a Unit or sub-entry mentioning the specific subject.
    query = text("""
        WITH RECURSIVE filtered_tree AS (
            -- Step 1: Secure top-level root unit containers belonging to this exam track
            SELECT id, parent_id, title, level, content_type, unit_number, is_leaf, content_id, display_order, exam_type
            FROM public.curriculum_tree
            WHERE (LOWER(exam_type) = :exact_combined OR LOWER(exam_type) LIKE :pattern_combined)
               OR (
                    LOWER(exam_type) = :clean_exam 
                    AND parent_id IS NULL 
                    AND (
                        LOWER(title) LIKE LOWER('%' || :clean_subject || '%')
                        OR (:clean_subject = 'physics' AND LOWER(title) NOT LIKE '%maths%' AND LOWER(title) NOT LIKE '%chemistry%' AND LOWER(title) NOT LIKE '%biology%')
                        OR (:clean_subject = 'maths' AND (LOWER(title) LIKE '%math%' OR LOWER(title) LIKE '%algebra%' OR LOWER(title) LIKE '%calculus%' OR LOWER(title) LIKE '%geometry%'))
                    )
               )
            
            UNION ALL
            
            -- Step 2: Recursively cascade down child nodes (topics, leaves) linked to those matched units
            SELECT child.id, child.parent_id, child.title, child.level, child.content_type, child.unit_number, child.is_leaf, child.content_id, child.display_order, child.exam_type
            FROM public.curriculum_tree child
            JOIN filtered_tree parent ON child.parent_id = parent.id
        )
        SELECT DISTINCT id, parent_id, title, level, content_type, unit_number, is_leaf, content_id, display_order
        FROM filtered_tree
        ORDER BY unit_number ASC, level ASC, display_order ASC;
    """)
    
    try:
        rows = db.execute(query, {
            "clean_exam": clean_exam,
            "exact_combined": exact_combined,
            "pattern_combined": pattern_combined,
            "clean_subject": clean_subject
        }).fetchall()
    except Exception as err:
        print(f"[Tree Query Error] Recursive execution failed: {err}")
        rows = []

    if not rows:
        return {"exam_type": exam_type.upper(), "subject": subject_code.capitalize(), "units": []}

    units_dict: Dict[str, Dict[str, Any]] = {}
    topics_dict: Dict[str, Dict[str, Any]] = {}
    all_leaves: List[Dict[str, Any]] = []

    for row in rows:
        row_id = str(row.id)
        if row.level == 1 or row.content_type == "unit":
            units_dict[row_id] = {
                "id": row.id,
                "title": row.title,
                "unit_number": row.unit_number if row.unit_number is not None else 1,
                "content_type": "unit",
                "topics": []
            }
        elif row.level == 2 or row.content_type == "topic":
            topics_dict[row_id] = {
                "id": row.id,
                "title": row.title,
                "content_type": "topic",
                "parent_id": str(row.parent_id) if row.parent_id else None,
                "leaves": []
            }
        else:
            all_leaves.append({
                "id": row.id,
                "parent_id": str(row.parent_id) if row.parent_id else None,
                "title": row.title,
                "content_type": row.content_type if row.content_type else "text",
                "content_id": row.content_id,
                "is_leaf": True
            })

    for leaf in all_leaves:
        p_id = leaf["parent_id"]
        if p_id and p_id in topics_dict:
            topics_dict[p_id]["leaves"].append({
                "id": leaf["id"],
                "title": leaf["title"],
                "content_type": leaf["content_type"],
                "content_id": leaf["content_id"],
                "is_leaf": True
            })

    for t_id, topic_data in topics_dict.items():
        p_id = topic_data.pop("parent_id", None)
        if p_id and p_id in units_dict:
            units_dict[p_id]["topics"].append(topic_data)

    return {
        "exam_type": exam_type.upper(),
        "subject": subject_code.capitalize(),
        "units": sorted(list(units_dict.values()), key=lambda x: x["unit_number"])
    }


# ==========================================
# 4. ADMIN PIPELINE CONTROL ROUTERS
# ==========================================

@admin_router.get("/grades", response_model=List[GradeResponse])
def get_admin_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

@admin_router.post("/grades", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
def create_admin_grade(payload: GradeCreate, db: Session = Depends(get_db)):
    try:
        new_grade = models.Grade(
            name=payload.name.strip(),
            level=payload.level.strip() if payload.level else None,
            org_id=payload.org_id
        )
        db.add(new_grade)
        db.commit()
        db.refresh(new_grade)
        return new_grade
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(err))

@admin_router.get("/subjects", response_model=List[RegularSubjectResponse])
def get_admin_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()

@admin_router.post("/subjects", response_model=RegularSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_admin_subject(payload: RegularSubjectCreate, db: Session = Depends(get_db)):
    try:
        new_sub = models.RegularSubject(
            name=payload.name.strip(),
            subject_code=payload.subject_code.upper().strip(),
            discipline=payload.discipline.strip(),
            grade_id=payload.grade_id,
            video_url=payload.video_url
        )
        db.add(new_sub)
        db.commit()
        db.refresh(new_sub)
        return new_sub
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(err))

@admin_router.get("/exams", response_model=List[ExamResponse])
def get_admin_exams(db: Session = Depends(get_db)):
    return db.query(models.Exam).all()

@admin_router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_admin_exam(payload: ExamCreate, db: Session = Depends(get_db)):
    try:
        new_exam = models.Exam(
            name=payload.name.strip(),
            exam_code=payload.exam_code.upper().strip()
        )
        db.add(new_exam)
        db.commit()
        db.refresh(new_exam)
        return new_exam
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(err))

@admin_router.get("/exam/subjects", response_model=List[ExamSubjectResponse])
def get_admin_exam_subjects(db: Session = Depends(get_db)):
    return db.query(models.ExamSubject).all()

@admin_router.post("/exam/subjects", response_model=ExamSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_exam_subject_node(payload: ExamSubjectCreate, db: Session = Depends(get_db)):
    parent_exam = db.query(models.Exam).filter(models.Exam.id == payload.exam_id).first()
    if not parent_exam:
        raise HTTPException(status_code=404, detail="Target exam tracker reference link missing.")
    try:
        new_subject = models.ExamSubject(
            exam_id=payload.exam_id,
            name=payload.name.strip(),
            subject_code=payload.subject_code.upper().strip(),
            discipline=payload.discipline.strip()
        )
        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)
        return new_subject
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(err))