from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Any, List, Dict, Union
from uuid import UUID

def uuid_to_str(value: Any) -> str:
    if isinstance(value, UUID): 
        return str(value)
    return str(value) if value is not None else None

# --- Organization ---
class OrganizationBase(BaseModel):
    name: str
    org_type: str 

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: Any 
    model_config = ConfigDict(from_attributes=True)
    @field_validator("id", mode="before")
    @classmethod
    def transform_id(cls, v): return uuid_to_str(v)

# --- Grade ---
class GradeBase(BaseModel):
    level: Optional[Union[int, str]] = None  # Flexible validation handling form integers and database strings
    name: Optional[str] = None
    org_id: Optional[UUID] = None

class GradeCreate(GradeBase):
    org_id: UUID  # Enforced on form submissions

class Grade(GradeBase):
    id: Any
    org_id: Optional[Any] = None
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "org_id", mode="before")
    @classmethod
    def transform_uuids(cls, v): 
        return uuid_to_str(v)

# --- Subjects ---
class RegularSubjectBase(BaseModel):
    name: str
    subject_code: str
    grade_id: UUID
    discipline: Optional[str] = "General"
    video_url: Optional[str] = ""

class RegularSubjectCreate(RegularSubjectBase):
    pass

class RegularSubject(RegularSubjectBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "grade_id", mode="before")
    @classmethod
    def transform_uuids(cls, v): 
        return uuid_to_str(v)

# --- Subject Areas (Units) ---
class RegularSubjectAreaBase(BaseModel):
    title: str
    sequence_order: int
    subject_id: UUID

class RegularSubjectAreaCreate(RegularSubjectAreaBase):
    pass

class RegularSubjectArea(RegularSubjectAreaBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "subject_id", mode="before")
    @classmethod
    def transform_uuids(cls, v): return uuid_to_str(v)

# --- Chapters ---
class RegularChapterBase(BaseModel):
    title: str
    sequence_order: int
    subject_area_id: UUID

class RegularChapterCreate(RegularChapterBase):
    pass

class RegularChapter(RegularChapterBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "subject_area_id", mode="before")
    @classmethod
    def transform_uuids(cls, v): return uuid_to_str(v)

# --- Prompt Templates ---
class PromptTemplateBase(BaseModel):
    subject_id: UUID
    model_name: str
    system_instruction: str

class PromptTemplateCreate(PromptTemplateBase):
    pass

class PromptTemplate(PromptTemplateBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "subject_id", mode="before")
    @classmethod
    def transform_uuids(cls, v): return uuid_to_str(v)

# --- AI Tutor & Studio ---
class ModularLessonBase(BaseModel):
    title: str
    physics_params: Dict[str, Any]
    latex_formula: str
    video_asset_id: Optional[str] = None

class ModularLesson(ModularLessonBase):
    id: Any
    created_at: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "created_at", mode="before")
    @classmethod
    def transform_metadata(cls, v):
        return str(v) if v is not None else None

class ModularLessonCreate(BaseModel):
    title: str
    variables: dict[str, float]
    formula: str
    videoAssetId: Optional[str] = None

class AIQueryRequest(BaseModel):
    subject_id: UUID
    user_query: str
    board: str
    grade: str

# --- Lesson Articles ---
class ArticleBase(BaseModel):
    title: str
    content_markdown: str
    subject_id: UUID

class ArticleCreate(ArticleBase):
    pass

class Article(ArticleBase):
    id: Any
    created_at: Any
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "subject_id", mode="before")
    @classmethod
    def transform_uuid(cls, v): return uuid_to_str(v)

# --- W3Schools Style Navigation Tree ---
class CurriculumNodeBase(BaseModel):
    title: str
    level: Optional[int] = None
    content_type: Optional[str] = "text"
    subject_id: UUID
    parent_id: Optional[UUID] = None

class CurriculumNode(CurriculumNodeBase):
    id: Any
    children: List['CurriculumNode'] = []
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator("id", "subject_id", "parent_id", mode="before")
    @classmethod
    def transform_uuids(cls, v):
        return str(v) if v is not None else None

# --- Explicit Form Ingestion Data Mappings ---
class ExamCreate(BaseModel):
    name: str
    code: str

class ExamResponse(ExamCreate):
    id: UUID
    model_config = ConfigDict(from_attributes=True)

class AdminGradeCreate(BaseModel):
    org_id: UUID
    level: Union[int, str]
    name: Optional[str] = None

class AdminSubjectCreate(BaseModel):
    grade_id: UUID
    name: str
    subject_code: str
    discipline: Optional[str] = "General"
    video_url: Optional[str] = ""