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
    video_url: Optional[str] = None # Added for video player

class RegularSubjectCreate(SubjectBase):
    grade_id: UUID

class RegularSubject(SubjectBase):
    id: Any
    grade_id: Any
    video_url: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "grade_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)