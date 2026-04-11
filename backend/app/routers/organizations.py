from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db

router = APIRouter(
    prefix="/api/admin/organizations",
    tags=["organizations"]
)

# 1. GET ALL ORGANIZATIONS
@router.get("/", response_model=List[schemas.Organization])
def get_organizations(db: Session = Depends(get_db)):
    return db.query(models.Organization).all()

# 2. CREATE NEW ORGANIZATION
@router.post("/", response_model=schemas.Organization, status_code=status.HTTP_201_CREATED)
def create_organization(org: schemas.OrganizationCreate, db: Session = Depends(get_db)):
    # The 'org' object follows the OrganizationCreate schema
    new_org = models.Organization(
        name=org.name, 
        org_type=org.org_type
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return new_org

# 3. UPDATE EXISTING ORGANIZATION (Fixes the 405 Error)
@router.put("/{org_id}", response_model=schemas.Organization)
def update_organization(
    org_id: str, 
    org_update: schemas.OrganizationCreate, 
    db: Session = Depends(get_db)
):
    db_org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    
    if not db_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Organization not found"
        )
    
    # Update the fields with the new data from the frontend
    db_org.name = org_update.name
    db_org.org_type = org_update.org_type
    
    db.commit()
    db.refresh(db_org)
    return db_org

# 4. DELETE ORGANIZATION
@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_organization(org_id: str, db: Session = Depends(get_db)):
    db_org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    
    if not db_org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Organization not found"
        )
    
    db.delete(db_org)
    db.commit()
    return None