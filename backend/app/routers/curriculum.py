import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db

router = APIRouter(prefix="/api/curriculum", tags=["Curriculum Framework"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Console"])


# ==========================================
# PYDANTIC DATA TRANSFER SCHEMAS
# ==========================================

class GradeResponse(BaseModel):
    id: UUID4
    name: Optional[str] = None
    level: Optional[str] = None
    org_id: Optional[UUID4] = None

    class Config:
        from_attributes = True


class CourseCardResponse(BaseModel):
    id: UUID4  # This is the actual Course ID from public.courses
    name: str
    subject_code: str
    discipline: str
    track_type: str  # "board" or "competitive"
    video_url: Optional[str] = None
    grade_id: Optional[UUID4] = None
    exam_id: Optional[UUID4] = None

    class Config:
        from_attributes = True


# ==========================================
# ENDPOINTS
# ==========================================

@admin_router.get("/grades", response_model=List[GradeResponse])
def get_all_admin_grades(db: Session = Depends(get_db)):
    """
    Fetches all registered grades/academic tiers for dashboard drop-downs.
    """
    try:
        grades_list = db.execute(
            text("SELECT id, name, level, org_id FROM public.grades ORDER BY name ASC")
        ).mappings().all()
        return grades_list
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch administrative grade structural tiers: {str(e)}"
        )


@router.get("/subjects", response_model=List[CourseCardResponse])
def get_filtered_courses(
    track_code: Optional[str] = Query(None, alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    Polymorphic Course Resolver: Queries public.courses joined with regular_subjects 
    or exam_subjects to return cards based on selection.
    """
    try:
        courses_output = []

        # CASE A: User selected a Board Track (e.g., CBSE)
        if track_code == "CBSE" or (grade_name and grade_name.strip()):
            query = text("""
                SELECT 
                    c.id as course_id,
                    rs.name as course_name,
                    rs.subject_code,
                    rs.discipline,
                    rs.video_url,
                    rs.grade_id,
                    NULL::uuid as exam_id
                FROM public.courses c
                JOIN public.regular_subjects rs ON c.regular_subject_id = rs.id
                JOIN public.grades g ON rs.grade_id = g.id
                WHERE c.exam_subject_id IS NULL
                  AND (g.name ILIKE :gname OR g.level ILIKE :gname)
            """)
            # Default to match '11' if frontend passes variation string configurations
            g_search = f"%{grade_name}%" if grade_name else "%11%"
            rows = db.execute(query, {"gname": g_search}).mappings().all()
            
            for r in rows:
                courses_output.append({
                    "id": r["course_id"],
                    "name": r["course_name"],
                    "subject_code": r["subject_code"],
                    "discipline": r["discipline"],
                    "track_type": "board",
                    "video_url": r["video_url"],
                    "grade_id": r["grade_id"],
                    "exam_id": None
                })

        # CASE B: User selected a Competitive Track (e.g., IIT-JEE)
        else:
            query = text("""
                SELECT 
                    c.id as course_id,
                    es.name as course_name,
                    es.subject_code,
                    es.discipline,
                    es.exam_id
                FROM public.courses c
                JOIN public.exam_subjects es ON c.exam_subject_id = es.id
                WHERE c.regular_subject_id IS NULL
                  AND (es.subject_code ILIKE :track OR es.name ILIKE :track)
            """)
            track_search = f"%{track_code}%" if track_code else "%IITJEE%"
            rows = db.execute(query, {"track": track_search}).mappings().all()
            
            for r in rows:
                courses_output.append({
                    "id": r["course_id"],
                    "name": r["course_name"],
                    "subject_code": r["subject_code"],
                    "discipline": r["discipline"],
                    "track_type": "competitive",
                    "video_url": "https://www.youtube.com/embed/dQw4w9WgXcQ",
                    "grade_id": None,
                    "exam_id": r["exam_id"]
                })

        return courses_output

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Polymorphic data collection execution error: {str(e)}"
        )


@router.get("/subjects/{subject_id}/tree")
def get_curriculum_hierarchical_tree(subject_id: str, db: Session = Depends(get_db)):
    """
    Constructs a nested tree structure (Units -> Topics -> Chapters/Leaf Concepts).
    Handles queries whether the incoming ID matches a Course ID, a Regular Subject ID, or an Exam Subject ID.
    """
    try:
        # Resolve real mapping reference by examining what type of node clicked
        course_query = text("""
            SELECT regular_subject_id, exam_subject_id 
            FROM public.courses 
            WHERE id = :sid LIMIT 1
        """)
        course_match = db.execute(course_query, {"sid": subject_id}).mappings().first()

        real_target_id = subject_id
        if course_match:
            real_target_id = str(course_match["regular_subject_id"] or course_match["exam_subject_id"])

        tree_query = text("""
            SELECT id, title, content_type, parent_id, level, unit_number
            FROM public.curriculum_tree
            WHERE subject_id = :target_id OR subject_id = :orig_id
            ORDER BY unit_number ASC, level ASC, title ASC
        """)
        nodes = db.execute(tree_query, {"target_id": real_target_id, "orig_id": subject_id}).mappings().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query curriculum hierarchy: {str(e)}"
        )

    all_nodes = [dict(n) for n in nodes]
    nodes_by_id = {str(node["id"]): {**node, "children": []} for node in all_nodes}
    root_nodes = []

    for node_id, node in nodes_by_id.items():
        parent_id = str(node["parent_id"]) if node["parent_id"] else None
        if parent_id and parent_id in nodes_by_id:
            nodes_by_id[parent_id]["children"].append(node)
        else:
            if node["level"] == 1 or parent_id is None:
                root_nodes.append(node)

    return root_nodes


@router.get("/leaf/{leaf_id}")
def get_individual_leaf_node_details(leaf_id: str, db: Session = Depends(get_db)):
    """
    Resolves full material textbook references for a single leaf concept node.
    """
    try:
        query = text("""
            SELECT id, title, content_type, level, unit_number, subject_id
            FROM public.curriculum_tree
            WHERE id = :lid LIMIT 1
        """)
        result = db.execute(query, {"lid": leaf_id}).mappings().first()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Leaf node resolution error: {str(e)}")

    if not result:
        raise HTTPException(status_code=404, detail="Target leaf concept node could not be located.")

    node_data = dict(result)

    try:
        content_match = db.execute(
            text("""
                SELECT content FROM public.generated_content 
                WHERE topic ILIKE :title AND content_type = 'theory' LIMIT 1
            """),
            {"title": f"%{node_data['title']}%"}
        ).mappings().first()
    except Exception:
        content_match = None

    educational_material = content_match["content"] if content_match and content_match["content"] else f"""# {node_data['title']}
## Core Study Material Objectives
Comprehensive review and concept breakdowns are fully primed for **{node_data['title']}**.
"""

    return {
        "id": str(node_data["id"]),
        "title": node_data["title"] or "Untitled Node",
        "content_type": node_data["content_type"] or "CONCEPT",
        "description": f"Comprehensive study material for {node_data['title']}.",
        "content_text": educational_material,
        "video_placeholder_url": "https://www.w3schools.com/html/mov_bbb.mp4",
        "meta": {
            "level": node_data["level"],
            "unit_number": node_data["unit_number"]
        }
    }


@router.get("/resolve-hub")
def resolve_curriculum_hub_meta(
    track_code: str = Query(..., alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    Resolves incoming track context (e.g. CBSE + Class 11, or IITJEE) down to a real 
    course entry in the database, passing back a valid ID to initialize the sidebar tree.
    """
    try:
        # CASE A: Competitive Stream Profile (e.g., IIT-JEE, NEET)
        if track_code in ["IITJEE", "NEET"] or not grade_name:
            query = text("""
                SELECT c.id as course_id, es.name, es.subject_code 
                FROM public.courses c
                JOIN public.exam_subjects es ON c.exam_subject_id = es.id
                WHERE es.subject_code ILIKE :track OR es.name ILIKE :track
                LIMIT 1
            """)
            record = db.execute(query, {"track": f"%{track_code}%"}).mappings().first()
            if record:
                return {
                    "success": True,
                    "grade_id": None,
                    "org_id": None,
                    "subject_id": str(record["course_id"]),
                    "subject_meta": {"name": record["name"], "code": record["subject_code"]}
                }
        
        # CASE B: Standard School Board Profile (e.g., CBSE, ICSE)
        else:
            query = text("""
                SELECT c.id as course_id, rs.name, rs.subject_code, g.id as gid, g.org_id
                FROM public.courses c
                JOIN public.regular_subjects rs ON c.regular_subject_id = rs.id
                JOIN public.grades g ON rs.grade_id = g.id
                WHERE (g.name ILIKE :gname OR g.level ILIKE :gname)
                  AND (rs.subject_code ILIKE :track OR rs.name ILIKE :track)
                LIMIT 1
            """)
            record = db.execute(query, {"gname": f"%{grade_name}%", "track": f"%{track_code}%"}).mappings().first()
            if record:
                return {
                    "success": True,
                    "grade_id": str(record["gid"]),
                    "org_id": str(record["org_id"]) if record["org_id"] else None,
                    "subject_id": str(record["course_id"]),
                    "subject_meta": {"name": record["name"], "code": record["subject_code"]}
                }

        # Safe fallback if nothing matches yet
        return {
            "success": False,
            "msg": f"No active course mapping track discovered matching selection criteria: '{track_code}'",
            "subject_id": None,
            "grade_id": None
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Polymorphic hub metadata routing layout translation failed: {str(e)}"
        )