import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.schemas import CourseCardResponse, GradeResponse

router = APIRouter(prefix="/api/curriculum", tags=["Curriculum Framework"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Console"])

# ==========================================
# ENDPOINTS
# ==========================================

@admin_router.get("/grades", response_model=List[GradeResponse])
def get_all_admin_grades(db: Session = Depends(get_db)):
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
def get_filtered_courses_from_hub(
    track_code: Optional[str] = Query(None, alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    try:
        courses_output = []
        clean_track = str(track_code).strip() if track_code else ""
        clean_grade = str(grade_name).strip() if grade_name else ""

        # Check track structure
        is_board = clean_track in ["CBSE", "ICSE"] or (clean_grade != "")

        if is_board:
            query = text("""
                SELECT 
                    c.id as course_id,
                    c.title as course_title,
                    rs.subject_code,
                    rs.discipline,
                    rs.video_url,
                    rs.grade_id
                FROM public.courses c
                JOIN public.regular_subjects rs ON c.regular_subject_id = rs.id
                JOIN public.grades g ON rs.grade_id = g.id
                WHERE c.exam_subject_id IS NULL
                  AND (g.name ILIKE :gname OR :gname = '%%')
            """)
            g_search = f"%{clean_grade}%" if clean_grade else "%%"
            rows = db.execute(query, {"gname": g_search}).mappings().all()
            
            for r in rows:
                courses_output.append({
                    "id": r["course_id"],
                    "name": r["course_title"],
                    "subject_code": r["subject_code"],
                    "discipline": r["discipline"],
                    "track_type": "board",
                    "video_url": r["video_url"],
                    "grade_id": r["grade_id"],
                    "exam_id": None
                })

        else:
            query = text("""
                SELECT 
                    c.id as course_id,
                    c.title as course_title,
                    es.subject_code,
                    es.discipline,
                    es.exam_id
                FROM public.courses c
                JOIN public.exam_subjects es ON c.exam_subject_id = es.id
                WHERE c.regular_subject_id IS NULL
                  AND (es.subject_code ILIKE :track OR es.name ILIKE :track OR :track = '%%')
            """)
            track_search = f"%{clean_track}%" if clean_track else "%%"
            rows = db.execute(query, {"track": track_search}).mappings().all()
            
            for r in rows:
                courses_output.append({
                    "id": r["course_id"],
                    "name": r["course_title"],
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
            detail=f"Failed to load dynamic stream profiles from courses table: {str(e)}"
        )


@router.get("/subjects/{subject_id}/tree")
def get_curriculum_hierarchical_tree(subject_id: str, db: Session = Depends(get_db)):
    try:
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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query curriculum hierarchical tree parameters: {str(e)}"
        )


@router.get("/resolve-hub")
def resolve_curriculum_hub_meta(
    track_code: str = Query(..., alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    try:
        clean_track = str(track_code).strip() if track_code else ""
        clean_grade = str(grade_name).strip() if grade_name else ""

        # Competitive paths (IITJEE/NEET)
        if clean_track in ["IITJEE", "NEET", "IIT-JEE Advance"] or not clean_grade:
            query = text("""
                SELECT c.id as course_id, es.name as exam_subject_name, es.subject_code 
                FROM public.courses c
                JOIN public.exam_subjects es ON c.exam_subject_id = es.id
                WHERE es.subject_code ILIKE :track OR es.name ILIKE :track OR :track ILIKE ('%%' || es.subject_code || '%%')
                LIMIT 1
            """)
            # Extract basic prefix if full token string like IIT-JEE Advance arrives
            search_param = "IITJEE" if "IIT" in clean_track else clean_track
            record = db.execute(query, {"track": f"%{search_param}%"}).mappings().first()
            if record:
                return {
                    "success": True,
                    "grade_id": None,
                    "org_id": None,
                    "subject_id": str(record["course_id"]),
                    "subject_meta": {"name": record["exam_subject_name"], "code": record["subject_code"]}
                }
        
        # School board paths
        else:
            query = text("""
                SELECT 
                    c.id as course_id, 
                    c.title as course_title, 
                    rs.subject_code, 
                    g.id as gid, 
                    g.org_id
                FROM public.courses c
                JOIN public.regular_subjects rs ON c.regular_subject_id = rs.id
                JOIN public.grades g ON rs.grade_id = g.id
                WHERE g.name ILIKE :gname OR :gname ILIKE ('%%' || g.name || '%%')
                LIMIT 1
            """)
            # Handles checking strings like "Class 11" safely against database record "11"
            digit_grade = "".join(filter(str.isdigit, clean_grade))
            search_grade = f"%{digit_grade}%" if digit_grade else f"%{clean_grade}%"
            record = db.execute(query, {"gname": search_grade}).mappings().first()
            if record:
                return {
                    "success": True,
                    "grade_id": str(record["gid"]),
                    "org_id": str(record["org_id"]) if record["org_id"] else None,
                    "subject_id": str(record["course_id"]),
                    "subject_meta": {"name": record["course_title"], "code": record["subject_code"]}
                }

        # Dynamic fallback row provider
        fallback_record = db.execute(text("""
            SELECT c.id as course_id, c.title as course_title, COALESCE(rs.subject_code, 'GEN') as subject_code
            FROM public.courses c
            LEFT JOIN public.regular_subjects rs ON c.regular_subject_id = rs.id
            LIMIT 1
        """)).mappings().first()
        
        if fallback_record:
            return {
                "success": True,
                "grade_id": None,
                "org_id": None,
                "subject_id": str(fallback_record["course_id"]),
                "subject_meta": {"name": fallback_record["course_title"], "code": fallback_record["subject_code"]}
            }

        return {"success": False, "subject_id": None, "grade_id": None}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Polymorphic engine hub breakdown: {str(e)}"
        )