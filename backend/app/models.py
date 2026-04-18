import uuid
from sqlalchemy import Column, String, ForeignKey, TEXT, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .database import Base

# --- Organization & Grade ---
class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False)

class Grade(Base):
    __tablename__ = "grades"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String, nullable=True)
    name = Column(String, nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)

# --- Curriculum ---
class RegularSubject(Base):
    __tablename__ = "regular_subjects"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Science")
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"))
    video_url = Column(String, nullable=True) 

class RegularSubjectArea(Base):
    __tablename__ = "regular_subject_areas"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    area_code = Column(String, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("regular_subjects.id"))

# --- NEW: AI Tutor & Content Studio ---
class PromptTemplate(Base):
    __tablename__ = "prompt_templates"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("regular_subjects.id"), nullable=False)
    system_instruction = Column(TEXT, nullable=False)
    model_name = Column(String, default="gemini-1.5-flash")
    temperature = Column(Float, default=0.7)

class ModularLesson(Base):
    __tablename__ = "modular_lessons"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    physics_params = Column(JSONB, nullable=False) # Stores {u, a, t, s}
    latex_formula = Column(String)
    video_asset_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LessonArticle(Base):
    __tablename__ = "lesson_articles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String)
    content = Column(TEXT) # Stores the W3Schools-style Markdown/HTML
    subject_id = Column(UUID(as_uuid=True), ForeignKey("regular_subjects.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Add this to models.py
class CurriculumTree(Base):
    __tablename__ = "curriculum_tree"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("regular_subjects.id"), nullable=False)
    course_id = Column(UUID(as_uuid=True), nullable=True) # Optional link to a specific course
    parent_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_tree.id"), nullable=True)
    title = Column(TEXT, nullable=False)
    level = Column(Integer, nullable=True) # 0 for Chapter, 1 for Topic, 2 for Subtopic
    content_type = Column(TEXT, default="text")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    subject = relationship("RegularSubject", back_populates="curriculum_nodes")
    children = relationship("CurriculumTree", backref=remote(parent_id))