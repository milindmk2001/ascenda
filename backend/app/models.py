import uuid
from sqlalchemy import Column, String, ForeignKey, TEXT, Float, DateTime, func, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB  # JSONB must come from here
from sqlalchemy.orm import relationship, backref
from app.database import Base

# --- Organization & Grade ---
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False)
    grades = relationship("Grade", back_populates="organization")

class Grade(Base):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String, nullable=True)
    name = Column(String, nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    organization = relationship("Organization", back_populates="grades")
    subjects = relationship("RegularSubject", back_populates="grade")

# --- Curriculum ---
class RegularSubject(Base):
    __tablename__ = "regular_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Science")
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"))
    video_url = Column(String, nullable=True) 
    
    grade = relationship("Grade", back_populates="subjects")
    curriculum_nodes = relationship("CurriculumTree", back_populates="subject")

# --- New: Curriculum Tree (For the W3Schools Sidebar) ---
class CurriculumTree(Base):
    __tablename__ = "curriculum_tree"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("regular_subjects.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_tree.id"), nullable=True)
    title = Column(TEXT, nullable=False)
    level = Column(Integer, nullable=True) 
    content_type = Column(TEXT, default="text")

    # This allows automatic nesting in the API response
    children = relationship(
        "CurriculumTree",
        backref=backref('parent', remote_side=[id]),
        lazy="joined"
    )

# --- AI Tutor & Content Studio ---
class ModularLesson(Base):
    __tablename__ = "modular_lessons"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    physics_params = Column(JSONB, nullable=False) # This line will work now
    latex_formula = Column(String)
    video_asset_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())