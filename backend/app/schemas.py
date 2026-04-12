from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Literal, Any
from uuid import UUID

# --- ORGANIZATION SCHEMAS ---

class OrganizationBase(BaseModel):
    name: str
    org_type: str 

    @field_validator("org_type", mode="before")
    @classmethod
    def validate_org_type(cls, value: Any) -> str:
        if not value:
            return "other"
            
        val_lower = str(value).lower().strip()
        allowed = ["board", "competitive", "other"]
        
        if val_lower in allowed:
            return val_lower
            
        return "competitive"

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    id: str 

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def transform_uuid(cls, value: Any) -> str:
        if isinstance(value, UUID):
            return str(value)
        return str(value)

# --- COURSE SCHEMAS ---

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    organization_id: str

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "organization_id", mode="before")
    @classmethod
    def transform_uuids(cls, value: Any) -> str:
        return str(value)