from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, List, Literal, Any
from uuid import UUID

# --- ORGANIZATION SCHEMAS ---

class OrganizationBase(BaseModel):
    name: str
    # We keep this strict for NEW entries, but we'll add a validator 
    # below to handle existing "dirty" data in your database.
    org_type: Literal["board", "competitive", "other"]

    @field_validator("org_type", mode="before")
    @classmethod
    def validate_org_type(cls, value: Any) -> str:
        # If the DB has "IIT/JEE" or something else, map it to "competitive" 
        # so the application doesn't crash.
        allowed = ["board", "competitive", "other"]
        if value not in allowed:
            return "competitive" 
        return value

class OrganizationCreate(OrganizationBase):
    pass

class Organization(OrganizationBase):
    # Change id type to Any or UUID to stop the "Input should be a valid string" error
    id: Any 

    model_config = ConfigDict(from_attributes=True)

    # Convert UUID to string automatically for the frontend
    @field_validator("id", mode="before")
    @classmethod
    def transform_uuid(cls, value: Any) -> str:
        if isinstance(value, UUID):
            return str(value)
        return value

# --- COURSE SCHEMAS ---

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    organization_id: Any

class CourseCreate(CourseBase):
    pass

class Course(CourseBase):
    id: Any
    model_config = ConfigDict(from_attributes=True)