from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Event, EventPhoto
from schemas import EventCreate
import shutil
import os
from uuid import uuid4

router = APIRouter(prefix="/events", tags=["Events"])

UPLOAD_DIR = "uploads/"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    new_event = Event(**event.dict())
    db.add(new_event)
    db.commit()
    return new_event

@router.get("/")
def get_events(db: Session = Depends(get_db)):
    return db.query(Event).all()

@router.post("/{event_id}/upload-photo")
def upload_event_photo(event_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """ Mengunggah foto event dan menyimpan path-nya di database. """
    
    # Pastikan event ada di database
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return {"error": "Event not found"}

    # Generate nama unik untuk file
    file_extension = file.filename.split(".")[-1]
    file_name = f"{uuid4()}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, file_name)

    # Simpan file ke server
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Simpan path file di database
    new_photo = EventPhoto(event_id=event_id, photo_path=file_path)
    db.add(new_photo)
    db.commit()

    return {"message": "Photo uploaded successfully", "photo_url": file_path}
