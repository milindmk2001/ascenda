from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, List
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
    level: str
    name: Optional[str] = None
    org_id: Optional[UUID] = None # Added to match DB

class GradeCreate(GradeBase):
    org_id: Optional[UUID] = None

class Grade(GradeBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "org_id", mode="before")
    @classmethod
    def transform_uuids(cls, v): 
        return uuid_to_str(v)

# --- Subjects ---
class SubjectBase(BaseModel):
    name: str
    subject_code: str
    discipline: Optional[str] = "Science" # Added to match curriculum logic

class RegularSubjectCreate(SubjectBase):
    grade_id: UUID

class RegularSubject(SubjectBase):
    id: Any
    grade_id: Any
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", "grade_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)

class ExamSubjectCreate(SubjectBase):
    organization_id: UUID

class ExamSubject(SubjectBase):
    id: Any
    organization_id: Any
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", "organization_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)

# --- Subject Areas ---
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
    name: str
    area_code: str
    exam_subject_id: UUID

class ExamSubjectArea(SubjectAreaBase):
    id: Any
    exam_subject_id: Any
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", "exam_subject_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)