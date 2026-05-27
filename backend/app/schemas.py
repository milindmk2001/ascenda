from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, List, Dict, Union
from uuid import UUID
from datetime import datetime


def uuid_to_str(value: Any) -> str:
    if isinstance(value, UUID):
        return str(value)
    return str(value) if value is not None else None


# ══════════════════════════════════════════════════════════════
# ORGANIZATION
# ══════════════════════════════════════════════════════════════

class OrganizationBase(BaseModel):
    name:     str
    org_type: str

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v):
        return uuid_to_str(v)


# ══════════════════════════════════════════════════════════════
# GRADE
# ══════════════════════════════════════════════════════════════

class GradeBase(BaseModel):
    level:  Optional[Union[int, str]] = None
    name:   Optional[str] = None
    org_id: Optional[UUID] = None

class GradeCreate(GradeBase):
    org_id: UUID

class Grade(GradeBase):
    id:     Any
    org_id: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "org_id", mode="before")
    @classmethod
    def transform_uuids(cls, v):
        return str(v) if v is not None else None

# ── GradeResponse: single definition used everywhere ─────────
class GradeResponse(BaseModel):
    """Used by curriculum.py /grades endpoint and any other grade listing."""
    id:    str
    name:  str
    level: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════
# SUBJECTS
# ══════════════════════════════════════════════════════════════

class RegularSubjectBase(BaseModel):
    name:         str
    subject_code: str
    grade_id:     UUID
    discipline:   Optional[str] = "General"
    video_url:    Optional[str] = None

class RegularSubject(RegularSubjectBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "grade_id", mode="before")
    @classmethod
    def transform_uuids(cls, v):
        return str(v) if v is not None else None

class AdminSubjectCreate(BaseModel):
    grade_id:     UUID
    name:         str
    subject_code: str
    discipline:   Optional[str] = "General"
    video_url:    Optional[str] = None


# ══════════════════════════════════════════════════════════════
# COURSES
# Single CourseCardResponse — used by curriculum.py resolve-hub
# ══════════════════════════════════════════════════════════════

class CourseCardResponse(BaseModel):
    """
    Response schema for homepage course cards.
    Fields match what public.v_course_hub returns.
    id = course UUID as string (not UUID type — safer for JSON serialization)
    title = course display name
    subject_name = subject label shown on card (Physics, Chemistry etc)
    subject_code = IITJEE_PHYSICS, CBSE-11-PHY etc
    discipline = Competitive Exam | Science | General
    track_type = competitive | board
    video_url = optional promotional video
    """
    id:           str
    title:        str
    subject_name: Optional[str] = None
    subject_code: str
    discipline:   str
    track_type:   Optional[str] = None
    video_url:    Optional[str] = None
    model_config  = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════
# EXAM ENGINE
# ══════════════════════════════════════════════════════════════

class ExamCreate(BaseModel):
    name: str
    code: str

class ExamResponse(ExamCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class ExamNestedResponse(BaseModel):
    id:   UUID
    name: str
    code: str
    model_config = ConfigDict(from_attributes=True)

class ExamSubjectCreate(BaseModel):
    exam_id:      UUID
    name:         str
    subject_code: str
    discipline:   Optional[str] = "Competitive Exam"
    video_url:    Optional[str] = ""

class ExamSubjectResponse(BaseModel):
    id:           UUID
    exam_id:      UUID
    name:         str
    subject_code: str
    discipline:   str
    video_url:    Optional[str] = ""
    exam:         Optional[ExamNestedResponse] = None
    model_config  = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════
# CURRICULUM TREE
# ══════════════════════════════════════════════════════════════

class CurriculumNodeBase(BaseModel):
    title:        str
    level:        Optional[int] = None
    content_type: Optional[str] = "text"
    subject_id:   UUID
    parent_id:    Optional[UUID] = None

class CurriculumNode(CurriculumNodeBase):
    id:       Any
    children: List['CurriculumNode'] = []
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "subject_id", "parent_id", mode="before")
    @classmethod
    def transform_uuids(cls, v):
        return str(v) if v is not None else None

class CurriculumNodeResponse(BaseModel):
    """Used by curriculum.py /subjects/{id}/tree endpoint."""
    id:            str
    title:         str
    parent_id:     Optional[str] = None
    is_leaf:       bool
    unit_number:   int
    display_order: int
    content_id:    Optional[str] = None
    content_type:  Optional[str] = None
    level:         Optional[int] = None
    model_config   = ConfigDict(from_attributes=True)

class RegularSubjectAreaCreate(BaseModel):
    title:          str
    sequence_order: int
    subject_id:     UUID

class RegularSubjectArea(RegularSubjectAreaCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class RegularChapterCreate(BaseModel):
    title:           str
    sequence_order:  int
    subject_area_id: UUID

class RegularChapter(RegularChapterCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════
# AI PROMPT ENGINE
# ══════════════════════════════════════════════════════════════

class PromptTemplateCreate(BaseModel):
    name:          str
    system_prompt: str
    user_template: str
    description:   Optional[str] = None

class PromptTemplateResponse(PromptTemplateCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)


# ══════════════════════════════════════════════════════════════
# AI TUTOR
# ══════════════════════════════════════════════════════════════

class AIQueryRequest(BaseModel):
    query:           str
    context_node_id: Optional[UUID] = None
    chat_history:    List[Dict[str, str]] = []


# ══════════════════════════════════════════════════════════════
# CONTENT STUDIO
# ══════════════════════════════════════════════════════════════

class ModularLessonBase(BaseModel):
    title:         str
    physics_params: Dict[str, Any] = {}
    latex_formula:  Optional[str] = None
    video_asset_id: Optional[str] = None

class ModularLessonCreate(ModularLessonBase):
    pass

class ModularLesson(ModularLessonBase):
    id:         UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
