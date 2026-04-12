from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, List
from uuid import UUID

def uuid_to_str(value: Any) -> str:
    if isinstance(value, UUID): return str(value)
    return str(value)

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

class GradeBase(BaseModel):
    level: str
    name: Optional[str] = None

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): return uuid_to_str(v)

class SubjectBase(BaseModel):
    name: str
    subject_code: str

class Subject(SubjectBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): return uuid_to_str(v)

class RegularSubjectCreate(SubjectBase):
    grade_id: str

class ExamSubjectCreate(SubjectBase):
    organization_id: str

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)