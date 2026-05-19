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
# 2. PUBLIC CORE ROUTE ENDPOINTS
# ==========================================

@router.get("/resolve-hub")
def resolve_hub_fallback(track_code: Optional[str] = None, grade_name: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Permissive tracking locator engine. Resolves and lists all configured courses 
    and tracks to build selection components on the frontend hub layout viewports.
    """
    if track_code:
        clean_track = track_code.strip().lower().replace("-", "").replace("_", "")
        track_pattern = f"%{clean_track}%"
        
        query = text("""
            SELECT id, name, code, description 
            FROM public.courses
            WHERE LOWER(name) LIKE :pattern 
               OR LOWER(code) LIKE :pattern;
        """)
        try:
            result = db.execute(query, {"pattern": track_pattern}).fetchall()
            if result:
                return [
                    {"id": str(row.id), "name": row.name, "code": row.code, "description": row.description or ""}
                    for row in result
                ]
        except Exception:
            pass

    # Fallback/Default: Fetch all courses from the database
    fallback_all = text("SELECT id, name, code, description FROM public.courses ORDER BY code ASC LIMIT 50;")
    try:
        all_rows = db.execute(fallback_all).fetchall()
        if all_rows:
            return [
                {"id": str(row.id), "name": row.name, "code": row.code, "description": row.description or ""}
                for row in all_rows
            ]
    except Exception:
        pass

    return [
        {"id": "00000000-0000-0000-0000-000000000000", "name": "CBSE", "code": "CBSE", "description": "Standard K-12 Foundation"},
        {"id": "11111111-1111-1111-1111-111111111111", "name": "IIT-JEE", "code": "IITJEE", "description": "Engineering Preparation Track"},
        {"id": "22222222-2222-2222-2222-222222222222", "name": "NEET", "code": "NEET", "description": "Medical Entrance Track"}
    ]

@router.get("/subjects", response_model=List[RegularSubjectResponse])
def get_filtered_subjects(
    track_code: Optional[str] = Query(None, description="e.g., CBSE, IITJEE"),
    grade_name: Optional[str] = Query(None, description="e.g., 11, 12"),
    db: Session = Depends(get_db)
):
    """
    Dynamically maps subjects filtered directly by track context or grade identifiers.
    Falls back to a flat text pattern lookup if full relational links are missing.
    """
    # Clean up strings
    clean_track = track_code.strip().lower() if track_code else ""
    clean_grade = grade_name.strip().lower() if grade_name else ""

    # Check relation matrix via raw text join filtering for speed and safety
    sql_query = text("""
        SELECT s.id, s.name, s.subject_code, s.discipline, s.grade_id, s.video_url
        FROM public.subjects s
        JOIN public.grades g ON s.grade_id = g.id
        LEFT JOIN public.organizations o ON g.org_id = o.id
        WHERE (:grade_name = '' OR LOWER(g.name) = :grade_name)
          AND (:track_code = '' OR LOWER(o.name) LIKE :track_pattern OR LOWER(s.discipline) LIKE :track_pattern);
    """)
    
    try:
        params = {
            "grade_name": clean_grade,
            "track_code": clean_track,
            "track_pattern": f"%{clean_track}%"
        }
        rows = db.execute(sql_query, params).fetchall()
        if rows:
            return [
                {
                    "id": row.id,
                    "name": row.name,
                    "subject_code": row.subject_code,
                    "discipline": row.discipline,
                    "grade_id": row.grade_id,
                    "video_url": row.video_url or ""
                } for row in rows
            ]
    except Exception:
        pass

    # Safety Fallback: Return all subjects if no filters match perfectly
    try:
        all_subs = db.execute(text("SELECT id, name, subject_code, discipline, grade_id, video_url FROM public.subjects LIMIT 20;")).fetchall()
        return [
            {
                "id": r.id,
                "name": r.name,
                "subject_code": r.subject_code,
                "discipline": r.discipline,
                "grade_id": r.grade_id,
                "video_url": r.video_url or ""
            } for r in all_subs
        ]
    except Exception:
        return []

@router.get("/content/{content_id}", response_model=ContentPayloadResponse)
def get_content_payload(content_id: UUID4 = Path(..., description="Target payload identifier"), db: Session = Depends(get_db)):
    query = text("""
        SELECT content, content_type, topic, unit
        FROM public.generated_content
        WHERE id = :content_id
        LIMIT 1;
    """)
    result = db.execute(query, {"content_id": str(content_id)}).fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Asset could not be located.")
    return {
        "content": result.content,
        "content_type": result.content_type,
        "topic": result.topic,
        "unit": result.unit
    }

@router.get("/{exam_type}/{subject_code}", response_model=CurriculumTreeResponse)
def get_curriculum_tree(
    exam_type: str = Path(..., description="e.g., CBSE or IIT-JEE"),
    subject_code: str = Path(..., description="e.g., physics"),
    db: Session = Depends(get_db)
):
    clean_exam = exam_type.strip().lower().replace("-", "").replace("_", "")
    clean_subject = subject_code.strip().lower()

    query = text("""
        SELECT id, parent_id, title, level, content_type,
               unit_number, is_leaf, content_id, display_order
        FROM public.curriculum_tree
        WHERE LOWER(REPLACE(REPLACE(exam_type, '_', ''), '-', '')) = :clean_exam
           OR LOWER(exam_type) LIKE :exam_pattern
        ORDER BY unit_number ASC, level ASC, display_order ASC;
    """)
    
    try:
        rows = db.execute(query, {
            "clean_exam": clean_exam,
            "exam_pattern": f"%{clean_exam}%"
        }).fetchall()
    except Exception:
        rows = []

    if not rows:
        fallback_query = text("""
            SELECT id, NULL::uuid as parent_id, name as title, 1 as level, 
                   'unit' as content_type, 1 as unit_number, false as is_leaf, 
                   NULL::uuid as content_id, 0 as display_order
            FROM public.courses
            WHERE LOWER(code) LIKE :subject_pattern 
               OR LOWER(name) LIKE :subject_pattern
            UNION ALL
            SELECT s.id, s.exam_id as parent_id, s.name as title, 1 as level,
                   'unit' as content_type, 1 as unit_number, false as is_leaf,
                   NULL::uuid as content_id, 0 as display_order
            FROM public.exam_subjects s
            JOIN public.exams e ON s.exam_id = e.id
            WHERE (LOWER(REPLACE(REPLACE(e.exam_code, '_', ''), '-', '')) = :clean_exam 
               OR LOWER(e.name) LIKE :exam_pattern)
               AND (LOWER(s.subject_code) LIKE :subject_pattern OR LOWER(s.name) LIKE :subject_pattern);
        """)
        try:
            rows = db.execute(fallback_query, {
                "clean_exam": clean_exam,
                "exam_pattern": f"%{clean_exam}%",
                "subject_pattern": f"%{clean_subject}%"
            }).fetchall()
        except Exception:
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
# 3. ADMIN MANAGEMENT INGESTION ENDPOINTS
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
        raise HTTPException(status_code=500, detail=f"Database update failure: {str(err)}")

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
        raise HTTPException(status_code=500, detail=f"Database update failure: {str(err)}")

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
        raise HTTPException(status_code=500, detail=f"Database update rollback: {str(err)}")

@admin_router.get("/exam/subjects", response_model=List[ExamSubjectResponse])
def get_admin_exam_subjects(db: Session = Depends(get_db)):
    return db.query(models.ExamSubject).all()

@admin_router.post("/exam/subjects", response_model=ExamSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_exam_subject_node(payload: ExamSubjectCreate, db: Session = Depends(get_db)):
    parent_exam = db.query(models.Exam).filter(models.Exam.id == payload.exam_id).first()
    if not parent_exam:
        raise HTTPException(status_code=404, detail="Target tracking track profile code link missing.")
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
        raise HTTPException(status_code=500, detail=f"Database rollback: {str(err)}")