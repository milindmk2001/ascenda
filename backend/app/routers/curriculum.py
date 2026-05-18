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