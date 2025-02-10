from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import News
from schemas import NewsCreate

router = APIRouter(prefix="/news", tags=["News"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
def create_news(news: NewsCreate, db: Session = Depends(get_db)):
    new_news = News(**news.dict())
    db.add(new_news)
    db.commit()
    return new_news

@router.get("/")
def get_news(db: Session = Depends(get_db)):
    return db.query(News).all()
