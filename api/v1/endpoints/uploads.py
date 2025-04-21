from fastapi import APIRouter, Request, UploadFile, File, Depends, HTTPException
from typing import List
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
from core.security import verify_token
from core.database import get_db, admin_required
from core.utils.file_handler import FileHandler
from ..models.news import News, NewsPhoto
from ..models.events import Event, EventPhoto
from ..models.user import Member, User
from ..models.finance import Finance

router = APIRouter()

def get_file_handler():
    return file_handler
file_handler = FileHandler()

async def save_multiple_images(entity_id: int, files: List[UploadFile], entity_type: str, db: Session):
    """Helper function untuk menyimpan multiple gambar."""
    uploaded_urls = []
    today_date = datetime.now().strftime("%Y-%m-%d")

    for idx, file in enumerate(files):
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        timestamp = int(datetime.now().timestamp() * 1000)  
        file_extension = os.path.splitext(file.filename)[1]
        new_filename = f"{timestamp}_{idx}{file_extension}"
        
        file_url = await file_handler.save_file(file, f"{entity_type}/{today_date}", new_filename)
        file_url = file_url.replace("\\", "/")

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

async def replace_file(
    old_file_url: str,
    file: UploadFile,
    category: str,
    filename_prefix: str,
    db_model_obj,
    db_field_name: str,
    db: Session
) -> str:
    # Hapus file lama dengan toleransi error
    if old_file_url:
        file_handler.delete_image(old_file_url)

    # Generate filename
    timestamp = int(datetime.now().timestamp() * 1000)
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"{filename_prefix}_{timestamp}{file_extension}"

    # Save file
    today = datetime.now().strftime("%Y-%m-%d")
    file_url = await file_handler.save_file(file, f"{category}/{today}", filename)
    file_url = file_url.replace("\\", "/")

    # Update field di DB model
    setattr(db_model_obj, db_field_name, file_url)
    db.commit()

    return file_url


@router.post("/news/{news_id}/photos", tags=["Uploads - News"])
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
        raise HTTPException(status_code=200, detail="News not found")

    uploaded_urls = await save_multiple_images(news_id, files, "news", db)
    return {"uploaded_files": uploaded_urls}

@router.put("/news/photos/{photo_id}", tags=["Uploads - News"])
@admin_required()
async def edit_news_photo(
    photo_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    photo = db.query(NewsPhoto).filter(NewsPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=200, detail="Photo not found")

    file_url = await replace_file(
        old_file_url=photo.photo_url,
        file=file,
        category="news",
        filename_prefix=f"news_photo_{photo_id}",
        db_model_obj=photo,
        db_field_name="photo_url",
        db=db
    )

    return {"updated_file": file_url}


@router.delete("/news/photos/{photo_id}", tags=["Uploads - News"])
@admin_required()
async def delete_news_photo(
    photo_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a news photo."""
    photo = db.query(NewsPhoto).filter(NewsPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=200, detail="Photo not found")

    # Hapus file dari sistem
    file_handler.delete_image(photo.photo_url)

    # Hapus dari database
    db.delete(photo)
    db.commit()
    return {"message": "Photo deleted successfully"}

@router.post("/events/{event_id}/photos", tags=["Uploads - Events"])
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
        raise HTTPException(status_code=200, detail="Event not found")

    uploaded_urls = await save_multiple_images(event_id, files, "events", db)
    return {"uploaded_files": uploaded_urls}

@router.put("/events/photos/{photo_id}", tags=["Uploads - Events"])
@admin_required()
async def edit_event_photo(
    photo_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    photo = db.query(EventPhoto).filter(EventPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=200, detail="Photo not found")

    file_url = await replace_file(
        old_file_url=photo.photo_url,
        file=file,
        category="events",
        filename_prefix=f"event_photo_{photo_id}",
        db_model_obj=photo,
        db_field_name="photo_url",
        db=db
    )

    return {"updated_file": file_url}



@router.delete("/events/photos/{photo_id}", tags=["Uploads - Events"])
@admin_required()
async def delete_event_photo(
    photo_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete an event photo."""
    photo = db.query(EventPhoto).filter(EventPhoto.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=200, detail="Photo not found")
    
    db.delete(photo)
    db.commit()
    return {"message": "Photo deleted successfully"}

@router.post("/finances/{finance_id}/document", tags=["Uploads - Finance"])
@admin_required()
async def upload_finance_document(
    finance_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    finance = db.query(Finance).filter(Finance.id == finance_id).first()
    if not finance:
        raise HTTPException(status_code=200, detail="Finance record not found")

    file_url = await file_handler.save_file(file, f"finances/{finance_id}")
    file_url = file_url.replace("\\", "/")  # Pastikan selalu menggunakan '/'
    finance.document_url = file_url
    db.commit()

    return {"file_url": file_url}

@router.put("/finances/{finance_id}/document", tags=["Uploads - Finance"])
@admin_required()
async def edit_finance_document(
    finance_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    finance = db.query(Finance).filter(Finance.id == finance_id).first()
    if not finance:
        raise HTTPException(status_code=200, detail="Finance record not found")

    file_url = await replace_file(
        old_file_url=finance.document_url,
        file=file,
        category=f"finances/{finance_id}",
        filename_prefix=f"finance_doc_{finance_id}",
        db_model_obj=finance,
        db_field_name="document_url",
        db=db
    )

    return {"updated_file": file_url}


@router.delete("/finances/{finance_id}/document", tags=["Uploads - Finance"])
@admin_required()
async def delete_finance_document(
    finance_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a finance document."""
    finance = db.query(Finance).filter(Finance.id == finance_id).first()
    if not finance:
        raise HTTPException(status_code=200, detail="Finance record not found")
    
    finance.document_url = None
    db.commit()
    return {"message": "Document deleted successfully"}

# Add this at the bottom of uploads.py
def get_save_multiple_images():
    return save_multiple_images

@router.post(
    "/users/{user_id}/photo",
    summary="Upload user profile photo",
    tags=["Uploads - User"]
)
@admin_required()
async def upload_user_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    """Upload photo for a user (member) profile."""
    member = db.query(Member).filter(Member.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=200, detail="Member not found")

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    timestamp = int(datetime.now().timestamp() * 1000)
    file_extension = os.path.splitext(file.filename)[1]
    filename = f"profile_{user_id}_{timestamp}{file_extension}"

    file_url = await file_handler.save_file(file, f"users/{user_id}", filename)
    file_url = file_url.replace("\\", "/")

    member.photo_url = file_url
    db.commit()
    return {"photo_url": file_url}


@router.put("/users/{user_id}/photo", tags=["Uploads - User"])
@admin_required()
async def update_user_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_token)
):
    member = db.query(Member).filter(Member.user_id == user_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    file_url = await replace_file(
        old_file_url=member.photo_url,
        file=file,
        category=f"users/{user_id}",
        filename_prefix=f"profile_{user_id}",
        db_model_obj=member,
        db_field_name="photo_url",
        db=db
    )

    return {"updated_photo_url": file_url}


