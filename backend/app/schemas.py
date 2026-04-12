# Inside backend/apps/schemas.py

class OrganizationBase(BaseModel):
    name: str
    org_type: str 

    @field_validator("org_type", mode="before")
    @classmethod
    def validate_org_type(cls, value: Any) -> str:
        if not value:
            return "other"
            
        # Convert to lowercase to match our list exactly
        val_lower = str(value).lower().strip()
        allowed = ["board", "competitive", "other"]
        
        # If it's a known valid type, return the lowercase version
        if val_lower in allowed:
            return val_lower
            
        # If it's something weird like "IIT/JEE", map it to "competitive"
        # But only if it's NOT one of our three standard types
        return "competitive"