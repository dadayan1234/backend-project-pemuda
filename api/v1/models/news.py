from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))  # Sesuaikan dengan nama tabel User

    # user = relationship("User", back_populates="news")
