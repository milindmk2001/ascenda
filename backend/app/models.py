import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, TEXT, DateTime, func, text, Float, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base


# ══════════════════════════════════════════════════════════════
# 1. ORGANIZATION & GRADE LAYER
# ══════════════════════════════════════════════════════════════

class Organization(Base):
    __tablename__ = "organizations"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name     = Column(String, nullable=False)
    org_type = Column(String, nullable=False)

    grades = relationship("Grade", back_populates="organization")


class Grade(Base):
    __tablename__ = "grades"

    id     = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level  = Column(String, nullable=True)
    name   = Column(String, nullable=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)

    organization = relationship("Organization", back_populates="grades")
    subjects     = relationship("RegularSubject", back_populates="grade")


# ══════════════════════════════════════════════════════════════
# 2. K-12 BOARD CURRICULUM LAYER
# ══════════════════════════════════════════════════════════════

class RegularSubject(Base):
    __tablename__ = "regular_subjects"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name         = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline   = Column(String, default="Science")
    grade_id     = Column(UUID(as_uuid=True), ForeignKey("grades.id"), nullable=True)
    video_url    = Column(String, default="")

    grade   = relationship("Grade", back_populates="subjects")
    courses = relationship("Course", back_populates="regular_subject")


# ══════════════════════════════════════════════════════════════
# 3. COMPETITIVE EXAM LAYER
# ══════════════════════════════════════════════════════════════

class Exam(Base):
    __tablename__ = "exams"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String, nullable=False)
    exam_code       = Column(String, unique=True, nullable=False)
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True
    )

    subjects = relationship(
        "ExamSubject", back_populates="exam",
        cascade="all, delete-orphan"
    )


class ExamSubject(Base):
    __tablename__ = "exam_subjects"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_id      = Column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False
    )
    name         = Column(String, nullable=False)
    subject_code = Column(String, nullable=False)
    discipline   = Column(String, default="Competitive Exam")
    created_at   = Column(DateTime(timezone=True), server_default=text("now()"))

    exam    = relationship("Exam", back_populates="subjects")
    courses = relationship("Course", back_populates="exam_subject")


# ══════════════════════════════════════════════════════════════
# 4. COURSES
# ══════════════════════════════════════════════════════════════

class Course(Base):
    __tablename__  = "courses"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title              = Column(String, nullable=False)
    description        = Column(TEXT, nullable=True)
    rigor_level        = Column(String, nullable=True)
    is_featured        = Column(Boolean, default=False)
    thumbnail_url      = Column(String, nullable=True)
    instructor_id      = Column(UUID(as_uuid=True), nullable=True)
    created_at         = Column(DateTime(timezone=True), server_default=text("now()"))

    regular_subject_id = Column(
        UUID(as_uuid=True), ForeignKey("regular_subjects.id"), nullable=True
    )
    exam_subject_id    = Column(
        UUID(as_uuid=True), ForeignKey("exam_subjects.id"), nullable=True
    )

    regular_subject = relationship("RegularSubject", back_populates="courses")
    exam_subject    = relationship("ExamSubject",    back_populates="courses")


# ══════════════════════════════════════════════════════════════
# 5. CURRICULUM TREE
# All columns present in Supabase including new ones
# ══════════════════════════════════════════════════════════════

class CurriculumTreeView(Base):
    __tablename__  = "curriculum_tree"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # ── tree structure ────────────────────────────────────────
    parent_id          = Column(UUID(as_uuid=True), nullable=True)
    title              = Column(String, nullable=False)
    level              = Column(Integer, nullable=False)
    content_type       = Column(String, nullable=False)
    is_leaf            = Column(Boolean, default=False)
    display_order      = Column(Integer, default=0)
    # ── content ───────────────────────────────────────────────
    content_id         = Column(UUID(as_uuid=True), nullable=True)
    # ── exam metadata ─────────────────────────────────────────
    exam_type          = Column(String, nullable=True)
    unit_number        = Column(Integer, nullable=True)
    # ── foreign keys to other tables ─────────────────────────
    subject_id         = Column(UUID(as_uuid=True), nullable=True)   # → exam_subjects.id
    course_id          = Column(UUID(as_uuid=True), nullable=True)   # → courses.id
    # ── AI engine ─────────────────────────────────────────────
    prompt_template_id = Column(UUID(as_uuid=True), nullable=True)   # → prompt_templates.id
    # ── timestamps ────────────────────────────────────────────
    created_at         = Column(DateTime(timezone=True), server_default=text("now()"))


