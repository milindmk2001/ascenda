import uuid
from sqlalchemy import Column, String, ForeignKey, TEXT
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

# --- Organization Model ---
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False) # e.g., "School", "Coaching", "Board"

# --- Grade Model ---
class Grade(Base):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String, nullable=True) # e.g., "10", "12"
    name = Column(String, nullable=True)  # e.g., "Grade 10"
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)

# --- Regular Curriculum Models ---
class RegularSubject(Base):
    __tablename__ = "regular_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Science")
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"))
    # video_url stores the embed link for the Udemy-style player
    video_url = Column(String, nullable=True) 

class RegularSubjectArea(Base):
    __tablename__ = "regular_subject_areas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    area_code = Column(String, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("regular_subjects.id"))

# --- Competitive Exam Models ---
class ExamSubject(Base):
    __tablename__ = "exam_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Competitive")
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))

class ExamSubjectArea(Base):
    __tablename__ = "exam_subject_areas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    area_code = Column(String, nullable=False)
    exam_subject_id = Column(UUID(as_uuid=True), ForeignKey("exam_subjects.id"))