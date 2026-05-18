import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Path
from pydantic import BaseModel, UUID4
from sqlalchemy.orm import Session
from sqlalchemy import text

from app import models
from app.database import get_db

router = APIRouter(prefix="/api/curriculum", tags=["Curriculum Public Framework"])
admin_router = APIRouter(prefix="/api/admin/curriculum", tags=["Admin Curriculum Ingestion Console"])


# ==========================================\n# 1. PYDANTIC DATA TRANSFER SCHEMAS\n# ==========================================\n
# --- K-12 Schema Matrix ---
class GradeCreate(BaseModel):
    name: str
    level: Optional[str] = None
    org_id: Optional[UUID4] = None

class GradeResponse(BaseModel):
    id: UUID4
    name: Optional[str]
    level: Optional[str]
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
    grade_id: Optional[UUID4] = None
    video_url: Optional[str] = ""

    class Config:
        from_attributes = True


# --- Competitive Exam Schema Matrix ---
class ExamCreate(BaseModel):
    name: str
    exam_code: str

class ExamResponse(BaseModel):
    id: UUID4
    name: str
    exam_code: str

    class Config:
        from_attributes = True

class ExamSubjectCreate(BaseModel):
    exam_id: UUID4
    name: str
    subject_code: str
    discipline: str

class ExamSubjectResponse(BaseModel):
    id: UUID4
    exam_id: UUID4
    name: str
    subject_code: str
    discipline: str

    class Config:
        from_attributes = True


# --- NEW: Curriculum Tree & Content Content Payload Schemas ---
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


# ==========================================\n# 2. PUBLIC CONSUMPTION ROUTER PORTS\n# ==========================================\n
@router.get("/resolve-hub")
def resolve_hub_curriculum(
    track_code: str, 
    grade_name: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Core algorithmic multiplexer matching parameters down to active 
    subject components for the learning application dashboard layout.
    """
    if track_code in ["IIT-JEE", "NEET", "IITJEE"]:
        exam_node = db.query(models.Exam).filter(models.Exam.exam_code == "IITJEE").first()
        if not exam_node:
            return []
        
        exam_subs = db.query(models.ExamSubject).filter(models.ExamSubject.exam_id == exam_node.id).all()
        return [
            {
                "id": sub.id,
                "name": sub.name,
                "subject_code": sub.subject_code,
                "discipline": sub.discipline,
                "video_url": f"https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"
            }
            for sub in exam_subs
        ]
    
    else:
        org_node = db.query(models.Organization).filter(models.Organization.name == track_code).first()
        if not org_node:
            return []
            
        grade_query = db.query(models.Grade).filter(models.Grade.org_id == org_node.id)
        if grade_name:
            grade_query = grade_query.filter(models.Grade.name == grade_name)
        grade_node = grade_query.first()
        
        if not grade_node:
            return []
            
        regular_subs = db.query(models.RegularSubject).filter(models.RegularSubject.grade_id == grade_node.id).all()
        return regular_subs


# ────────────────────────────────────────────────────────
# NEW PIPELINE ROUTE: GET COLLAPSIBLE SYLLABUS TREE 
# ────────────────────────────────────────────────────────
@router.get("/{exam_type}/{subject_code}", response_model=CurriculumTreeResponse)
def get_curriculum_tree(
    exam_type: str = Path(..., description="Target exam tracker tag, e.g., iitjee"),
    subject_code: str = Path(..., description="Target subject selection token, e.g., physics"),
    db: Session = Depends(get_db)
):
    """
    Assembles relational components from public.curriculum_tree into an optimized, 
    nested JSON format using automated case-insensitive SQL matching layers.
    """
    # Defensive Normalization: lowercase URL inputs match case-insensitive conditions in SQL
    norm_exam = exam_type.strip().lower()
    norm_subject = subject_code.strip().lower()

    # Query uses LOWER mappings to ensure compatibility with mixed case entries
    query = text("""
        SELECT id, parent_id, title, level, content_type,
               unit_number, is_leaf, content_id, display_order
        FROM public.curriculum_tree
        WHERE LOWER(exam_type) = :exam_type
          AND (LOWER(title) LIKE :subject_pattern OR level > 1)
        ORDER BY unit_number ASC, level ASC, display_order ASC;
    """)
    
    rows = db.execute(query, {
        "exam_type": norm_exam if norm_exam != "iit-jee" else "iitjee",
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

    # Filter out units not belonging to the chosen subject (if multiple exist)
    # level 1 contains titles like 'Unit 1 — Physics and Measurement'
    for row in rows:
        if row.level == 1:
            units_dict[str(row.id)] = {
                "id": str(row.id),
                "title": row.title,
                "unit_number": row.unit_number,
                "content_type": "unit",
                "topics": []
            }
        elif row.level == 2:
            topics_dict[str(row.id)] = {
                "id": str(row.id),
                "title": row.title,
                "content_type": "topic",
                "parent_id": str(row.parent_id),
                "leaves": []
            }
        elif row.level == 3:
            all_leaves.append({
                "id": str(row.id),
                "parent_id": str(row.parent_id),
                "title": row.title,
                "content_type": row.content_type,
                "content_id": str(row.content_id) if row.content_id else None,
                "is_leaf": True
            })

    # Stitching Phase 1: Append Leaf dict nodes directly to Topics
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

    # Stitching Phase 2: Append Topics arrays directly inside parent Unit buckets
    for t_id, topic_data in topics_dict.items():
        p_id = topic_data.pop("parent_id", None)
        if p_id in units_dict:
            units_dict[p_id]["topics"].append(topic_data)

    # Compile maps back to an array structure sorted by unit positioning sequence
    sorted_units = sorted(list(units_dict.values()), key=lambda x: x["unit_number"])

    return {
        "exam_type": exam_type.upper(),
        "subject": subject_code.capitalize(),
        "units": sorted_units
    }


# ────────────────────────────────────────────────────────
# NEW PIPELINE ROUTE: RECOVER CANVAS DISPLAY CONTENT 
# ────────────────────────────────────────────────────────
@router.get("/content/{content_id}", response_model=ContentPayloadResponse)
def get_content_payload(
    content_id: UUID4 = Path(..., description="Target database content row identifier uuid"),
    db: Session = Depends(get_db)
):
    """
    Returns actual textual concept notes or solved numerical frameworks 
    when a user clicks a dynamic leaf.
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
            detail="The active instructional textbook artifact could not be found in the system vector repository."
        )
        
    return {
        "content": result.content,
        "content_type": result.content_type,
        "topic": result.topic,
        "unit": result.unit
    }


