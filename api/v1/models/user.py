from sqlalchemy import Column, Integer, String, Enum, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True)
    password = Column(String(255))
    role = Column(Enum("Admin", "Member"))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    fcm_token = Column(String(512), nullable=True)
    
    member_info = relationship("Member", back_populates="user", uselist=False, cascade="all, delete-orphan")

    # ✅ Tambahkan relasi baru
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")

class Member(Base):
    __tablename__ = "members"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    full_name = Column(String(255), nullable=False)
    birth_place = Column(String(255))  # ✅ Tempat lahir ditambahkan di sini
    birth_date = Column(DateTime, nullable=True)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(255), nullable=True)
    division = Column(String(255), nullable=True)
    address = Column(Text, nullable=True)
    position = Column(String(255), nullable=True)
    photo_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    
    user = relationship("User", back_populates="member_info")
    attendances = relationship("Attendance", back_populates="member", cascade="all, delete-orphan")
    feedback = relationship("Feedback", back_populates="member", cascade="all, delete-orphan")
