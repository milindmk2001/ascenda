import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models
from app.database import get_db

# Reuse the existing routers mounted in main.py
router = APIRouter(prefix="/api/curriculum", tags=["Curriculum Public Framework"])


# ==========================================
# PYDANTIC SCHEMAS FOR THE TREE
# ==========================================

class LeafNode(BaseModel):
    id: UUID4
    title: str
    content_type: str
    content_id: Optional[UUID4] = None
    is_leaf: bool = True

class TopicNode(BaseModel):
    id: UUID4
    title: str
    content_type: str = "topic"
    leaves: List[LeafNode] = []

class UnitNode(BaseModel):
    id: UUID4
    title: str
    unit_number: int
    content_type: str = "unit"
    topics: List[TopicNode] = []

class CurriculumTreeResponse(BaseModel):
    exam_type: str
    subject: str
    units: List[UnitNode]

class ContentPayloadResponse(BaseModel):
    content: str
    content_type: str
    topic: str
    unit: str


# ==========================================
# ROUTE ENDPOINTS
# ==========================================

@router.get("/{exam_type}/{subject_code}", response_model=CurriculumTreeResponse)
def get_curriculum_tree(
    exam_type: str = Path(..., description="Target exam tracker tag, e.g., iitjee"),
    subject_code: str = Path(..., description="Target subject selection token, e.g., physics"),
    db: Session = Depends(get_db)
):
    """
    Fetches the flat curriculum rows for an exam and structures them into a 
    nested Unit -> Topic -> Leaf dictionary hierarchy in O(N) time.
    """
    # Normalize inputs for robust SQL matching
    norm_exam = exam_type.strip().lower().replace("-", "")
    if norm_exam == "iitjee":
        norm_exam = "iit_jee"  # Sync with DB table normalization strings
        
    norm_subject = subject_code.strip().lower()

    # Parametrized raw query targeting the curriculum materialized schema structure
    query = text("""
        SELECT id, parent_id, title, level, content_type,
               unit_number, is_leaf, content_id, display_order
        FROM public.curriculum_tree
        WHERE (LOWER(exam_type) = :exam_type OR REPLACE(LOWER(exam_type), '_', '') = :exam_clean)
          AND (LOWER(title) LIKE :subject_pattern OR level > 1)
        ORDER BY unit_number ASC, level ASC, display_order ASC;
    """)
    
    rows = db.execute(query, {
        "exam_type": norm_exam,
        "exam_clean": norm_exam.replace("_", ""),
        "subject_pattern": f"%{norm_subject}%"
    }).fetchall()
    
    if not rows:
        return {
            "exam_type": exam_type.upper(),
            "subject": subject_code.capitalize(),
            "units": []
        }

    units_dict: Dict[str, Dict[str, Any]] = {}
    topics_dict: Dict[str, Dict[str, Any]] = {}
    all_leaves: List[Dict[str, Any]] = []

    # Single-pass parsing of the database rows
    for row in rows:
        row_id = str(row.id)
        if row.level == 1:
            units_dict[row_id] = {
                "id": row.id,
                "title": row.title,
                "unit_number": row.unit_number,
                "content_type": "unit",
                "topics": []
            }
        elif row.level == 2:
            topics_dict[row_id] = {
                "id": row.id,
                "title": row.title,
                "content_type": "topic",
                "parent_id": str(row.parent_id),
                "leaves": []
            }
        elif row.level == 3:
            all_leaves.append({
                "id": row.id,
                "parent_id": str(row.parent_id),
                "title": row.title,
                "content_type": row.content_type,
                "content_id": row.content_id,
                "is_leaf": True
            })

    # Nest level 3 leaves inside level 2 topics
    for leaf in all_leaves:
        p_id = leaf["parent_id"]
        if p_id in topics_dict:
            topics_dict[p_id]["leaves"].append({
                "id": leaf["id"],
                "title": leaf["title"],
                "content_type": leaf["content_type"],
                "content_id": leaf["content_id"],
                "is_leaf": True
            })

    # Nest level 2 topics inside level 1 units
    for t_id, topic_data in topics_dict.items():
        p_id = topic_data.pop("parent_id", None)
        if p_id in units_dict:
            units_dict[p_id]["topics"].append(topic_data)

    # Output sorted arrays aligned to defined sequence ordering constraints
    sorted_units = sorted(list(units_dict.values()), key=lambda x: x["unit_number"])

    return {
        "exam_type": exam_type.upper(),
        "subject": subject_code.capitalize(),
        "units": sorted_units
    }


@router.get("/content/{content_id}", response_model=ContentPayloadResponse)
def get_content_payload(
    content_id: UUID4 = Path(..., description="Target data payload unique record identifier"),
    db: Session = Depends(get_db)
):
    """
    Returns text documentation contents for canvas node viewports.
    """
    query = text("""
        SELECT content, content_type, topic, unit
        FROM public.generated_content
        WHERE id = :content_id
        LIMIT 1;
    """)
    
    result = db.execute(query, {"content_id": str(content_id)}).fetchone()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="The active core knowledge asset could not be located."
        )
        
    return {
        "content": result.content,
        "content_type": result.content_type,
        "topic": result.topic,
        "unit": result.unit
    }