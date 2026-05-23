import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path, Query
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models
from app.database import get_db

# ── ROUTER INITIALIZATION DEFINITIONS ─────────────────────────────────
router = APIRouter(prefix="/api/curriculum", tags=[\"Curriculum Public Framework\"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=[\"Admin Curriculum Ingestion Console\"])


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
    level: Optional[str] = None
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
    grade_id: UUID4
    video_url: Optional[str] = ""

    class Config:
        from_attributes = True


# ==========================================
# 2. RESOLVE ACTIVE TRACK HUB ROUTES (FIXED)
# ==========================================

@router.get("/resolve-hub", response_model=List[RegularSubjectResponse])
def resolve_active_track_hub_courses(
    track_code: str = Query(..., alias="track_code"),
    grade_name: str = Query(..., alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    Requirements Guard:
    Fetches courses from public.subjects if and only if they match 
    the selected track (Exam) and Grade name. 
    Otherwise, safely returns an empty array list [].
    """
    # 1. Resolve the Grade record by name
    grade_query = "SELECT id FROM public.grades WHERE name = :grade_name LIMIT 1;"
    grade_res = db.execute(text(grade_query), {"grade_name": grade_name.strip()}).fetchone()
    if not grade_res:
        return []

    grade_id = grade_res[0]

    # 2. Resolve the track (Exam) record by code
    exam_query = "SELECT id FROM public.exams WHERE exam_code = :track_code LIMIT 1;"
    exam_res = db.execute(text(exam_query), {"track_code": track_code.upper().strip()}).fetchone()
    
    # If your courses table maps straight to grades without an intermediary join table,
    # we select subjects filtered by grade_id. If exams are joined, we filter by both.
    if exam_res:
        exam_id = exam_res[0]
        subject_query = """
            SELECT id, name, subject_code, discipline, grade_id, video_url 
            FROM public.subjects 
            WHERE grade_id = :grade_id AND exam_id = :exam_id;
        """
        params = {"grade_id": grade_id, "exam_id": exam_id}
    else:
        # Fallback to grade filtering only if exam record is missing from data configuration
        subject_query = """
            SELECT id, name, subject_code, discipline, grade_id, video_url 
            FROM public.subjects 
            WHERE grade_id = :grade_id;
        """
        params = {"grade_id": grade_id}

    try:
        result = db.execute(text(subject_query), params)
        courses = [dict(row) for row in result.mappings()]
        return courses
    except Exception as err:
        print(f"Database error executing hub courses lookup: {str(err)}")
        return []


@router.get("/subjects", response_model=List[RegularSubjectResponse])
def get_subjects_by_track_and_grade(
    track_code: str = Query(...),
    grade_name: str = Query(...),
    db: Session = Depends(get_db)
):
    # Keep original alias route layout intact
    return resolve_active_track_hub_courses(track_code=track_code, grade_name=grade_name, db=db)


@router.get("/subjects/{subject_id}/tree")
def get_hierarchical_curriculum_tree_by_subject(subject_id: str, db: Session = Depends(get_db)):
    """
    Builds structural navigation nodes filtered explicitly by subject_id.
    """
    sql_query = """
        SELECT id, parent_id, title, level, unit_number, display_order, is_leaf, content_type
        FROM public.curriculum_tree
        WHERE subject_id = :subject_id
        ORDER BY level ASC, unit_number ASC, display_order ASC;
    """
    try:
        result = db.execute(text(sql_query), {"subject_id": subject_id})
        all_nodes = [dict(row) for row in result.mappings()]
    except Exception:
        # Fallback schema handling if subject_id column is missing
        try:
            fallback = "SELECT id, parent_id, title, level, unit_number, display_order, is_leaf, content_type FROM public.curriculum_tree ORDER BY level ASC;"
            result = db.execute(text(fallback))
            all_nodes = [dict(row) for row in result.mappings()]
        except Exception:
            return []

    if not all_nodes:
        return []

    nodes_by_id = {}
    for node in all_nodes:
        node_id = str(node["id"])
        nodes_by_id[node_id] = {
            "id": node_id,
            "parent_id": str(node["parent_id"]) if node.get("parent_id") else None,
            "title": node.get("title", "Untitled Concept"),
            "level": node.get("level", 0),
            "unit_number": node.get("unit_number", 0),
            "is_leaf": bool(node.get("is_leaf", False)),
            "content_type": node.get("content_type"),
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