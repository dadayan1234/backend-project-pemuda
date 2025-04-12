from sqlalchemy import Column, Integer, String, DateTime, Time, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)         # 🔍 sering dicari => index
    description = Column(Text, nullable=False)
    date = Column(DateTime, nullable=False, index=True)             # 🔍 search/filter by date
    time = Column(Time, nullable=False)
    location = Column(String(255), nullable=False, index=True)      # 🔍 filter by location
    created_by = Column(Integer, ForeignKey("users.id"), index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    status = Column(Enum("akan datang", "selesai"), nullable=False, index=True)  # 🔍 filter berdasarkan status

    photos = relationship("EventPhoto", back_populates="event", cascade="all, delete-orphan")
    attendances = relationship("Attendance", back_populates="event", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="event", cascade="all, delete-orphan")
    meeting_minutes = relationship("MeetingMinutes", back_populates="event", cascade="all, delete-orphan")


class EventPhoto(Base):
    __tablename__ = "event_photos"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    photo_url = Column(String(255), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="photos")

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    member_id = Column(Integer, ForeignKey("members.id"))
    status = Column(Enum("Hadir", "Izin", "Alfa"), nullable=False)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    event = relationship("Event", back_populates="attendances")
    member = relationship("Member", back_populates="attendances")
    
