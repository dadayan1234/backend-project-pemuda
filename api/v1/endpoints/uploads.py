from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime
import os
from core.security import verify_token
from core.database import get_db, admin_required
from core.utils.file_handler import FileHandler
from ..models.news import News, NewsPhoto
from ..models.events import Event, EventPhoto
from ..models.user import User
from ..models.finance import Finance

router = APIRouter()
file_handler = FileHandler()

async def save_multiple_images(
    entity_id: int,
    files: List[UploadFile],
    entity_type: str,
    db: Session
):
    """Helper function untuk menyimpan multiple gambar."""
    uploaded_urls = []
    today_date = datetime.now().strftime("%Y-%m-%d")  # Format YYYY-MM-DD

    for file in files:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Buat nama file berdasarkan timestamp
        timestamp = int(datetime.now().timestamp())
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"{timestamp}{file_extension}"

        # Simpan file ke dalam folder news/{YYYY-MM-DD}/ atau events/{YYYY-MM-DD}/
        file_url = await file_handler.save_file(file, f"{entity_type}/{today_date}", new_filename)

        # Simpan ke database
        if entity_type == "news":
            photo = NewsPhoto(news_id=entity_id, photo_url=file_url)
        elif entity_type == "events":
            photo = EventPhoto(event_id=entity_id, photo_url=file_url)
        else:
            raise HTTPException(status_code=400, detail="Invalid entity type")

        db.add(photo)
        uploaded_urls.append(file_url)

    db.commit()
    return uploaded_urls

@router.post("/news/{news_id}/photos")
@admin_required()
async def upload_news_photos(
    news_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload multiple images for a news item."""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    uploaded_urls = await save_multiple_images(news_id, files, "news", db)
    return {"uploaded_files": uploaded_urls}

@router.post("/events/{event_id}/photos")
@admin_required()
async def upload_event_photos(
    event_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload multiple images for an event."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    uploaded_urls = await save_multiple_images(event_id, files, "events", db)
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