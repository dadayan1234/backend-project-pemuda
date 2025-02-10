from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Attendance
from schemas import AttendanceCreate

router = APIRouter(prefix="/attendance", tags=["Attendance"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_attendance(attendance: AttendanceCreate, db: Session = Depends(get_db)):
    new_attendance = Attendance(**attendance.dict())
    db.add(new_attendance)
    db.commit()
    return new_attendance

@router.get("/")
def get_attendances(db: Session = Depends(get_db)):
    return db.query(Attendance).all()
