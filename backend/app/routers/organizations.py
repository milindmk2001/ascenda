from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

# Use a consistent trailing slash strategy
router = APIRouter(prefix="/api/admin/organizations", tags=["organizations"])

@router.get("/", response_model=List[schemas.Organization])
@router.get("", response_model=List[schemas.Organization]) # Support both with/without slash
def get_organizations(db: Session = Depends(get_db)):
    """
    Explicitly query only the columns needed to avoid 
    serialization issues with complex relationships.
    """
    orgs = db.query(models.Organization).all()
    
    # Debug: This will show in your Railway logs
    print(f"DEBUG: Found {len(orgs)} organizations in DB")
    
    return orgs