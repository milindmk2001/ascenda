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