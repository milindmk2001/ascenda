from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, List
from uuid import UUID

# --- HELPER FOR UUID TO STRING ---
def uuid_to_str(value: Any) -> str:
    if isinstance(value, UUID):
        return str(value)
    return str(value)

# --- ORGANIZATION SCHEMAS ---
class OrganizationBase(BaseModel):
    name: str
    org_type: str 

    @field_validator("org_type", mode="before")
    @classmethod
    def validate_org_type(cls, value: Any) -> str:
        if not value: return "other"
        val_lower = str(value).lower().strip()
        allowed = ["board", "competitive", "other"]
        return val_lower if val_lower in allowed else "competitive"

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: Any 
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): return uuid_to_str(v)

# --- GRADE SCHEMAS ---
class GradeBase(BaseModel):
    level: str

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): return uuid_to_str(v)

# --- SUBJECT SCHEMAS ---
class SubjectBase(BaseModel):
    name: str
    subject_code: str

class RegularSubjectCreate(SubjectBase):
    grade_id: str

class ExamSubjectCreate(SubjectBase):
    organization_id: str

class Subject(SubjectBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): return uuid_to_str(v)