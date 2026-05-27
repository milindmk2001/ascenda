import re
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

# Database utility dependency
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

    class Config:
        from_attributes = True


# =====================================================================
# ENDPOINT 1: /resolve-hub (Matches Frontend Dashboard Fetching)
# =====================================================================
@router.get("/resolve-hub", response_model=List[CourseCardResponse])
def resolve_hub_courses(
    track_code: Optional[str] = Query(None, alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    Resolves matching hub courses dynamically based on user selections.
    """
    try:
        # 1. Normalize Grade Inputs (e.g., "Class 11" or "Grade 11" -> "11")
        clean_grade = ""
        if grade_name:
            digits = re.findall(r'\d+', str(grade_name))
            clean_grade = digits[0] if digits else str(grade_name).strip()

        # 2. Identify Target Tracking Strategy
        is_competitive = False
        if track_code:
            track_upper = track_code.upper()
            if "JEE" in track_upper or "NEET" in track_upper:
                is_competitive = True

        # 3. Dynamic Fallback Query
        query_str = """
            SELECT 
                c.id as course_id,
                c.title as course_title,
                COALESCE(rs.subject_code, es.subject_code, 'GEN-TRACK') as subject_code,
                COALESCE(rs.discipline, 'Science') as discipline,
                COALESCE(rs.video_url, 'https://www.youtube.com/embed/dQw4w9WgXcQ') as video_url,
                g.name as grade_name
            FROM public.courses c
            LEFT JOIN public.regular_subjects rs ON c.regular_subject_id = rs.id
            LEFT JOIN public.exam_subjects es ON c.exam_subject_id = es.id
            LEFT JOIN public.grades g ON rs.grade_id = g.id
            WHERE 
                (:is_comp = false AND c.exam_subject_id IS NULL)
                OR (:is_comp = true AND (c.regular_subject_id IS NOT NULL OR c.exam_subject_id IS NOT NULL))
        """
        
        db_results = db.execute(text(query_str), {"is_comp": is_competitive}).mappings().all()
        
        filtered_courses = []
        for row in db_results:
            if clean_grade and str(row["grade_name"]) != clean_grade:
                continue
                
            if track_code and not is_competitive:
                if track_code.upper() not in str(row["subject_code"]).upper() and track_code.upper() not in str(row["course_title"]).upper():
                    continue

            filtered_courses.append({
                "id": str(row["course_id"]),
                "title": row["course_title"],
                "subject_code": row["subject_code"],
                "discipline": row["discipline"],
                "video_url": row["video_url"]
            })
            
        return filtered_courses

    except Exception as e:
        logger.error(f"Error resolving hub content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# ENDPOINT 2: Fetch Multi-Pane Lesson Navigation Tree
# =====================================================================
@router.get("/subjects/{subject_id}/tree", response_model=List[CurriculumNodeResponse])
def get_curriculum_navigation_tree(
    subject_id: str,
    db: Session = Depends(get_db)
):
    try:
        tree_query = text("""
            SELECT 
                ct.id,
                ct.title,
                ct.parent_id,
                ct.is_leaf,
                COALESCE(ct.unit_number, 0) as unit_number,
                COALESCE(ct.display_order, 0) as display_order,
                ct.content_id
            FROM public.curriculum_tree ct
            WHERE ct.subject_id = :subject_id
               OR ct.subject_id IN (
                   SELECT id FROM public.courses 
                   WHERE regular_subject_id = (
                       SELECT regular_subject_id FROM public.courses WHERE id = :subject_id
                   )
               )
            ORDER BY COALESCE(ct.unit_number, 0) ASC, COALESCE(ct.display_order, 0) ASC
        """)
        
        nodes = db.execute(tree_query, {"subject_id": subject_id}).mappings().all()
        
        return [
            {
                "id": str(node["id"]),
                "title": node["title"],
                "parent_id": str(node["parent_id"]) if node["parent_id"] else None,
                "is_leaf": bool(node["is_leaf"]),
                "unit_number": node["unit_number"],
                "display_order": node["display_order"],
                "content_id": str(node["content_id"]) if node["content_id"] else None
            }
            for node in nodes
        ]
    except Exception as e:
        logger.error(f"Error loading curriculum navigation tree matrix: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================================
# ADMIN ROUTE: /grades (Clears Frontend Dropdown Error)
# =====================================================================
@admin_router.get("/grades", response_model=List[GradeResponse])
def get_all_grades(db: Session = Depends(get_db)):
    """
    Fetches available academic grade slots to populate frontend global selector nodes.
    """
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