# ══════════════════════════════════════════════════════════════
# 6. GENERATED CONTENT & AI TABLES
# ══════════════════════════════════════════════════════════════

class GeneratedContentPayload(Base):
    __tablename__  = "generated_content"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    unit                = Column(String, nullable=False)
    subject             = Column(String, nullable=False)
    exam_type           = Column(String, nullable=False)
    topic               = Column(String, nullable=False)
    content_type        = Column(String, nullable=False)
    content             = Column(TEXT,   nullable=False)
    difficulty          = Column(String, nullable=True)
    source_file         = Column(String, nullable=True)
    generated_by        = Column(String, nullable=True)
    curriculum_chunk_id = Column(UUID(as_uuid=True), nullable=True)
    created_at          = Column(DateTime(timezone=True), server_default=text("now()"))


class PromptTemplate(Base):
    __tablename__  = "prompt_templates"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String, nullable=False)
    exam_subject_id = Column(UUID(as_uuid=True), nullable=True)
    content_type    = Column(String, nullable=False)
    template_text   = Column(TEXT, nullable=False)
    system_prompt   = Column(TEXT, nullable=True)
    version         = Column(Integer, default=1)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=text("now()"))


class PromptParameter(Base):
    __tablename__  = "prompt_parameters"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_tree_id   = Column(UUID(as_uuid=True), nullable=True)
    prompt_template_id   = Column(UUID(as_uuid=True), nullable=True)
    topic                = Column(String, nullable=True)
    unit                 = Column(String, nullable=True)
    exam_type            = Column(String, nullable=True)
    subject              = Column(String, nullable=True)
    difficulty           = Column(String, nullable=True)
    weightage            = Column(String, nullable=True)
    key_formulae         = Column(ARRAY(String), nullable=True)
    common_mistakes      = Column(ARRAY(String), nullable=True)
    prerequisites        = Column(ARRAY(String), nullable=True)
    top_k_theory         = Column(Integer, default=3)
    top_k_examples       = Column(Integer, default=3)
    top_k_questions      = Column(Integer, default=4)
    similarity_threshold = Column(Float, default=0.25)
    created_at           = Column(DateTime(timezone=True), server_default=text("now()"))


class Explanation(Base):
    __tablename__  = "explanations"
    __table_args__ = {"schema": "public", "extend_existing": True}

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    curriculum_tree_id  = Column(UUID(as_uuid=True), nullable=True)
    prompt_template_id  = Column(UUID(as_uuid=True), nullable=True)
    prompt_parameter_id = Column(UUID(as_uuid=True), nullable=True)
    explanation_text    = Column(TEXT, nullable=True)
    explanation_json    = Column(JSONB, nullable=True)
    generated_by        = Column(String, default="gemini-2.0-flash")
    generation_tokens   = Column(Integer, nullable=True)
    is_cached           = Column(Boolean, default=True)
    cache_version       = Column(Integer, default=1)
    created_at          = Column(DateTime(timezone=True), server_default=text("now()"))


# ══════════════════════════════════════════════════════════════
# 7. CONTENT STUDIO
# ══════════════════════════════════════════════════════════════

class ModularLesson(Base):
    __tablename__ = "modular_lessons"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title          = Column(String, nullable=False)
    physics_params = Column(JSONB, default={})
    latex_formula  = Column(String)
    video_asset_id = Column(String)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

class VisualLessonCache(Base):
    __tablename__ = "visual_lesson_cache"

    lesson_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    curriculum_node_id = Column(UUID(as_uuid=True), ForeignKey("curriculum_tree.id"), nullable=False, index=True)
    source_chunk_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=True)
    grade = Column(String(50), nullable=True)
    subject = Column(String(100), nullable=True)
    book = Column(String(250), nullable=True)
    chapter = Column(String(250), nullable=True)
    topic = Column(String(250), nullable=True)
    concept = Column(String(250), nullable=True)
    lesson_json = Column(JSONB, nullable=False)
    schema_version = Column(String(20), default="1.0")
    prompt_version = Column(String(20), nullable=True)
    model_used = Column(String(100), nullable=True)
    generation_status = Column(String(50), default="completed")
    validation_status = Column(String(50), default="valid")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
