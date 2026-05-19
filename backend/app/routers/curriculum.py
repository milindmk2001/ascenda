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


# ==========================================
# 1. PYDANTIC DATA TRANSFER SCHEMAS
# ==========================================

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


# ==========================================
# 2. PUBLIC CONSUMPTION ROUTER PORTS
# ==========================================

@router.get("/resolve-hub")
def resolve_hub_curriculum(
    track_code: str, 
    grade_name: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Core algorithmic multiplexer matching incoming dashboard selectors
    to corresponding dataset structures in PostgreSQL database engines.
    """
    # Normalize structural strings to cleanly match database entries (IIT-JEE -> IITJEE)
    clean_track = track_code.replace("-", "").strip().upper()

    if clean_track in ["IITJEE", "NEET"]:
        # FIXED: Changed models.Exam.exam_code to models.Exam.code to match schema layout
        exam_node = db.query(models.Exam).filter(models.Exam.code == clean_track).first()
        
        if not exam_node:
            # Fallback check in case the table contains hyphenated strings ("IIT-JEE")
            fallback_track = track_code.strip().upper()
            exam_node = db.query(models.Exam).filter(models.Exam.code == fallback_track).first()
            
        if not exam_node:
            return []
            
        exam_subs = db.query(models.ExamSubject).filter(models.ExamSubject.exam_id == exam_node.id).all()
        return [
            {
                "id": str(sub.id),
                "name": sub.name,
                "subject_code": sub.subject_code,
                "discipline": sub.discipline,
                "video_url": "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"
            }
            for sub in exam_subs
        ]
        
    else:
        # Standard Multi-Tenant K-12 Track Pathway (CBSE / ICSE)
        org_node = db.query(models.Organization).filter(models.Organization.name == track_code.strip().upper()).first()
        if not org_node:
            return []
            
        if not grade_name:
            return []
            
        cleaned_grade = grade_name.lower().replace("class", "").strip()
        
        # Scope-locked query matching the specific active tenant organization id context
        grade_node = db.query(models.Grade).filter(
            models.Grade.org_id == org_node.id,
            models.Grade.name.like(f"%{cleaned_grade}%")
        ).first()
        
        if not grade_node:
            return []
            
        regular_subs = db.query(models.RegularSubject).filter(models.RegularSubject.grade_id == grade_node.id).all()
        return [
            {
                "id": str(sub.id),
                "name": sub.name,
                "subject_code": sub.subject_code,
                "discipline": sub.discipline,
                "video_url": sub.video_url if getattr(sub, "video_url", None) else ""
            }
            for sub in regular_subs
        ]


@router.get("/{exam_type}/{subject_code}", response_model=CurriculumTreeResponse)
def get_curriculum_tree(
    exam_type: str = Path(..., description="Target exam tracker tag, e.g., iitjee"),
    subject_code: str = Path(..., description="Target subject selection token, e.g., physics"),
    db: Session = Depends(get_db)
):
    norm_exam = exam_type.strip().lower().replace("-", "")
    norm_subject = subject_code.strip().lower()

    query = text("""
        SELECT id, parent_id, title, level, content_type,
               unit_number, is_leaf, content_id, display_order
        FROM public.curriculum_tree
        WHERE (LOWER(exam_type) = :exam_type OR REPLACE(LOWER(exam_type), '-', '') = :exam_type)
          AND (LOWER(title) LIKE :subject_pattern OR level > 1)
        ORDER BY unit_number ASC, level ASC, display_order ASC;
    """)
    
    rows = db.execute(query, {
        "exam_type": norm_exam,
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

    for t_id, topic_data in topics_dict.items():
        p_id = topic_data.pop("parent_id", None)
        if p_id in units_dict:
            units_dict[p_id]["topics"].append(topic_data)

    sorted_units = sorted(list(units_dict.values()), key=lambda x: x["unit_number"])

    return {
        "exam_type": exam_type.upper(),
        "subject": subject_code.capitalize(),
        "units": sorted_units
    }


@router.get("/content/{content_id}", response_model=ContentPayloadResponse)
def get_content_payload(
    content_id: UUID4 = Path(..., description="Target database content row identifier uuid"),
    db: Session = Depends(get_db)
):
    query = text("""
        SELECT content, content_type
        FROM public.generated_content
        WHERE id = :content_id
        LIMIT 1;
    """)
    
    result = db.execute(query, {"content_id": str(content_id)}).fetchone()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="The active instructional textbook artifact could not be found."
        )
        
    return {
        "content": result.content,
        "content_type": result.content_type
    }


# ==========================================
# 3. ADMINISTRATIVE WORKFLOW MANAGEMENT CHANNELS
# ==========================================

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

@admin_router.get("/exams", response_model=List[ExamResponse])
def get_admin_exams(db: Session = Depends(get_db)):
    return db.query(models.Exam).all()

@admin_router.post("/exams", response_model=ExamResponse, status_code=status.HTTP_201_CREATED)
def create_admin_exam_track(payload: ExamCreate, db: Session = Depends(get_db)):
    # FIXED: Bound to code field directly to align with metadata patterns
    new_exam = models.Exam(
        name=payload.name.strip(),
        code=payload.exam_code.upper().strip()
    )
    db.add(new_exam)
    db.commit()
    db.refresh(new_exam)
    return ExamResponse(id=new_exam.id, name=new_exam.name, exam_code=new_exam.code)

@admin_router.get("/exam/subjects", response_model=List[ExamSubjectResponse])
def get_admin_exam_subjects(db: Session = Depends(get_db)):
    return db.query(models.ExamSubject).all()

@admin_router.post("/exam/subjects", response_model=ExamSubjectResponse, status_code=status.HTTP_201_CREATED)
def create_exam_subject_node(payload: ExamSubjectCreate, db: Session = Depends(get_db)):
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