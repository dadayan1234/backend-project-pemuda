from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Feedback(Base):
    __tablename__ = "feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("members.id"))
    event_id = Column(Integer, ForeignKey("events.id"))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    member = relationship("Member", back_populates="feedback")
    event = relationship("Event", back_populates="feedback")