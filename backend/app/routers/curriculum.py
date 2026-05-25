import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
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
    name: str
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
    video_url: Optional[str]
    created_at: Any

    class Config:
        from_attributes = True


# ==========================================
# 2. PUBLIC PUBLIC-FACING ROUTER ENDPOINTS
# ==========================================

@admin_router.get("/grades", response_model=List[GradeResponse])
def get_all_admin_grades(db: Session = Depends(get_db)):
    """
    Fetches all registered grades/academic tiers for the admin ingestion dashboard layout.
    """
    try:
        # Queries the grades table using your SQLAlchemy model mapping
        grades_list = db.execute(
            text("SELECT id, name, level, org_id FROM public.grades ORDER BY name ASC")
        ).mappings().all()
        return grades_list
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch administrative grade structural tiers: {str(e)}"
        )
    

@router.get("/subjects", response_model=List[RegularSubjectResponse])
def get_all_public_subjects(db: Session = Depends(get_db)):
    """
    Retrieves all available core multi-disciplinary educational tracking pathways.
    """
    return db.query(models.Subject).order_by(models.Subject.name).all()


@router.get("/subjects/{subject_id}/tree")
def get_curriculum_hierarchical_tree(subject_id: str, db: Session = Depends(get_db)):
    """
    Constructs a nested tree structure (Units -> Topics -> Chapters/Leaf Concepts)
    to feed the frontend sidebar navigation tree component.
    """
    try:
        query = text("""
            SELECT id, title, content_type, parent_id, level, unit_number
            FROM public.curriculum_tree
            WHERE subject_id = :sid
            ORDER BY unit_number ASC, level ASC, title ASC
        """)
        nodes = db.execute(query, {"sid": subject_id}).mappings().all()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to query curriculum relational topography framework: {str(e)}"
        )

    # Transform SQLAlchemy mapping proxies into pure manipulatable dictionaries
    all_nodes = [dict(n) for n in nodes]
    
    # Fast access lookups map tracking references
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
    Resolves comprehensive tracking data models and textbook references for a single leaf node.
    Synchronizes with public.generated_content to feed structural text down onto Left Panel views.
    """
    try:
        query = text("""
            SELECT id, title, content_type, level, unit_number, subject_id
            FROM public.curriculum_tree
            WHERE id = :lid LIMIT 1
        """)
        result = db.execute(query, {"lid": leaf_id}).mappings().first()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database concept processing transaction dropped: {str(e)}"
        )

    if not result:
        raise HTTPException(
            status_code=404, 
            detail=f"Target leaf concept node reference '{leaf_id}' could not be located."
        )

    node_data = dict(result)

    # Data-Driven Lookup: Query matching ingested text content
    try:
        content_match = db.execute(
            text("""
                SELECT content 
                FROM public.generated_content 
                WHERE topic ILIKE :title 
                  AND content_type = 'theory' 
                LIMIT 1
            """),
            {"title": f"%{node_data['title']}%"}
        ).mappings().first()
    except Exception:
        content_match = None

    # Resolve core markdown contents without falling through or causing syntax fragmentation
    if content_match and content_match["content"]:
        educational_material = content_match["content"]
    else:
        educational_material = f"""# {node_data['title']}
    
## Core Curriculum Objectives
Comprehensive study material, instructional breakdowns, and structured analytical benchmarks for **{node_data['title']}**.

### Analytical Focus
* Systematic formulation and structured review of fundamental parameters.
* Test-oriented deep dives tailored for competitive examination assessment environments.
"""

    return {
        "id": str(node_data["id"]),
        "title": node_data["title"] or "Untitled Concept Node",
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
    grade_name: str = Query(..., alias="grade_name"),
    db: Session = Depends(get_db)
):
    """
    ADDED ENDPOINT:
    Resolves human-readable track parameters and grade limits (e.g., CBSE/IITJEE & 11) down to 
    functional primary database UUIDs to safely initialize workspace states on frontend dashboards.
    """
    try:
        # 1. Resolve Grade ID and Organization Parent references safely
        grade_query = text("""
            SELECT id, name, org_id 
            FROM public.grades 
            WHERE name ILIKE :gname OR level ILIKE :gname 
            LIMIT 1
        """)
        grade_record = db.execute(grade_query, {"gname": f"%{grade_name}%"}).mappings().first()
        
        if not grade_record:
            return {
                "success": False,
                "msg": f"Grade descriptor '{grade_name}' not discovered within backend schemas.",
                "subject_id": None,
                "grade_id": None
            }

        # 2. Extract relative subject path configurations tied directly to this grade layer
        subject_query = text("""
            SELECT id, name, subject_code 
            FROM public.subjects 
            WHERE grade_id = :gid 
              AND (subject_code ILIKE :track OR name ILIKE :track)
            LIMIT 1
        """)
        subject_record = db.execute(
            subject_query, 
            {"gid": grade_record["id"], "track": f"%{track_code}%"}
        ).mappings().first()

        return {
            "success": True,
            "grade_id": str(grade_record["id"]),
            "org_id": str(grade_record["org_id"]) if grade_record["org_id"] else None,
            "subject_id": str(subject_record["id"]) if subject_record else None,
            "subject_meta": {
                "name": subject_record["name"] if subject_record else "General Tracking Node",
                "code": subject_record["subject_code"] if subject_record else track_code
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal system mapping error during parameters hub resolution: {str(e)}"
        )