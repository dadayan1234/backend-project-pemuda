from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), index=True)  # Tambahkan panjang 255
    email = Column(String(255), unique=True, index=True)  # Tambahkan panjang 255
    password_hash = Column(String(255))  # Tambahkan panjang 255

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)  # Tambahkan panjang 255
    description = Column(String(1000))  # Sesuaikan panjang dengan kebutuhan
    event_date = Column(DateTime)
    location = Column(String(255))  # Tambahkan panjang 255

class EventPhoto(Base):
    __tablename__ = "event_photos"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    photo_path = Column(String(500), nullable=False)  # Tambahkan panjang 500 (untuk path yang panjang)

class Finance(Base):
    __tablename__ = "finance"
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    description = Column(String(255))  # Sudah benar
    date = Column(DateTime, default=datetime.utcnow)
    category = Column(String(255))  # Tambahkan panjang 255

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String(50))  # Tambahkan panjang 50

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))  # Tambahkan panjang 255
    date = Column(DateTime)
    description = Column(String(1000))  # Sesuaikan panjang dengan kebutuhan
    status = Column(String(100))  # Tambahkan panjang 100

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))  # Tambahkan panjang 255
    description = Column(String(1000))  # Sesuaikan panjang dengan kebutuhan
    date = Column(DateTime, default=datetime.utcnow)

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(255))  # Tambahkan panjang 255
    details = Column(String(1000))  # Sesuaikan panjang dengan kebutuhan

class Minutes(Base):
    __tablename__ = "minutes"
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"))
    content = Column(String(2000))  # Sesuaikan panjang dengan kebutuhan
