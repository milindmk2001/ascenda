from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional, Literal, Any
from uuid import UUID

class OrganizationBase(BaseModel):
    name: str
    org_type: str  # We change this to str to prevent the crash

    @field_validator("org_type", mode="before")
    @classmethod
    def validate_org_type(cls, value: Any) -> str:
        # Define your strictly allowed types for the frontend
        allowed = ["board", "competitive", "other"]
        # If the DB value is something like "IIT/JEE", map it to "competitive"
        if value not in allowed:
            return "competitive"
        return value

class OrganizationCreate(OrganizationBase):
    # For NEW entries, you can still enforce the Literal if you want, 
    # but for now, let's keep it simple to get you running.
    pass

class Organization(OrganizationBase):
    id: str  # We will force this to be a string

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def transform_uuid(cls, value: Any) -> str:
        # If it's a UUID object from Postgres, turn it into a string
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