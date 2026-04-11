from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from .. import models, schemas, database

router = APIRouter(
    prefix="/api/admin/organizations",
    tags=["Admin: Organizations"]
)

@router.get("/", response_model=List[schemas.Organization])
def list_orgs(db: Session = Depends(database.get_db)):
    return db.query(models.Organization).all()

@router.post("/", status_code=201, response_model=schemas.Organization)
def create_org(org: schemas.OrganizationCreate, db: Session = Depends(database.get_db)):
    db_org = models.Organization(**org.model_dump())
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org

@router.delete("/{org_id}")
def delete_org(org_id: UUID, db: Session = Depends(database.get_db)):
    db_org = db.query(models.Organization).filter(models.Organization.id == org_id).first()
    if not db_org:
        raise HTTPException(status_code=404, detail="Organization not found")
    db.delete(db_org)
    db.commit()
    return {"message": "Deleted successfully"}