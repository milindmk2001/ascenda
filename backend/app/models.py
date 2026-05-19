import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TEXT, DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

# ==========================================\n# 1. ORGANIZATION & GRADE LAYER\n# ==========================================\n
class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    org_type = Column(String, nullable=False)
    
    grades = relationship("Grade", back_populates=\"organization\")


class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String, nullable=True)
    name = Column(String, nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    
    organization = relationship("Organization", back_populates="grades")
    subjects = relationship("RegularSubject", back_populates="grade")


# ==========================================\n# 2. K-12 STANDARDIZED CURRICULUM LAYER\n# ==========================================\n
class RegularSubject(Base):
    __tablename__ = "subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Science")
    grade_id = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    video_url = Column(String, default="")

    grade = relationship("Grade", back_populates="subjects")


# ==========================================\n# 3. COMPETITIVE TRACKS / EXAMS ENGINE\n# ==========================================\n
class Exam(Base):
    __tablename__ = "exams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    exam_code = Column(String, unique=True, nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)

    subjects = relationship("ExamSubject", back_populates="exam", cascade="all, delete-orphan")


class ExamSubject(Base):
    __tablename__ = "exam_subjects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id = Column(UUID(as_uuid=True), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline = Column(String, default="Competitive Exam")
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))

    exam = relationship("Exam", back_populates="subjects")


# ==========================================\n# 4. CONTENT STUDIO & AI TUTOR RUNTIME LAYER\n# ==========================================\n
class ModularLesson(Base):
    __tablename__ = "modular_lessons"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    physics_params = Column(JSONB, default={})
    latex_formula = Column(String)
    video_asset_id = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# ==========================================\n# 5. ASCENDAPRO CURRICULUM NAVIGATION LAYERS\n# ==========================================\n
class CurriculumTreeView(Base):
    __tablename__ = "curriculum_tree"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), nullable=True)
    title = Column(String, nullable=False)
    level = Column(Integer, nullable=False) 
    content_type = Column(String, nullable=False) 
    exam_type = Column(String, default="IITJEE")
    unit_number = Column(Integer, nullable=True)
    is_leaf = Column(Boolean, default=False)
    content_id = Column(UUID(as_uuid=True), nullable=True)
    display_order = Column(Integer, default=0)


class GeneratedContentPayload(Base):
    __tablename__ = "generated_content"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(TEXT, nullable=False)
    content_type = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    unit = Column(String, nullable=False)


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    description = Column(TEXT, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=text("now()"))
    organization_id = Column(UUID(as_uuid=True), nullable=True)