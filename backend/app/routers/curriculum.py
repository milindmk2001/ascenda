import re
import logging
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.database import get_db

router       = APIRouter(prefix="/api/curriculum",       tags=["Curriculum"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Curriculum"])

logger = logging.getLogger(__name__)


# ── PYDANTIC SCHEMAS ──────────────────────────────────────────

class CourseCardResponse(BaseModel):
    id:           str
    title:        str
    subject_code: str
    subject_name: Optional[str] = None   # ← added: React uses this for card label
    discipline:   str
    video_url:    Optional[str] = None

    class Config:
        from_attributes = True


class GradeResponse(BaseModel):
    id:    str
    name:  str
    level: Optional[int] = None

    class Config:
        from_attributes = True


class CurriculumNodeResponse(BaseModel):
    id:            str
    title:         str
    parent_id:     Optional[str] = None
    is_leaf:       bool
    unit_number:   int
    display_order: int
    content_id:    Optional[str] = None
    content_type:  Optional[str] = None
    level:         Optional[int] = None

    class Config:
        from_attributes = True


# ── ENDPOINT 1: resolve-hub ───────────────────────────────────

@router.get("/resolve-hub", response_model=List[CourseCardResponse])
def resolve_hub_courses(
    track_code: Optional[str] = Query(None, alias="track_code"),
    grade_name: Optional[str] = Query(None, alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    Returns course cards for the homepage hub.
    Uses public.v_course_hub view — handles board and competitive tracks.
    """
    # Extract numeric grade: 'Class 11' → '11', '11' → '11'
    clean_grade = ""
    if grade_name:
        digits = re.findall(r'\d+', str(grade_name))
        clean_grade = digits[0] if digits else ""

    # Competitive if track contains JEE or NEET
    is_competitive = bool(track_code) and any(
        k in track_code.upper() for k in ["JEE", "NEET"]
    )

    # Fix 2 — Minor Hardening: Explicit diagnostic logging for debugging parameter state transitions
    logger.info(f"resolve-hub called: track={track_code} grade={clean_grade} competitive={is_competitive}")

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
            results = db.execute(
                query, {"prefix": f"{prefix}%"}
            ).mappings().all()

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

        return [
            {
                "id":           str(row["id"]),
                "title":        row["title"]        or "",
                "subject_code": row["subject_code"] or "",
                "subject_name": row.get("subject_name") or row.get("title") or "",
                "discipline":   row["discipline"]   or "General",
                "video_url":    row.get("video_url") or None,
            }
            for row in results
        ]

    except Exception as e:
        logger.error(f"resolve-hub error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ── ENDPOINT 2: curriculum tree ───────────────────────────────

@router.get(
    "/subjects/{subject_id}/tree",
    response_model=List[CurriculumNodeResponse]
)
def get_curriculum_navigation_tree(
    subject_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns full curriculum tree for a given course_id.
    Uses public.v_curriculum_by_course to bridge course_id → exam_subject_id.
    """
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
        nodes = db.execute(
            query, {"subject_id": subject_id}
        ).mappings().all()

        return [
            {
                "id":           str(node["id"]),
                "title":        node["title"],
                "parent_id":    str(node["parent_id"]) if node["parent_id"] else None,
                "is_leaf":      bool(node["is_leaf"]),
                "unit_number":  node["unit_number"],
                "display_order": node["display_order"],
                "content_id":   str(node["content_id"]) if node["content_id"] else None,
                "content_type": node["content_type"],
                "level":        node["level"],
            }
            for node in nodes
        ]

    except Exception as e:
        logger.error(f"Curriculum tree error for {subject_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ── ADMIN: grades ─────────────────────────────────────────────

@admin_router.get("/grades", response_model=List[GradeResponse])
def get_all_grades(db: Session = Depends(get_db)):
    try:
        query   = text(
            "SELECT id, name, level FROM public.grades "
            "ORDER BY level ASC NULLS LAST"
        )
        results = db.execute(query).mappings().all()
        return [
            {
                "id":    str(row["id"]),
                "name":  str(row["name"]),
                "level": row["level"],
            }
            for row in results
        ]
    except Exception as e:
        logger.error(f"Grades fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ── ENDPOINT 3: fetch leaf content ───────────────────────────

@router.get("/leaf/{leaf_id}")
def get_leaf_content(
    leaf_id: str,
    db: Session = Depends(get_db)
):
    """
    Returns content for a curriculum leaf node.
    Uses content_id FK to fetch from generated_content.
    """
    try:
        query = text("""
            SELECT
                gc.id,
                gc.content,
                gc.content_type,
                gc.topic,
                gc.unit,
                gc.difficulty,
                ct.title       AS leaf_title,
                ct.content_type AS leaf_type,
                ct.unit_number,
                ct.is_leaf
            FROM public.curriculum_tree ct
            JOIN public.generated_content gc
              ON gc.id = ct.content_id
            WHERE ct.id = :leaf_id
              AND ct.is_leaf = true
        """)
        row = db.execute(
            query, {"leaf_id": leaf_id}
        ).mappings().first()

        if not row:
            # content_id may be null — return leaf metadata only
            meta_query = text("""
                SELECT
                    ct.id,
                    ct.title,
                    ct.content_type,
                    ct.unit_number,
                    ct.is_leaf,
                    ct.content_id,
                    parent.title AS topic_title
                FROM public.curriculum_tree ct
                LEFT JOIN public.curriculum_tree parent
                  ON parent.id = ct.parent_id
                WHERE ct.id = :leaf_id
            """)
            meta = db.execute(
                meta_query, {"leaf_id": leaf_id}
            ).mappings().first()

            if not meta:
                raise HTTPException(status_code=404, detail="Leaf node not found")

            return {
                "id":           str(meta["id"]),
                "content":      None,
                "content_type": meta["content_type"],
                "topic":        meta["topic_title"] or meta["title"],
                "leaf_title":   meta["title"],
                "unit_number":  meta["unit_number"],
                "is_leaf":      True,
                "content_id":   str(meta["content_id"]) if meta["content_id"] else None,
            }

        return {
            "id":           leaf_id,
            "content":      row["content"],
            "content_type": row["content_type"],
            "topic":        row["topic"],
            "unit":         row["unit"],
            "leaf_title":   row["leaf_title"],
            "leaf_type":    row["leaf_type"],
            "difficulty":   row["difficulty"],
            "unit_number":  row["unit_number"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Leaf content error for {leaf_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))