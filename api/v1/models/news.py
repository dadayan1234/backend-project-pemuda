from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from core.database import Base
from datetime import datetime

class News(Base):
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    photos_url = relationship("NewsPhoto", back_populates="news", cascade="all, delete-orphan")

class NewsPhoto(Base):
    __tablename__ = "news_photos"

    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(Integer, ForeignKey("news.id"))
    photo_url = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.now)

    news = relationship("News", back_populates="photos_url")