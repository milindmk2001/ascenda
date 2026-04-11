from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from .database import Base
import uuid

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    org_type = Column(String, nullable=False) # board, IIT/JEE, etc.
    icon_url = Column(String, nullable=True)

class Grade(Base):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    name = Column(String, nullable=False)

class RegularSubject(Base):
    __tablename__ = "regular_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"))
    name = Column(String, nullable=False)
    subject_code = Column(String, unique=True, nullable=False)
    discipline = Column(String, nullable=True)

class ExamSubject(Base):
    __tablename__ = "exam_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    name = Column(String, nullable=False)
    subject_code = Column(String, unique=True, nullable=False)
    discipline = Column(String, nullable=True)