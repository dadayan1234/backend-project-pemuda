from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Organization
from schemas import OrganizationCreate

router = APIRouter(prefix="/organization", tags=["Organization"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_organization(org: OrganizationCreate, db: Session = Depends(get_db)):
    new_org = Organization(**org.dict())
    db.add(new_org)
    db.commit()
    return new_org

@router.get("/")
def get_organizations(db: Session = Depends(get_db)):
    return db.query(Organization).all()
