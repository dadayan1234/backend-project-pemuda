from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Finance
from schemas import FinanceCreate

router = APIRouter(prefix="/finance", tags=["Finance"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_finance(finance: FinanceCreate, db: Session = Depends(get_db)):
    new_finance = Finance(**finance.dict())
    db.add(new_finance)
    db.commit()
    return new_finance

@router.get("/")
def get_finances(db: Session = Depends(get_db)):
    return db.query(Finance).all()