# ==========================================\n# 3. ADMINISTRATIVE WORKFLOW MANAGEMENT CHANNELS\n# ==========================================\n
# --- PARTITION A: K-12 INTERFACE CONFIGURATIONS ---

@admin_router.get("/grades", response_model=List[GradeResponse])
def get_admin_grades(db: Session = Depends(get_db)):
    return db.query(models.Grade).all()

@admin_router.post("/grades", response_model=GradeResponse, status_code=status.HTTP_201_CREATED)
def create_admin_grade(payload: GradeCreate, db: Session = Depends(get_db)):
    new_grade = models.Grade(
        name=payload.name.strip(),
        level=payload.level.strip() if payload.level else None,
        org_id=payload.org_id
    )
    db.add(new_grade)
    db.commit()
    db.refresh(new_grade)
    return new_grade

@admin_router.get("/regular/subjects", response_model=List[RegularSubjectResponse])
def get_admin_regular_subjects(db: Session = Depends(get_db)):
    return db.query(models.RegularSubject).all()

@admin_router.post("/regular/subjects", response_model=RegularSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_admin_regular_subject(payload: RegularSubjectCreate, db: Session = Depends(get_db)):
    new_sub = models.RegularSubject(
        name=payload.name.strip(),
        subject_code=payload.subject_code.upper().strip(),
        discipline=payload.discipline.strip(),
        grade_id=payload.grade_id,
        video_url=payload.video_url.strip() if payload.video_url else ""
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return new_sub


# --- PARTITION B: GLOBAL TRACK TRACKING ---

@admin_router.get("/exams", response_model=List[ExamResponse])
def get_admin_exams(db: Session = Depends(get_db)):
    return db.query(models.Exam).all()

@admin_router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_admin_exam_track(payload: ExamCreate, db: Session = Depends(get_db)):
    new_exam = models.Exam(
        name=payload.name.strip(),
        exam_code=payload.exam_code.upper().strip()
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return new_exam


# --- PARTITION C: COMPETITIVE EXAM SUBJECT MAPS ---

@admin_router.get("/exam/subjects", response_model=List[ExamSubjectResponse])
def get_admin_exam_subjects(db: Session = Depends(get_db)):
    """Lists registered exam domain components."""
    return db.query(models.ExamSubject).all()

@admin_router.post("/exam/subjects", response_model=ExamSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_exam_subject_node(payload: ExamSubjectCreate, db: Session = Depends(get_db)):
    """Safely handles dashboard payloads to build data objects without column matching crashes."""
    parent_exam = db.query(models.Exam).filter(models.Exam.id == payload.exam_id).first()
    if not parent_exam:
        raise HTTPException(
            status_code=404,
            detail=f"Target tracking track profile code link '{payload.exam_id}' missing."
        )
    try:
        new_subject = models.ExamSubject(
            exam_id=payload.exam_id,
            name=payload.name.strip(),
            subject_code=payload.subject_code.upper().strip(),
            discipline=payload.discipline.strip()
        )
        db.add(new_subject)
        db.commit()
        db.refresh(new_subject)
        return new_subject
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database transaction failure context: {str(err)}")