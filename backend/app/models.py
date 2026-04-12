import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from .database import Base

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False) 

class Grade(Base):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # The database requires 'name'. We map it here.
    name = Column(String, nullable=True) 
    # 'level' is used for the display logic in your frontend
    level = Column(String, nullable=False)

class RegularSubject(Base):
    __tablename__ = "regular_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, unique=True)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"))

class ExamSubject(Base):
    __tablename__ = "exam_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, unique=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))