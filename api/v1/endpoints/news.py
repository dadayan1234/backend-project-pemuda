from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.user import User
from ..models.news import News, NewsPhoto
from ..schemas.news import NewsCreate, NewsResponse, NewsUpdate, NewsPhotoResponse
from .uploads import get_save_multiple_images, file_handler # Import the function getter
from datetime import datetime
from fastapi import BackgroundTasks
from .notification_service import send_notification


router = APIRouter()
save_multiple_images = get_save_multiple_images()  # Get the working function

@router.post("/", response_model=NewsResponse)
@admin_required()
async def create_news(
    news_data: NewsCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db),
    files: Optional[List[UploadFile]] = File(None)
):
    try:
        db_news = News(
            title=news_data.title,
            description=news_data.description,
            date=news_data.date,
            is_published=news_data.is_published,
            created_by=current_user.id
        )
        db.add(db_news)
        db.commit()
        db.refresh(db_news)

        if files:
            await save_multiple_images(db_news.id, files, "news", db)

        # Kirim notifikasi jika langsung dipublish
        if news_data.is_published:
            members = db.query(User).filter(User.role == "Member").all()
            for member in members:
                background_tasks.add_task(
                    send_notification,
                    db=db,
                    user_id=member.id,
                    title=f"Berita Baru: {db_news.title}",
                    content=f"{db_news.description[:100]}...",  # ringkasan
                )

        return db_news

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

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

@router.put("/{news_id}", response_model=NewsResponse)
@admin_required()
async def update_news(
    news_id: int,
    news_data: NewsUpdate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update informasi berita"""
    db_news = db.query(News).filter(News.id == news_id).first()
    if not db_news:
        raise HTTPException(status_code=404, detail="News not found")

    update_data = news_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_news, field, value)

    db.commit()
    db.refresh(db_news)
    return db_news

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