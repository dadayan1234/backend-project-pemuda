from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db, admin_required
from core.security import verify_token
from ..models.user import User
from ..models.news import News
from api.v1.schemas.news import NewsCreate, News as NewsSchema

router = APIRouter()

@router.post("/", response_model=NewsSchema)
@admin_required()
async def create_news(
    news: NewsCreate,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    db_news = News(**news.dict(), created_by=current_user.id)
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news

@router.get("/", response_model=List[NewsSchema])
async def get_news(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(verify_token),
    db: Session = Depends(get_db)
):
    return (
        db.query(News)
        .order_by(News.date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

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