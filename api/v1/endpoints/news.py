import json
from fastapi import APIRouter, BackgroundTasks, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from api.v1.endpoints.notification_service import send_notification
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.user import User
from ..models.news import News, NewsPhoto
from ..schemas.news import NewsCreate, NewsResponse, NewsUpdate, NewsPhotoResponse
from datetime import datetime
from core.utils.file_handler import FileHandler
from .uploads import save_multiple_images


router = APIRouter()
file_handler = FileHandler()


@router.get("/", response_model=List[NewsResponse])
async def get_all_news(
    skip: int = 0,
    limit: int = 100,
    is_published: Optional[bool] = None,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Dapatkan semua berita dengan filter opsional"""
    query = db.query(News)
    
    if is_published is not None:
        query = query.filter(News.is_published == is_published)
    
    news_list = query.order_by(News.date.desc()) \
        .offset(skip) \
        .limit(limit) \
        .all()

    return news_list

@router.get("/{news_id}", response_model=NewsResponse)
async def get_news_detail(
    news_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Dapatkan detail berita beserta foto-fotonya"""
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    return news

@router.post("/", response_model=NewsResponse)
@admin_required()
async def create_news(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    description: str = Form(...),
    date: datetime = Form(...),
    is_published: bool = Form(True),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        # Buat objek dan simpan
        db_news = News(
            title=title,
            description=description,
            date=date,
            is_published=is_published,
            created_by=current_user.id,
        )
        db.add(db_news)
        db.commit()
        db.refresh(db_news)

        # Upload foto (jika ada)
        if files:
            await save_multiple_images(db_news.id, files, "news", db)

        # Kirim notifikasi jika published
        if is_published:
            members = db.query(User).filter(User.role == "Member").all()
            for member in members:
                background_tasks.add_task(
                    send_notification,
                    db=db,
                    user_id=member.id,
                    title=f"Berita Baru: {db_news.title}",
                    content=f"{db_news.description[:100]}..."
                )

        return db_news

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.put("/{news_id}", response_model=NewsResponse)
@admin_required()
async def update_news(
    news_id: int,
    background_tasks: BackgroundTasks,
    news_data: NewsUpdate,  # Menggunakan pydantic model untuk data JSON
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db),
):
    # Mencari berita berdasarkan ID
    db_news = db.query(News).filter(News.id == news_id).first()
    if not db_news:
        raise HTTPException(status_code=404, detail="News not found")

    try:
        # Menyimpan status sebelumnya dari is_published
        previously_published = db_news.is_published

        # Menyimpan perubahan hanya untuk field yang diberikan dalam request body
        update_dict = news_data.dict(exclude_unset=True)  # Hanya field yang diberikan yang akan diupdate
        for field, value in update_dict.items():
            setattr(db_news, field, value)

        # Memperbarui waktu update
        db_news.updated_at = datetime.now()

        # Commit perubahan ke database
        db.commit()
        db.refresh(db_news)

        # Upload foto (jika ada) - Di sini kita tidak memproses gambar karena ada endpoint terpisah
        if news_data.files:
            await save_multiple_images(db_news.id, news_data.files, "news", db)

        # Mengirim notifikasi jika berubah menjadi published
        if not previously_published and db_news.is_published:
            members = db.query(User).filter(User.role == "Member").all()
            for member in members:
                background_tasks.add_task(
                    send_notification,
                    db=db,
                    user_id=member.id,
                    title=f"Berita Dipublikasikan: {db_news.title}",
                    content=f"{db_news.description[:100]}..."
                )

        return db_news

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{news_id}")
@admin_required()
async def delete_news(
    news_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Hapus berita beserta semua fotonya"""
    db_news = db.query(News).filter(News.id == news_id).first()
    if not db_news:
        raise HTTPException(status_code=404, detail="News not found")

    # Hapus file foto dari storage
    for photo in db_news.photos:
        file_handler.delete_image(photo.photo_url)

    db.delete(db_news)
    db.commit()
    return {"message": "News deleted successfully"}