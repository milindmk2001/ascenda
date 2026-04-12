import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    # Note: Ensure your DB Enum includes 'board', 'competitive', 'other'
    org_type = Column(String, nullable=False) 

class Grade(Base):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String, nullable=False, unique=True) # e.g., "Class 10"

class RegularSubject(Base):
    __tablename__ = "regular_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, unique=True) # e.g., "BIO-10"
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"))

class ExamSubject(Base):
    __tablename__ = "exam_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, unique=True) # e.g., "JEE-PHY"
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))