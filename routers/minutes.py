from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Minutes
from schemas import MinutesCreate

router = APIRouter(prefix="/minutes", tags=["Minutes"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_minutes(minutes: MinutesCreate, db: Session = Depends(get_db)):
    new_minutes = Minutes(**minutes.dict())
    db.add(new_minutes)
    db.commit()
    return new_minutes

@router.get("/")
def get_minutes(db: Session = Depends(get_db)):
    return db.query(Minutes).all()
