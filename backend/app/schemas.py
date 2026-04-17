from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, List, Dict # <--- Ensure Dict is here
from uuid import UUID

def uuid_to_str(value: Any) -> str:
    if isinstance(value, UUID): 
        return str(value)
    return str(value) if value is not None else None

# --- Organization ---
class OrganizationBase(BaseModel):
    name: str
    org_type: str 

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: Any 
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): return uuid_to_str(v)

# --- Grade ---
class GradeBase(BaseModel):
    level: Optional[str] = None
    name: Optional[str] = None
    org_id: Optional[UUID] = None

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: Any
    org_id: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "org_id", mode="before")
    @classmethod
    def transform_uuids(cls, v): 
        return uuid_to_str(v)

# --- Subjects ---
class SubjectBase(BaseModel):
    name: str
    subject_code: str
    discipline: Optional[str] = "Science"
    video_url: Optional[str] = None

class RegularSubjectCreate(SubjectBase):
    grade_id: UUID

class RegularSubject(SubjectBase):
    id: Any
    grade_id: Any
    video_url: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "grade_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)

# --- Subject Areas (FIXED: Added missing classes) ---
class SubjectAreaBase(BaseModel):
    name: str
    area_code: str

class RegularSubjectAreaCreate(SubjectAreaBase):
    subject_id: UUID

class RegularSubjectArea(SubjectAreaBase):
    id: Any
    subject_id: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "subject_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)

class ExamSubjectAreaCreate(SubjectAreaBase):
    exam_subject_id: UUID

class ExamSubjectArea(SubjectAreaBase):
    id: Any
    exam_subject_id: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "exam_subject_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)

# --- Studio & AI ---
class ModularLesson(BaseModel):
    id: Any
    title: str
    physics_params: dict[str, float]
    latex_formula: Optional[str] = None
    video_asset_id: Optional[str] = None
    created_at: Any

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "created_at", mode="before")
    @classmethod
    def transform_metadata(cls, v):
        return str(v) if v is not None else None
class ModularLessonCreate(BaseModel):
    title: str
    variables: dict[str, float] # Works natively in Python 3.9+
    formula: str
    videoAssetId: Optional[str]

class AIQueryRequest(BaseModel):
    subject_id: UUID
    user_query: str
    board: str
    grade: str