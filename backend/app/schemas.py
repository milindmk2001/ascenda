from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Literal

# --- ORGANIZATION SCHEMAS ---

class OrganizationBase(BaseModel):
    name: str
    # Literal ensures ONLY these exact strings are accepted. 
    # This must match your frontend dropdown exactly.
    org_type: Literal["board", "competitive", "other"]

class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization (Incoming Data)"""
    pass

class Organization(OrganizationBase):
    """Schema for returning organization data (Outgoing Data)"""
    id: str

    # Pydantic v2 configuration to work with SQLAlchemy models
    model_config = ConfigDict(from_attributes=True)


# --- COURSE SCHEMAS (For future use) ---

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    organization_id: str

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: str

    model_config = ConfigDict(from_attributes=True)