from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, List
from uuid import UUID

# Helper function for UUID transformation
def uuid_to_str(value: Any) -> str:
    if isinstance(value, UUID): 
        return str(value)
    return str(value)

# --- Organization Schemas ---
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
    def transform_id(cls, v): 
        return uuid_to_str(v)

# --- Grade Schemas ---
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
    def transform_id(cls, v): 
        return uuid_to_str(v)

# --- Regular Curriculum Schemas ---
class RegularSubjectBase(BaseModel):
    name: str
    subject_code: str

class RegularSubjectCreate(RegularSubjectBase):
    grade_id: str

class RegularSubject(RegularSubjectBase):
    id: Any
    grade_id: Any
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "grade_id", mode="before")
    @classmethod
    def transform_id(cls, v): 
        return uuid_to_str(v)

class RegularSubjectAreaBase(BaseModel):
    name: str
    area_code: str

class RegularSubjectAreaCreate(RegularSubjectAreaBase):
    subject_id: str

class RegularSubjectArea(RegularSubjectAreaBase):
    id: Any
    subject_id: Any
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "subject_id", mode="before")
    @classmethod
    def transform_id(cls, v): 
        return uuid_to_str(v)

# --- Exam Curriculum Schemas ---
class ExamSubjectBase(BaseModel):
    name: str
    subject_code: str

class ExamSubjectCreate(ExamSubjectBase):
    organization_id: str

class ExamSubject(ExamSubjectBase):
    id: Any
    organization_id: Any
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "organization_id", mode="before")
    @classmethod
    def transform_id(cls, v): 
        return uuid_to_str(v)

class ExamSubjectAreaBase(BaseModel):
    name: str
    area_code: str

class ExamSubjectAreaCreate(ExamSubjectAreaBase):
    exam_subject_id: str

class ExamSubjectArea(ExamSubjectAreaBase):
    id: Any
    exam_subject_id: Any
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "exam_subject_id", mode="before")
    @classmethod
    def transform_id(cls, v): 
        return uuid_to_str(v)

# --- Course Schemas ---
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): 
        return uuid_to_str(v)