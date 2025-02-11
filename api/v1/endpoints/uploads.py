from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from core.security import verify_token
from core.database import get_db, admin_required
from core.utils.file_handler import FileHandler
from ..models.events import Event, EventPhoto
from ..models.finance import Finance
# from ..models.news import News
from ..models.user import User

router = APIRouter()
file_handler = FileHandler()

@router.post("/events/{event_id}/photos")
@admin_required()
async def upload_event_photos(
    event_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
        
    uploaded_urls = []
    for file in files:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        file_url = await file_handler.save_file(file, f"events/{event_id}")
        photo = EventPhoto(event_id=event_id, photo_url=file_url)
        db.add(photo)
        uploaded_urls.append(file_url)
        
    db.commit()
    return {"uploaded_files": uploaded_urls}

@router.post("/finances/{finance_id}/document")
@admin_required()
async def upload_finance_document(
    finance_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    finance = db.query(Finance).filter(Finance.id == finance_id).first()
    if not finance:
        raise HTTPException(status_code=404, detail="Finance record not found")
        
    file_url = await file_handler.save_file(file, f"finances/{finance_id}")
    finance.document_url = file_url
    db.commit()
    
    return {"file_url": file_url}