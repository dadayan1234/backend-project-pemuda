from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.user import User
from ..models.news import News, NewsPhoto
from api.v1.schemas.news import NewsCreate, News as NewsSchema, NewsPhotoResponse

router = APIRouter()

@router.post("/", response_model=NewsSchema)
@admin_required()
async def create_news(
    news: NewsCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # Buat entri berita baru
    db_news = News(
        title=news.title,
        description=news.description,
        date=news.date,
        created_by=current_user.id
    )
    db.add(db_news)
    db.commit()
    db.refresh(db_news)

    # Tambahkan foto-foto jika ada
    if news.photo_urls:
        db_photos = [
            NewsPhoto(news_id=db_news.id, photo_url=url)
            for url in news.photo_urls
        ]
        db.add_all(db_photos)
        db.commit()

    # Muat ulang data agar menyertakan foto-foto dalam respons
    db.refresh(db_news)
    return db_news

@router.get("/", response_model=List[NewsSchema])
async def get_news(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    news_list = (
        db.query(News)
        .order_by(News.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return news_list

@router.get("/{news_id}", response_model=NewsSchema)
async def get_news_item(
    news_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    news_item = db.query(News).filter(News.id == news_id).first()
    
    if not news_item:
        raise HTTPException(status_code=404, detail="News not found")

    return news_item

@router.delete("/{news_id}")
@admin_required()
async def delete_news(
    news_id: int,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    news_item = db.query(News).filter(News.id == news_id).first()
    
    if not news_item:
        raise HTTPException(status_code=404, detail="News not found")
    
    db.delete(news_item)
    db.commit()
    
    return {"status": "success"}
