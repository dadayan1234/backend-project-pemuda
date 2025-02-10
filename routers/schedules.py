from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Schedule
from schemas import ScheduleCreate

router = APIRouter(prefix="/schedules", tags=["Schedules"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_schedule(schedule: ScheduleCreate, db: Session = Depends(get_db)):
    new_schedule = Schedule(**schedule.dict())
    db.add(new_schedule)
    db.commit()
    return new_schedule

@router.get("/")
def get_schedules(db: Session = Depends(get_db)):
    return db.query(Schedule).all()
