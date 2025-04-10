from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from core.database import Base  # Sesuaikan dengan import dari konfigurasi database Anda

class MeetingMinutes(Base):
    __tablename__ = "meeting_minutes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    document_url = Column(String(255), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)  # Relasi ke events
    created_at = Column(DateTime, default=func.current_timestamp())
    updated_at = Column(DateTime, default=func.current_timestamp(), onupdate=func.current_timestamp())

    event = relationship("Event", back_populates="meeting_minutes")  # Relasi ke Event