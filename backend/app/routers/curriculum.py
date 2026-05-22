import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models
from app.database import get_db

# ── ROUTER INITIALIZATION DEFINITIONS ─────────────────────────────────
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
    video_url: Optional[str]

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
    discipline: str = "Science"

class ExamSubjectResponse(BaseModel):
    id: UUID4
    exam_id: Optional[UUID4]
    name: str
    subject_code: str
    discipline: str

    class Config:
        from_attributes = True


# ==========================================
# 2. PUBLIC API ENDPOINTS
# ==========================================

@router.get("/resolve-hub")
def resolve_course_hub(
    track_code: str = Query(..., alias="track_code"), 
    db: Session = Depends(get_db)
):
    """
    Resolves the core entry structural wrapper for a given track (e.g., IITJEE or NEET).
    Uses robust raw SQL queries to bypass model mismatch 500 crashes and gracefully
    handles table structure variants.
    """
    clean_code = track_code.upper().strip()
    
    # Try reading from standard public.exams table with safe fallback checking variations
    exam_sql = """
        SELECT id, name, 
               COALESCE(exam_code, exam_type) as track_code 
        FROM public.exams 
        WHERE UPPER(exam_code) = :code OR UPPER(exam_type) = :code
        LIMIT 1;
    """
    
    try:
        exam_result = db.execute(text(exam_sql), {"code": clean_code}).mappings().first()
    except Exception:
        exam_result = None

    # FALLBACK LAYER 1: If standard table fails or has no rows, read from curriculum_tree directly
    if not exam_result:
        try:
            fallback_sql = """
                SELECT DISTINCT exam_id as id, exam_type as name, exam_type as track_code
                FROM public.curriculum_tree
                WHERE UPPER(exam_type) = :code
                LIMIT 1;
            """
            exam_result = db.execute(text(fallback_sql), {"code": clean_code}).mappings().first()
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Database execution failed during track resolution: {str(e)}"
            )

    if not exam_result:
        raise HTTPException(
            status_code=404, 
            detail=f"Exam track matching metadata code '{clean_code}' could not be resolved."
        )

    exam_id = str(exam_result["id"])

    # Resolve subjects mapped to this exam pipeline
    subject_sql = """
        SELECT id, exam_id, name, subject_code, discipline
        FROM public.exam_subjects
        WHERE exam_id = :exam_id;
    """
    
    try:
        subject_rows = db.execute(text(subject_sql), {"exam_id": exam_id}).mappings().all()
        subjects_payload = [dict(row) for row in subject_rows]
    except Exception:
        subjects_payload = []

    # FALLBACK LAYER 2: If subjects join table is empty or missing, derive from the curriculum tree nodes
    if not subjects_payload:
        try:
            fallback_subj_sql = """
                SELECT DISTINCT subject_id as id, exam_id, 
                                'Physics' as name, 'PHYSICS' as subject_code, 'Science' as discipline
                FROM public.curriculum_tree
                WHERE exam_id = :exam_id;
            """
            fallback_rows = db.execute(text(fallback_subj_sql), {"exam_id": exam_id}).mappings().all()
            subjects_payload = [dict(row) for row in fallback_rows]
        except Exception:
            pass

    return {
        "exam": {
            "id": exam_id,
            "name": exam_result["name"],
            "exam_code": exam_result["track_code"]
        },
        "subjects": subjects_payload
    }


@router.get("/exam/subjects", response_model=List[ExamSubjectResponse])
def get_public_exam_subjects(db: Session = Depends(get_db)):
    """Fetches a flat list of all exam tracking subjects across the ecosystem."""
    return db.query(models.ExamSubject).all()


@router.get("/exam/{exam_id}/subjects", response_model=List[ExamSubjectResponse])
def get_subjects_by_exam_id(exam_id: str, db: Session = Depends(get_db)):
    """Fetches available curriculum subject nodes linked to an exam pipeline ID."""
    return db.query(models.ExamSubject).filter(models.ExamSubject.exam_id == exam_id).all()


# =====================================================================
# DYNAMIC HIERARCHICAL RECURSIVE SYLLABUS TREE ENDPOINT
# =====================================================================

@router.get("/exam/{exam_id}/tree")
def get_hierarchical_curriculum_tree(
    exam_id: str, 
    subject_id: Optional[str] = Query(None), 
    db: Session = Depends(get_db)
):
    """
    Fetches flat curriculum nodes for a target exam and packs them recursively 
    into an integrated nested multi-pane tree layout array: 
    Units (Level 1) -> Topics (Level 2) -> Leaves (Level 3 Workspaces).
    """
    sql_query = """
        SELECT id, parent_id, title, level, unit_number, display_order, is_leaf, content_type
        FROM public.curriculum_tree
        WHERE exam_id = :exam_id
    """
    params = {"exam_id": exam_id}
    
    if subject_id:
        sql_query += " AND subject_id = :subject_id"
        params["subject_id"] = subject_id
        
    sql_query += " ORDER BY level ASC, unit_number ASC, display_order ASC"
    
    try:
        result = db.execute(text(sql_query), params)
        all_nodes = [dict(row) for row in result.mappings()]
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Database execution failed on structural tree compilation: {str(e)}"
        )

    if not all_nodes:
        return []

    nodes_by_id = {}
    for node in all_nodes:
        node_id = str(node["id"])
        nodes_by_id[node_id] = {
            "id": node_id,
            "parent_id": str(node["parent_id"]) if node["parent_id"] else None,
            "title": node["title"],
            "level": node["level"],
            "unit_number": node["unit_number"],
            "is_leaf": node["is_leaf"],
            "content_type": node["content_type"],
            "children": []
        }

    root_nodes = []
    for n_id, node in nodes_by_id.items():
        p_id = node["parent_id"]
        if p_id is None or p_id not in nodes_by_id:
            root_nodes.append(node)
        else:
            parent = nodes_by_id[p_id]
            parent["children"].append(node)

    return root_nodes


# ==========================================
# 3. ADMIN / INGESTION CONTROL ENDPOINTS
# ==========================================

@admin_router.get("/grades", response_model=List[GradeResponse])
def list_admin_grades(db: Session = Depends(get_db)):
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

@admin_router.get("/exams", response_model=List[ExamResponse])
def get_admin_exams(db: Session = Depends(get_db)):
    return db.query(models.Exam).all()

@admin_router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_admin_exam_tracker(payload: ExamCreate, db: Session = Depends(get_db)):
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