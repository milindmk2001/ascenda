import re
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

# Import your database session utility injection dependency
from app.database import get_db  

# Initialize Router and Logger
router = APIRouter(prefix="/api/curriculum", tags=["Curriculum"])
logger = logging.getLogger(__name__)

# 👇 FIXES RAILWAY CRASH: Added administrative route pointer requested by app/main.py
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Curriculum"])


# =====================================================================
# PYDANTIC SCHEMAS (Response Models matching your multi-pane UI layer)
# =====================================================================

class CourseCardResponse(BaseModel):
    id: str
    title: str
    subject_code: str
    discipline: str
    video_url: Optional[str] = None

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
# ENDPOINT 1: Fetch and filter courses for the Dashboard Hub
# =====================================================================
@router.get("/subjects", response_model=List[CourseCardResponse])
def get_filtered_subjects(
    track_code: Optional[str] = Query(None, alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    Fetches available courses from the hub. Handles the mutual exclusivity 
    of regular_subject_id vs exam_subject_id dynamically.
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

        # 3. Robust Unified Left-Join Lookup Query
        # Avoids rigid inner join drops if metadata profiles aren't fully baked
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
                -- Board Routing Rule
                (:is_comp = false AND c.exam_subject_id IS NULL)
                -- Competitive Routing Rule (Allows fallback to regular courses if dedicated entries don't exist)
                OR (:is_comp = true AND (c.regular_subject_id IS NOT NULL OR c.exam_subject_id IS NOT NULL))
        """
        
        db_results = db.execute(text(query_str), {"is_comp": is_competitive}).mappings().all()
        
        filtered_courses = []
        for row in db_results:
            # Apply extracted digits filter to safely align with your '11' / '12' text records
            if clean_grade and str(row["grade_name"]) != clean_grade:
                continue
                
            # Filter standard tracks by board prefix context (e.g., separating CBSE vs ICSE text profiles)
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
        logger.error(f"Error fetching subjects from hub routing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database Hub Resolver error: {str(e)}")


# =====================================================================
# ENDPOINT 2: Fetch Multi-Pane Lesson Traversal Navigation Tree
# =====================================================================
@router.get("/subjects/{subject_id}/tree", response_model=List[CurriculumNodeResponse])
def get_curriculum_navigation_tree(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """
    Loads all nested units, chapters, topics, and interactive asset leaf nodes.
    Bridges the relationship whether the ID passed is a Core Subject ID or Course UUID.
    """
    try:
        # Relational check: Finds any structure elements connected directly to the ID, 
        # or matches items bound via the underlying shared 'regular_subject_id'.
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
        
        # Turn database results into schema-compliant dict objects
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
        logger.error(f"Error loading curriculum tree traversal matrix for target {subject_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Curriculum Tree Resolution Error: {str(e)}")


# =====================================================================
# ADMIN ROUTE PLACEHOLDERS (Prevents mounting crashes in main.py)
# =====================================================================
@admin_router.get("/status")
def get_admin_status():
    return {"status": "active", "scope": "curriculum_management"}