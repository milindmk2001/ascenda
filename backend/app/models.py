import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TEXT, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship, backref
from app.database import Base

# ==========================================
# 1. ORGANIZATION & GRADE LAYER
# ==========================================

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False)
    
    # Relationships
    grades = relationship("Grade", back_populates="organization")


class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String, nullable=True)
    name = Column(String, nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="grades")
    subjects = relationship("RegularSubject", back_populates="grade")


# ==========================================
# 2. K-12 STANDARDIZED CURRICULUM LAYER
# ==========================================

class RegularSubject(Base):
    __tablename__ = "regular_subjects"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Science")
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"))
    video_url = Column(String, nullable=True) 
    
    # Relationships
    grade = relationship("Grade", back_populates="subjects")


class CurriculumTree(Base):
    __tablename__ = "curriculum_tree"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("regular_subjects.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_tree.id"), nullable=True)
    title = Column(TEXT, nullable=False)
    level = Column(Integer, nullable=True) 
    content_type = Column(TEXT, default="text")

    # 1. Link to the Subject (Matches regular_subjects)
    subject = relationship("RegularSubject", backref="tree_nodes")

    # 2. Self-referential hierarchy mapping for units, topics, and chapters
    children = relationship(
        "CurriculumTree",
        backref=backref('parent', remote_side=[id]),
        lazy="joined"
    )


# ==========================================
# 3. COMPETITIVE EXAM TRACKS LAYER
# ==========================================

class Exam(Base):
    __tablename__ = "exams"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, unique=True, nullable=False)
    
    # Synced with Supabase layout tracking board structures (e.g., CBSE, ICSE context constraints)
    organisation_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)

    # Fixed bidirectional relationship back-population link
    subjects = relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")


class ExamSubject(Base):
    __tablename__ = "exam_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Competitive Exam")
    
    # Standardized on DateTime with timezone tracking to resolve NameError crashes safely
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    # Relationship back to the parent Exam blueprint core
    exam = relationship("Exam", back_populates="subjects")


# ==========================================
# 4. CONTENT STUDIO & AI TUTOR RUNTIME LAYER
# ==========================================

class ModularLesson(Base):
    __tablename__ = "modular_lessons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    physics_params = Column(JSONB, nullable=False)
    latex_formula = Column(String)
    video_asset_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ==========================================
# 5. ASCENDAPRO CURRICULUM TREE & CONTENT SCHEMA
# ==========================================

class CurriculumTree(Base):
    __tablename__ = "curriculum_tree"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String, nullable=False)
    level = Column(Integer, nullable=False) # 1=unit, 2=topic, 3=leaf
    content_type = Column(String, nullable=False) # unit | topic | concept | etc.
    exam_type = Column(String, default="IITJEE")
    unit_number = Column(Integer, nullable=True)
    is_leaf = Column(Boolean, default=False)
    content_id = Column(UUID(as_uuid=True), nullable=True)
    display_order = Column(Integer, default=0)


class GeneratedContent(Base):
    __tablename__ = "generated_content"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(TEXT, nullable=False)
    content_type = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    unit = Column(String, nullable=False)