from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

# --- Organization ---
class OrganizationBase(BaseModel):
    name: str
    org_type: str  # 'board' (CBSE) or 'competitive' (JEE)
    icon_url: Optional[str] = None

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: UUID
    class Config:
        from_attributes = True

# --- Grade (Class 1-12) ---
class GradeBase(BaseModel):
    name: str
    org_id: UUID

class GradeCreate(GradeBase):
    pass

class Grade(GradeBase):
    id: UUID
    class Config:
        from_attributes = True

# --- Subjects (Regular & Exam) ---
class SubjectBase(BaseModel):
    name: str
    subject_code: str
    discipline: Optional[str] = None  # e.g., 'Science', 'Arts'

class RegularSubjectCreate(SubjectBase):
    grade_id: UUID

class ExamSubjectCreate(SubjectBase):
    org_id: UUID

class Subject(SubjectBase):
    id: UUID
    class Config:
        from_attributes = True

# --- Course (The Final Product) ---
class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    rigor_level: str  # 'Foundation', 'Advanced', 'Board'
    is_featured: bool = False

class CourseCreate(CourseBase):
    # A course can belong to either a regular grade subject or a competitive exam subject
    regular_subject_id: Optional[UUID] = None
    exam_subject_id: Optional[UUID] = None

class Course(CourseBase):
    id: UUID
    class Config:
        from_attributes = True