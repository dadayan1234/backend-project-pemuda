from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, func
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    is_admin = Column(Integer, default=0) 

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(String(1000))
    event_date = Column(DateTime)
    location = Column(String(255))

    photos = relationship("EventPhoto", backref="event", cascade="all, delete-orphan")
    attendances = relationship("Attendance", backref="event", cascade="all, delete-orphan")
    minutes = relationship("Minutes", backref="event", cascade="all, delete-orphan")

class EventPhoto(Base):
    __tablename__ = "event_photos"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    photo_path = Column(String(500), nullable=False)

class Finance(Base):
    __tablename__ = "finances"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    description = Column(String(255))
    date = Column(DateTime, server_default=func.now())
    category = Column(String(255))

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    status = Column(String(50))

    user = relationship("User", backref="attendances")

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    date = Column(DateTime)
    description = Column(String(1000))
    status = Column(String(100))

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    description = Column(String(1000))
    date = Column(DateTime, server_default=func.now())

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(255))
    details = Column(String(1000))

class Minutes(Base):
    __tablename__ = "meeting_minutes"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    content = Column(String(2000))
