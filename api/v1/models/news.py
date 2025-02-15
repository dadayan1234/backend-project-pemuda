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
    photo_url = Column(String(255))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # user = relationship("User", back_populates="news")
