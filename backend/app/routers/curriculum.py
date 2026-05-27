import re
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

# Import database session utility injection dependency
from app.database import get_db  

# Initialize Routers to match main.py mounting points
router = APIRouter(prefix="/api/curriculum", tags=["Curriculum"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Curriculum"])

logger = logging.getLogger(__name__)

# =====================================================================
# PYDANTIC SCHEMAS
# =====================================================================

class CourseCardResponse(BaseModel):
    id: str
    title: str
    subject_code: str
    discipline: str
    video_url: Optional[str] = None

    class Config:
        from_attributes = True


class GradeResponse(BaseModel):
    id: str
    name: str
    level: Optional[int] = None

    class Config:
        from_attributes = True


class CurriculumNodeResponse(BaseModel):
    id: str
    title: str
    parent_id: Optional[str] = None
    is_leaf: bool
    unit_number: int
    display_order: int
    content_id: Optional[str] = None
    content_type: Optional[str] = None
    level: Optional[int] = None

    class Config:
        from_attributes = True


# =====================================================================
# ENDPOINT 1: /resolve-hub (Fixed video_url Column Crash)
# =====================================================================
@router.get("/resolve-hub", response_model=List[CourseCardResponse])
def resolve_hub_courses(
    track_code: Optional[str] = Query(None, alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    Resolves matching hub courses dynamically by routing queries through 
    the public.v_course_hub view based on track classifications.
    """
    # 1. Normalize Grade Inputs (Extract pure numeric characters: e.g., 'Class 11' -> '11')
    clean_grade = ""
    if grade_name:
        digits = re.findall(r'\d+', str(grade_name))
        clean_grade = digits[0] if digits else ""

    # 2. Segment competitive vs board-level parsing branches
    is_competitive = bool(track_code) and any(
        k in track_code.upper() for k in ["JEE", "NEET"]
    )

    try:
        if is_competitive:
            prefix = "IITJEE" if "JEE" in track_code.upper() else "NEET"
            query = text("""
                SELECT
                    course_id    AS id,
                    course_title AS title,
                    subject_code,
                    subject_name,
                    discipline
                FROM public.v_course_hub
                WHERE track_type   = 'competitive'
                  AND subject_code LIKE :prefix
                ORDER BY subject_name
            """)
            results = db.execute(query, {"prefix": f"{prefix}%"}).mappings().all()
        else:
            query = text("""
                SELECT
                    course_id    AS id,
                    course_title AS title,
                    subject_code,
                    subject_name,
                    discipline
                FROM public.v_course_hub
                WHERE track_type   = 'board'
                  AND grade_number = :grade
                  AND subject_code ILIKE :track
                ORDER BY subject_name
            """)
            results = db.execute(query, {
                "grade": clean_grade,
                "track": f"%{track_code}%"
            }).mappings().all()

        # 3. Safe dictionary building with explicit Python-level video fallback
        return [
            {
                "id": str(row["id"]),
                "title": row["title"],
                "subject_code": row["subject_code"],
                "discipline": row["discipline"],
                # 👇 Handles fallback safely out of the DB column structure execution context
                "video_url": str(row["video_url"]) if ("video_url" in row and row["video_url"]) else "https://www.youtube.com/embed/dQw4w9WgXcQ"
            }
            for row in results
        ]

    except Exception as e:
        logger.error(f"Error executing resolve-hub mapping: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# ENDPOINT 2: Fetch Navigation Tree 
# =====================================================================
@router.get("/subjects/{subject_id}/tree", response_model=List[CurriculumNodeResponse])
def get_curriculum_navigation_tree(
    subject_id: str,
    db: Session = Depends(get_db)
):
    try:
        query = text("""
            SELECT
                id,
                title,
                parent_id,
                is_leaf,
                COALESCE(unit_number, 0)   AS unit_number,
                COALESCE(display_order, 0) AS display_order,
                content_id,
                content_type,
                level
            FROM public.v_curriculum_by_course
            WHERE linked_course_id = :subject_id
            ORDER BY unit_number ASC, display_order ASC
        """)
        nodes = db.execute(query, {"subject_id": subject_id}).mappings().all()
        
        return [
            {
                "id": str(node["id"]),
                "title": node["title"],
                "parent_id": str(node["parent_id"]) if node["parent_id"] else None,
                "is_leaf": bool(node["is_leaf"]),
                "unit_number": node["unit_number"],
                "display_order": node["display_order"],
                "content_id": str(node["content_id"]) if node["content_id"] else None,
                "content_type": node["content_type"],
                "level": node["level"]
            }
            for node in nodes
        ]

    except Exception as e:
        logger.error(f"Curriculum tree extraction execution error for target {subject_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# ADMIN ROUTE: /grades
# =====================================================================
@admin_router.get("/grades", response_model=List[GradeResponse])
def get_all_grades(db: Session = Depends(get_db)):
    try:
        query = text("SELECT id, name, level FROM public.grades ORDER BY level ASC NULLS LAST")
        results = db.execute(query).mappings().all()
        return [
            {
                "id": str(row["id"]),
                "name": str(row["name"]),
                "level": row["level"]
            }
            for row in results
        ]
    except Exception as e:
        logger.error(f"Error fetching grades metadata lookup: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))